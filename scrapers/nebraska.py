"""Nebraska state scraper (Nebraska Game & Parks Commission).

Source: NGPC "Public Fishing Spots" (JoinedData_Lakes) ArcGIS FeatureServer.
Precomputed WGS84 centroid fields, county, species and acreage.

Layer: https://services5.arcgis.com/IOshH1zLrIieqrNk/arcgis/rest/services/JoinedData_Lakes/FeatureServer/0
"""

from .base import make_record, fetch_arcgis

STATE_NAME = "Nebraska"
STATE_CODE = "ne"

_LAYER = "https://services5.arcgis.com/IOshH1zLrIieqrNk/arcgis/rest/services/JoinedData_Lakes/FeatureServer/0"
_URL = "https://outdoornebraska.gov/things-to-do/fishing/"


def scrape(limit=None):
    print("[NE] Fetching NGPC public fishing spots...")
    features = fetch_arcgis(
        _LAYER, out_fields="Name,County,Acres_Text,Species,Centroid_X,Centroid_Y",
        limit=limit, page_size=2000,
    )
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Name") or "").strip()
        lat, lon = p.get("Centroid_Y"), p.get("Centroid_X")
        if not name or lat is None or lon is None:
            continue
        species = [s.strip() for s in (p.get("Species") or "").split(",") if s.strip()]
        acres = p.get("Acres_Text")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("County") or "").title() or None,
            area=f"{acres} Acres" if acres else "Unknown",
            species=species, url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[NE] Collected {len(records)} waters.")
    return records
