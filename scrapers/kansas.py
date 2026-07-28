"""Kansas state scraper (Kansas Dept of Wildlife & Parks).

Source: KDWP Fishing Atlas ArcGIS FeatureServer (points) -- reservoirs, state
fishing lakes and community lakes. Name + acreage; no species/county/elevation.

Layer: https://services1.arcgis.com/q2CglofYX6ACNEeu/arcgis/rest/services/Res_SFL_CFAP_NoFee_Current2022/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Kansas"
STATE_CODE = "ks"

_LAYER = "https://services1.arcgis.com/q2CglofYX6ACNEeu/arcgis/rest/services/Res_SFL_CFAP_NoFee_Current2022/FeatureServer/0"
_URL = "https://ksoutdoors.com/Fishing"


def scrape(limit=None):
    print("[KS] Fetching KDWP fishing atlas waters...")
    features = fetch_arcgis(_LAYER, out_fields="ImpndmtNam,ACRES,CLASS",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("ImpndmtNam") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("ACRES")
        try:
            area = f"{float(acres)} Acres" if acres else "Unknown"
        except (TypeError, ValueError):
            area = "Unknown"
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=area, url=_URL, description=(p.get("CLASS") or "").strip(),
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[KS] Collected {len(records)} waters.")
    return records
