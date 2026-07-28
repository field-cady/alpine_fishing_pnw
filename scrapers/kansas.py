"""Kansas state scraper (Kansas Dept of Wildlife & Parks).

Base: KDWP Fishing Atlas points (name, acreage, coords). Species: the KDWP
Fishing Forecast table (one row per water per species), joined by impoundment
name.

Base:     https://services1.arcgis.com/q2CglofYX6ACNEeu/arcgis/rest/services/Res_SFL_CFAP_NoFee_Current2022/FeatureServer/0
Forecast: https://services1.arcgis.com/q2CglofYX6ACNEeu/arcgis/rest/services/Fishing_Forecast_Publish_WFL1/FeatureServer/27
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Kansas"
STATE_CODE = "ks"

_LAYER = "https://services1.arcgis.com/q2CglofYX6ACNEeu/arcgis/rest/services/Res_SFL_CFAP_NoFee_Current2022/FeatureServer/0"
_FORECAST = "https://services1.arcgis.com/q2CglofYX6ACNEeu/arcgis/rest/services/Fishing_Forecast_Publish_WFL1/FeatureServer/27"
_URL = "https://ksoutdoors.com/Fishing"


def _species_by_name(limit=None):
    by = {}
    for feat in fetch_arcgis(_FORECAST, out_fields="Impoundment,Species", limit=limit, page_size=2000):
        p = feat.get("properties", {})
        name = (p.get("Impoundment") or "").strip().lower()
        sp = (p.get("Species") or "").strip()
        if name and sp:
            by.setdefault(name, set()).add(sp)
    return by


def scrape(limit=None):
    print("[KS] Fetching KDWP fishing forecast species...")
    species_by_name = _species_by_name(limit=limit)
    print(f"[KS] species for {len(species_by_name)} waters. Fetching atlas...")
    features = fetch_arcgis(_LAYER, out_fields="ImpndmtNam,ACRES,CLASS", limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("ImpndmtNam") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("ACRES")
        try:
            area = f"{float(acres)} Acres" if acres else "Unknown"
        except (TypeError, ValueError):
            area = "Unknown"
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon, area=area,
            species=sorted(species_by_name.get(name.lower(), set())), url=_URL,
            description=(p.get("CLASS") or "").strip(),
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[KS] Collected {len(records)} waters ({withsp} with species).")
    return records
