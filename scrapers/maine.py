"""Maine state scraper (Maine Office of GIS / MDIFW).

Source: Maine GIS "PublicMasterWaters" ArcGIS FeatureServer. We keep lentic
waters (lakes/ponds) with their native lat/long attribute fields and acreage.
Species live in MDIFW lake surveys keyed by waterbody id and are not fetched.

Layer: https://gis.maine.gov/arcgis/rest/services/Hosted/PublicMasterWaters/FeatureServer/1
"""

from .base import make_record, fetch_arcgis

STATE_NAME = "Maine"
STATE_CODE = "me"

_LAYER = "https://gis.maine.gov/arcgis/rest/services/Hosted/PublicMasterWaters/FeatureServer/1"
_URL = "https://www.maine.gov/ifw/fishing-boating/fishing/"


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def scrape(limit=None):
    print("[ME] Fetching Maine lentic waters...")
    features = fetch_arcgis(
        _LAYER, where="wtype='Lentic'",
        out_fields="name,lat,long,acres", limit=limit, page_size=2000,
    )
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("name") or "").strip()
        lat, lon = _to_float(p.get("lat")), _to_float(p.get("long"))
        if not name or lat is None or lon is None:
            continue
        acres = p.get("acres")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=f"{acres} Acres" if acres else "Unknown", url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[ME] Collected {len(records)} waters.")
    return records
