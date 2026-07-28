"""Alabama state scraper (ADCNR).

Source: Alabama DCNR "Public Fishing Lakes" ArcGIS MapServer (points). Only the
20 state Public Fishing Lakes; no species/county/area fields.

Layer: https://conservationgis.alabama.gov/adcnrweb/rest/services/PublicFishingLakes/MapServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Alabama"
STATE_CODE = "al"

_LAYER = "https://conservationgis.alabama.gov/adcnrweb/rest/services/PublicFishingLakes/MapServer/0"
_URL = "https://www.outdooralabama.com/fishing/public-fishing-lakes"


def scrape(limit=None):
    print("[AL] Fetching ADCNR public fishing lakes...")
    features = fetch_arcgis(_LAYER, out_fields="*", limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Name") or p.get("NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        records.append(make_record(name=name, state=STATE_NAME, lat=lat, lon=lon, url=_URL))
    records.sort(key=lambda r: r["name"])
    print(f"[AL] Collected {len(records)} lakes.")
    return records
