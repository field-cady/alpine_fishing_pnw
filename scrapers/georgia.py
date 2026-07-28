"""Georgia state scraper (Georgia DNR Wildlife Resources).

Base: GADNR "WRD_Waterbodies" (GNIS_Name, area, X/Y, WATER_CODE).
Species: the "Reservoir_Prospects" table (one row per species per reservoir),
joined by ``WATER_CODE``. Non-species rows ("Best Bets", etc.) are filtered.

Waterbodies: https://services6.arcgis.com/9QlSLDqa0P1cHLhu/arcgis/rest/services/WRD_Waterbodies/FeatureServer/0
Prospects:   https://services6.arcgis.com/9QlSLDqa0P1cHLhu/arcgis/rest/services/Reservoir_Prospects/FeatureServer/1
"""

from .base import make_record, fetch_arcgis

STATE_NAME = "Georgia"
STATE_CODE = "ga"

_LAYER = "https://services6.arcgis.com/9QlSLDqa0P1cHLhu/arcgis/rest/services/WRD_Waterbodies/FeatureServer/0"
_PROSPECTS = "https://services6.arcgis.com/9QlSLDqa0P1cHLhu/arcgis/rest/services/Reservoir_Prospects/FeatureServer/1"
_URL = "https://georgiawildlife.com/fishing"
_ACRES_PER_SQKM = 247.105
_NON_SPECIES = {"best bets", "best betts", "additional information", "other species", "other"}


def _species_by_code(limit=None):
    by = {}
    for feat in fetch_arcgis(_PROSPECTS, out_fields="WATER_CODE,SpeciesName", limit=limit, page_size=2000):
        p = feat.get("properties", {})
        code = (p.get("WATER_CODE") or "").strip()
        name = (p.get("SpeciesName") or "").strip()
        if code and name and name.lower() not in _NON_SPECIES:
            by.setdefault(code, set()).add(name)
    return by


def scrape(limit=None):
    print("[GA] Fetching GADNR reservoir species prospects...")
    species_by_code = _species_by_code(limit=limit)
    print(f"[GA] species for {len(species_by_code)} reservoirs. Fetching waterbodies...")
    features = fetch_arcgis(_LAYER, out_fields="GNIS_Name,X,Y,AreaSqKm,d_FType,WATER_CODE",
                            limit=limit, page_size=2000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("GNIS_Name") or "").strip()
        lat, lon = p.get("Y"), p.get("X")
        if not name or lat is None or lon is None:
            continue
        sqkm = p.get("AreaSqKm")
        records.append(make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon,
            area=f"{round(sqkm * _ACRES_PER_SQKM, 1)} Acres" if sqkm else "Unknown",
            species=sorted(species_by_code.get((p.get("WATER_CODE") or "").strip(), set())),
            url=_URL, description=(p.get("d_FType") or "").strip(),
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[GA] Collected {len(records)} waterbodies ({withsp} with species).")
    return records
