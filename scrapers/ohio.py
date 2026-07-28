"""Ohio state scraper (Ohio DNR Division of Wildlife).

Base: ODNR DOW "Lakes" (LAKE_NAME, ACRES, polygon centroid).
Species: the DOW "LakeFishing" per-species layers (3-10), each carrying a
SPECIES value and LAKE_NAME; unioned per lake by (case-insensitive) name.
Only the ~35 lakes ODNR profiles for fishing get species.

Lakes:   https://gis2.ohiodnr.gov/arcgis/rest/services/DOW_Services/DOW_Lakes_Bathymetry/MapServer/1
Fishing: https://gis2.ohiodnr.gov/arcgis/rest/services/DOW_Services/DOW_LakeFishing/MapServer/{3..10}
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Ohio"
STATE_CODE = "oh"

_LAYER = "https://gis2.ohiodnr.gov/arcgis/rest/services/DOW_Services/DOW_Lakes_Bathymetry/MapServer/1"
_FISHING = "https://gis2.ohiodnr.gov/arcgis/rest/services/DOW_Services/DOW_LakeFishing/MapServer/{}"
_SPECIES_LAYERS = range(3, 11)
_URL = "https://ohiodnr.gov/go-and-do/plan-a-visit/find-a-property/fishing"


def _species_by_lake(limit=None):
    by = {}
    for layer in _SPECIES_LAYERS:
        for feat in fetch_arcgis(_FISHING.format(layer), out_fields="LAKE_NAME,SPECIES",
                                 limit=limit, page_size=2000):
            p = feat.get("properties", {})
            name = (p.get("LAKE_NAME") or "").strip().lower()
            sp = (p.get("SPECIES") or "").strip()
            if name and sp:
                by.setdefault(name, set()).add(sp)
    return by


def scrape(limit=None):
    print("[OH] Fetching ODNR per-species fishing layers...")
    species_by_lake = _species_by_lake(limit=limit)
    print(f"[OH] species for {len(species_by_lake)} lakes. Fetching lakes...")
    features = fetch_arcgis(_LAYER, out_fields="LAKE_NAME,ACRES", limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("LAKE_NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("ACRES")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=f"{round(acres, 1)} Acres" if acres else "Unknown",
            species=sorted(species_by_lake.get(name.lower(), set())), url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[OH] Collected {len(records)} lakes ({withsp} with species).")
    return records
