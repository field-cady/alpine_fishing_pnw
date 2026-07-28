"""Ohio state scraper (Ohio DNR Division of Wildlife).

Source: ODNR DOW "Lakes" ArcGIS MapServer (polygons). Names + acreage for 321
major public fishing lakes; centroid computed from geometry. No species/
county/elevation in this layer.

Layer: https://gis2.ohiodnr.gov/arcgis/rest/services/DOW_Services/DOW_Lakes_Bathymetry/MapServer/1
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Ohio"
STATE_CODE = "oh"

_LAYER = "https://gis2.ohiodnr.gov/arcgis/rest/services/DOW_Services/DOW_Lakes_Bathymetry/MapServer/1"
_URL = "https://ohiodnr.gov/go-and-do/plan-a-visit/find-a-property/fishing"


def scrape(limit=None):
    print("[OH] Fetching ODNR lakes...")
    features = fetch_arcgis(_LAYER, out_fields="LAKE_NAME,ACRES",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("LAKE_NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("ACRES")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=f"{round(acres, 1)} Acres" if acres else "Unknown", url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[OH] Collected {len(records)} lakes.")
    return records
