"""Iowa state scraper (Iowa DNR).

Source: Iowa DNR "fishingreports" ArcGIS MapServer (points) -- fishing-report
waterbodies. Name + coordinates only; no species/county/area/elevation in the
layer (species live on per-code fishing-report pages).

Layer: https://programs.iowadnr.gov/geospatial/rest/services/fisheries/fishingreports/MapServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Iowa"
STATE_CODE = "ia"

_LAYER = "https://programs.iowadnr.gov/geospatial/rest/services/fisheries/fishingreports/MapServer/0"
_URL = "https://www.iowadnr.gov/things-to-do/fishing"


def scrape(limit=None):
    print("[IA] Fetching Iowa DNR fishing waterbodies...")
    features = fetch_arcgis(_LAYER, out_fields="WATERBODYNAME,hydrographyName,code",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WATERBODYNAME") or p.get("hydrographyName") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        records.append(make_record(name=name.title(), state=STATE_NAME,
                                    lat=lat, lon=lon, url=_URL))
    records.sort(key=lambda r: r["name"])
    print(f"[IA] Collected {len(records)} waters.")
    return records
