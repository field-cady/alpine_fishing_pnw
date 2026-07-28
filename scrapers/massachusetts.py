"""Massachusetts state scraper (MassGIS / MassWildlife).

Base: MassGIS "Massachusetts Water Features" named lakes/ponds (NAME, PALIS_ID,
acreage, centroid). Species: MassWildlife exposes no structured multi-species
table (full species live only in per-pond PDF maps), but its Trout Stocking
Waterbodies layer flags trout-stocked waters -- joined by PALIS id. So MA gets
a Trout tag where stocked; broader species are not machine-queryable.

Base:  https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Water_Features/FeatureServer/5
Trout: https://services1.arcgis.com/7iJyYTjCtKsZS1LR/arcgis/rest/services/Trout_Stocking_Waterbodies_ALL/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Massachusetts"
STATE_CODE = "ma"

_LAYER = "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Water_Features/FeatureServer/5"
_TROUT = "https://services1.arcgis.com/7iJyYTjCtKsZS1LR/arcgis/rest/services/Trout_Stocking_Waterbodies_ALL/FeatureServer/0"
_URL = "https://www.mass.gov/freshwater-fishing"
_SQM_PER_ACRE = 4046.8564


def _trout_palis(limit=None):
    palis = set()
    for feat in fetch_arcgis(_TROUT, out_fields="saris_pal", limit=limit, page_size=2000):
        v = feat.get("properties", {}).get("saris_pal")
        if v:
            palis.add(str(v).strip().zfill(5))
    return palis


def scrape(limit=None):
    print("[MA] Fetching MassWildlife trout-stocked waters...")
    trout_palis = _trout_palis(limit=limit)
    print(f"[MA] {len(trout_palis)} trout-stocked PALIS ids. Fetching lakes...")
    features = fetch_arcgis(_LAYER, where="NAME IS NOT NULL AND NAME<>''",
                            out_fields="NAME,PALIS_ID,Shape__Area", limit=limit, page_size=2000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        area_sqm = next((v for k, v in p.items() if "AREA" in k.upper() and v), None)
        area = f"{round(area_sqm / _SQM_PER_ACRE, 1)} Acres" if area_sqm else "Unknown"
        palis = str(p.get("PALIS_ID") or "").strip().zfill(5)
        species = ["Trout"] if palis in trout_palis else []
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=area, species=species, url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[MA] Collected {len(records)} waters ({withsp} trout-stocked).")
    return records
