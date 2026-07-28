"""Illinois state scraper (Illinois DNR).

Source: IDNR "LakeDepthAndCapacity" ArcGIS MapServer (polygons). Only the
bathymetry-surveyed lakes (44) are reliably queryable -- the full public-waters
layer times out. Gives name, acreage and normal-pool elevation; no species or
county anywhere in IL DNR GIS.

Layer: https://maps.dnr.illinois.gov/geoservices/rest/services/WaterResources/LakeDepthAndCapacity/MapServer/2
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Illinois"
STATE_CODE = "il"

_LAYER = "https://maps.dnr.illinois.gov/geoservices/rest/services/WaterResources/LakeDepthAndCapacity/MapServer/2"
_URL = "https://ifishillinois.org/"


def scrape(limit=None):
    print("[IL] Fetching IDNR surveyed lakes...")
    features = fetch_arcgis(_LAYER, out_fields="name,area_ac,norm_pool",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("name") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("area_ac")
        elev = p.get("norm_pool")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            elevation=float(elev) if elev else None,
            area=f"{acres} Acres" if acres else "Unknown", url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[IL] Collected {len(records)} lakes.")
    return records
