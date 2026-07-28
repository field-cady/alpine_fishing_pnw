"""Arkansas state scraper (Arkansas Game & Fish Commission).

Source: AGFC "WaterBodyList" ArcGIS FeatureServer (polygons). Filtered to
lake-like waters; centroid used for coordinates and gis_acres for area. County
is a numeric code (omitted); no species/elevation.

Layer: https://gisec2.agfc.com/arcgis/rest/services/Fisheries/WaterBodyList_Service/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Arkansas"
STATE_CODE = "ar"

_LAYER = "https://gisec2.agfc.com/arcgis/rest/services/Fisheries/WaterBodyList_Service/FeatureServer/0"
_URL = "https://www.agfc.com/fishing/"


def scrape(limit=None):
    print("[AR] Fetching AGFC waterbodies (lakes)...")
    features = fetch_arcgis(
        _LAYER,
        where="ftype IN ('Lake','Storage Reservoir','Fishing Pond')",
        out_fields="fname,gis_acres,acres,ftype",
        limit=limit, page_size=1000,
    )
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("fname") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("gis_acres") or p.get("acres")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=f"{round(float(acres), 1)} Acres" if acres else "Unknown",
            url=_URL, description=(p.get("ftype") or "").strip(),
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[AR] Collected {len(records)} waters.")
    return records
