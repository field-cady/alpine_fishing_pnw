"""New Hampshire state scraper (NH GRANIT / NH Fish & Game).

Source: NH GRANIT "IWR Water Resources" ArcGIS FeatureServer, layer 9 (NHD
Waterbody). We keep named lakes/ponds/reservoirs (ftype 390/436) with area and
(sparse) elevation; centroid used for coordinates. No species/county.

Layer: https://nhgeodata.unh.edu/hosting/rest/services/Hosted/IWR_WaterResources/FeatureServer/9
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "New Hampshire"
STATE_CODE = "nh"

_LAYER = "https://nhgeodata.unh.edu/hosting/rest/services/Hosted/IWR_WaterResources/FeatureServer/9"
_URL = "https://www.wildlife.nh.gov/fishing-new-hampshire"
_ACRES_PER_SQKM = 247.105
_FEET_PER_METER = 3.28084


def scrape(limit=None):
    print("[NH] Fetching NH GRANIT waterbodies...")
    features = fetch_arcgis(
        _LAYER,
        where="gnis_name IS NOT NULL AND ftype IN (390,436)",
        out_fields="gnis_name,areasqkm,elevation", limit=limit, page_size=1000,
    )
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("gnis_name") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        sqkm = p.get("areasqkm")
        elev_m = p.get("elevation")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            elevation=round(elev_m * _FEET_PER_METER, 1) if elev_m else None,
            area=f"{round(sqkm * _ACRES_PER_SQKM, 1)} Acres" if sqkm else "Unknown",
            url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[NH] Collected {len(records)} waters.")
    return records
