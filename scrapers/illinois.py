"""Illinois state scraper (Illinois DNR).

Base: IDNR "Lake Depth & Capacity" bathymetry lakes (name, area, elevation,
centroid). Species: iFishIllinois stocking API (species stocked per waterbody),
joined by name. (IDNR's full public-waters GIS layer times out; the bathymetry
set is the reliable base.)

Base:     https://maps.dnr.illinois.gov/geoservices/rest/services/WaterResources/LakeDepthAndCapacity/MapServer/2
Stocking: https://ifishillinois.org/FishStockings/LoadStockings
"""

import requests

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Illinois"
STATE_CODE = "il"

_LAYER = "https://maps.dnr.illinois.gov/geoservices/rest/services/WaterResources/LakeDepthAndCapacity/MapServer/2"
_STOCK = "https://ifishillinois.org/FishStockings/LoadStockings"
_URL = "https://ifishillinois.org/"


def _species_by_name():
    try:
        r = requests.post(_STOCK, timeout=90,
                          headers={"X-Requested-With": "XMLHttpRequest"},
                          data={"sort": "", "page": 1, "pageSize": 100000,
                                "group": "", "filter": ""})
        rows = r.json().get("Data") or r.json().get("data") or []
    except Exception as e:
        print(f"[IL] stocking API failed: {e}")
        return {}
    by = {}
    for row in rows:
        wb = (row.get("Waterbody") or "").strip().lower()
        sp = (row.get("Species") or "").strip()
        if wb and sp:
            by.setdefault(wb, set()).add(sp)
    return by


def scrape(limit=None):
    print("[IL] Fetching iFishIllinois stocking species...")
    species_by_name = _species_by_name()
    print(f"[IL] species for {len(species_by_name)} waters. Fetching lakes...")
    features = fetch_arcgis(_LAYER, out_fields="name,area_ac,norm_pool", limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("name") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres, elev = p.get("area_ac"), p.get("norm_pool")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            elevation=float(elev) if elev else None,
            area=f"{acres} Acres" if acres else "Unknown",
            species=sorted(species_by_name.get(name.lower(), set())), url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[IL] Collected {len(records)} lakes ({withsp} with species).")
    return records
