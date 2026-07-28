"""Texas state scraper (Texas Water Development Board).

Source: TWDB "Texas Reservoirs" ArcGIS FeatureServer (polygons). Gives
authoritative reservoir names and geometry; no species/county/elevation are
available in any queryable TPWD/TWDB GIS layer (TPWD stocking is HTML only).

Layer: https://services3.arcgis.com/O0h7Kr4STkhD6uiU/arcgis/rest/services/Texas_Reservoirs/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Texas"
STATE_CODE = "tx"

_LAYER = "https://services3.arcgis.com/O0h7Kr4STkhD6uiU/arcgis/rest/services/Texas_Reservoirs/FeatureServer/0"
_URL = "https://tpwd.texas.gov/fishboat/fish/"


def scrape(limit=None):
    print("[TX] Fetching TWDB Texas reservoirs...")
    features = fetch_arcgis(_LAYER, out_fields="RES_NAME,TYPE,STATUS",
                            limit=limit, page_size=1000)
    print(f"[TX] {len(features)} reservoir polygons.")

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("RES_NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon, url=_URL,
            description=(p.get("TYPE") or "").strip(),
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[TX] Collected {len(records)} reservoirs.")
    return records
