"""Florida state scraper (Florida FWC).

Source: FWC "LAKES_POINTS" ArcGIS FeatureServer -- named freshwater lakes as
label points with county. No species/area/elevation in this layer.

Layer: https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/LAKES_POINTS/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Florida"
STATE_CODE = "fl"

_LAYER = "https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/LAKES_POINTS/FeatureServer/0"
_URL = "https://myfwc.com/fishing/freshwater/"


def scrape(limit=None):
    print("[FL] Fetching FWC named lakes...")
    features = fetch_arcgis(_LAYER, out_fields="NAME,COUNTY", limit=limit, page_size=2000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("COUNTY") or "").title() or None, url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[FL] Collected {len(records)} lakes.")
    return records
