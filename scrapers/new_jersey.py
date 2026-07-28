"""New Jersey state scraper (NJ DEP Fish & Wildlife).

Source: NJDEP "Trout Stocked Lakes Centroids" ArcGIS MapServer (points) via
NJGIN. Trout-stocked lakes with native decimal-degree coordinates and acreage;
species recorded as Trout. No county/elevation.

Layer: https://mapsdep.nj.gov/arcgis/rest/services/Features/Environmental_admin/MapServer/33
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "New Jersey"
STATE_CODE = "nj"

_LAYER = "https://mapsdep.nj.gov/arcgis/rest/services/Features/Environmental_admin/MapServer/33"
_URL = "https://dep.nj.gov/njfw/fishing/freshwater/"


def scrape(limit=None):
    print("[NJ] Fetching NJDEP trout-stocked lakes...")
    features = fetch_arcgis(_LAYER, out_fields="WATERBODY,GNIS_NAME,LATDD,LONDD,ACRES",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WATERBODY") or p.get("GNIS_NAME") or "").strip()
        if not name:
            continue
        lat, lon = p.get("LATDD"), p.get("LONDD")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("ACRES")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=f"{acres} Acres" if acres else "Unknown",
            species=["Trout"], url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[NJ] Collected {len(records)} stocked lakes.")
    return records
