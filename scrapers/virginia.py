"""Virginia state scraper (Virginia DWR).

Source: Virginia DWR "Public Fishing Lakes" ArcGIS FeatureServer (polygons)
with precomputed WGS84 centroid fields (XCenter/YCenter). 193 DWR-managed
lakes; no species/county/elevation in the layer.

Layer: https://services.dwr.virginia.gov/arcgis/rest/services/HUB_Layers/DWR_Public_Fishing_Lakes/FeatureServer/0
"""

from .base import make_record, fetch_arcgis

STATE_NAME = "Virginia"
STATE_CODE = "va"

_LAYER = "https://services.dwr.virginia.gov/arcgis/rest/services/HUB_Layers/DWR_Public_Fishing_Lakes/FeatureServer/0"
_URL = "https://dwr.virginia.gov/fishing/"


def scrape(limit=None):
    print("[VA] Fetching Virginia DWR public fishing lakes...")
    features = fetch_arcgis(_LAYER, out_fields="NAME,XCenter,YCenter,Boat_Motor,URL",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("NAME") or "").strip()
        lat, lon = p.get("YCenter"), p.get("XCenter")
        if not name or lat is None or lon is None:
            continue
        records.append(make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon,
            url=p.get("URL") or _URL,
            description=(p.get("Boat_Motor") or "").strip(),
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[VA] Collected {len(records)} lakes.")
    return records
