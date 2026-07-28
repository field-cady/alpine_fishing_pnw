"""Missouri state scraper (Missouri Dept of Conservation).

Source: MDC "MO Fishing Interactive Map" ArcGIS MapServer, layer 11 (Water Body
Points). Point features with name and acreage; no species/county/elevation.

Layer: https://gisblue.mdc.mo.gov/arcgis/rest/services/Aquatic/MO_Fishing_Interactive_Map/MapServer/11
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Missouri"
STATE_CODE = "mo"

_LAYER = "https://gisblue.mdc.mo.gov/arcgis/rest/services/Aquatic/MO_Fishing_Interactive_Map/MapServer/11"
_URL = "https://mdc.mo.gov/fishing"


def scrape(limit=None):
    print("[MO] Fetching MDC water body points...")
    features = fetch_arcgis(_LAYER, out_fields="Wt_Body_Name,Area_Name,GIS_Acres",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Wt_Body_Name") or p.get("Area_Name") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("GIS_Acres")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=f"{round(acres, 1)} Acres" if acres else "Unknown", url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[MO] Collected {len(records)} waters.")
    return records
