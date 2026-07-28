"""Massachusetts state scraper (MassGIS).

Source: MassGIS "Massachusetts Water Features" ArcGIS FeatureServer, layer 5
(USGS 100k lakes and ponds, polygons). Named waterbodies with area; centroid
used for coordinates. No species/county/elevation in this layer.

Layer: https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Water_Features/FeatureServer/5
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Massachusetts"
STATE_CODE = "ma"

_LAYER = "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Water_Features/FeatureServer/5"
_URL = "https://www.mass.gov/freshwater-fishing"
_SQM_PER_ACRE = 4046.8564


def scrape(limit=None):
    print("[MA] Fetching MassGIS lakes and ponds...")
    features = fetch_arcgis(_LAYER, where="NAME IS NOT NULL AND NAME<>''",
                            out_fields="NAME,Shape__Area", limit=limit, page_size=2000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        area_sqm = next((v for k, v in p.items() if "AREA" in k.upper() and v), None)
        area = f"{round(area_sqm / _SQM_PER_ACRE, 1)} Acres" if area_sqm else "Unknown"
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=area, url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[MA] Collected {len(records)} waters.")
    return records
