"""Tennessee state scraper (TWRA).

Source: TWRA "Boating & Fishing Access Sites" ArcGIS MapServer (points) on
tnmap.tn.gov. Access sites are deduped to one record per water body; county
present, no species/elevation/area.

Layer: https://tnmap.tn.gov/arcgis/rest/services/ENVIRONMENTAL/TWRA/MapServer/1
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Tennessee"
STATE_CODE = "tn"

_LAYER = "https://tnmap.tn.gov/arcgis/rest/services/ENVIRONMENTAL/TWRA/MapServer/1"
_URL = "https://www.tn.gov/twra/fishing.html"


def scrape(limit=None):
    print("[TN] Fetching TWRA access sites...")
    features = fetch_arcgis(_LAYER, out_fields="Body_of_Wa,Latitude,Longitude,County",
                            limit=limit, page_size=1000)
    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Body_of_Wa") or "").strip()
        if not name or name in waters:
            continue
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        waters[name] = make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("County") or "").title() or None, url=_URL,
        )
    records = sorted(waters.values(), key=lambda r: r["name"])
    print(f"[TN] Collected {len(records)} waters.")
    return records
