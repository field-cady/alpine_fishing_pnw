"""Connecticut state scraper (CT DEEP).

Source: CT DEEP "Connecticut Stocked Lakes" ArcGIS FeatureServer (polygons).
Every waterbody is trout-stocked, so species is recorded as Trout. County
present; centroid used for coordinates.

Layer: https://services1.arcgis.com/FjPcSmEFuDYlIdKC/ArcGIS/rest/services/Connecticut_Stocked_Lakes/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Connecticut"
STATE_CODE = "ct"

_LAYER = "https://services1.arcgis.com/FjPcSmEFuDYlIdKC/ArcGIS/rest/services/Connecticut_Stocked_Lakes/FeatureServer/0"
_URL = "https://portal.ct.gov/DEEP/Fishing/Freshwater/Freshwater-Fishing"


def scrape(limit=None):
    print("[CT] Fetching CT DEEP stocked lakes...")
    features = fetch_arcgis(
        _LAYER, out_fields="LAKES_WATERBODY,STOCKING_TABLE_COUNTY,STOCKING_TABLE_MGT",
        limit=limit, page_size=1000,
    )
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("LAKES_WATERBODY") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("STOCKING_TABLE_COUNTY") or "").title() or None,
            species=["Trout"], url=_URL,
            description=(p.get("STOCKING_TABLE_MGT") or "").strip(),
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[CT] Collected {len(records)} stocked lakes.")
    return records
