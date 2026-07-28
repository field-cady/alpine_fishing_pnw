"""Georgia state scraper (Georgia DNR Wildlife Resources).

Source: GADNR "WRD_Waterbodies" ArcGIS FeatureServer (polygons) with native
X/Y centroid fields. Names + area only; no species/county/elevation.

Layer: https://services6.arcgis.com/9QlSLDqa0P1cHLhu/arcgis/rest/services/WRD_Waterbodies/FeatureServer/0
"""

from .base import make_record, fetch_arcgis

STATE_NAME = "Georgia"
STATE_CODE = "ga"

_LAYER = "https://services6.arcgis.com/9QlSLDqa0P1cHLhu/arcgis/rest/services/WRD_Waterbodies/FeatureServer/0"
_URL = "https://georgiawildlife.com/fishing"
_ACRES_PER_SQKM = 247.105


def scrape(limit=None):
    print("[GA] Fetching GADNR waterbodies...")
    features = fetch_arcgis(_LAYER, out_fields="GNIS_Name,X,Y,AreaSqKm,d_FType",
                            limit=limit, page_size=2000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("GNIS_Name") or "").strip()
        lat, lon = p.get("Y"), p.get("X")
        if not name or lat is None or lon is None:
            continue
        sqkm = p.get("AreaSqKm")
        records.append(make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon,
            area=f"{round(sqkm * _ACRES_PER_SQKM, 1)} Acres" if sqkm else "Unknown",
            url=_URL, description=(p.get("d_FType") or "").strip(),
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[GA] Collected {len(records)} waterbodies.")
    return records
