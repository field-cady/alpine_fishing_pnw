"""Maryland state scraper (Maryland DNR / iMAP).

Base: MD iMAP "Lakes - Detailed" (LAKENAME, COUNTY, ACRES, centroid).
Species: MD DNR "Public Angler Access Sites" layer carries a free-text
``FishTypes`` list per access site; we aggregate it per waterbody name and
join to the lakes (normalization handles the messy casing/typos).

Base:  https://mdgeodata.md.gov/imap/rest/services/Hydrology/MD_Waterbodies/FeatureServer/3
Sites: https://services.arcgis.com/njFNhDsUCentVYJW/arcgis/rest/services/Public_View_Angler_Access_Sites_/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Maryland"
STATE_CODE = "md"

_LAYER = "https://mdgeodata.md.gov/imap/rest/services/Hydrology/MD_Waterbodies/FeatureServer/3"
_SITES = "https://services.arcgis.com/njFNhDsUCentVYJW/arcgis/rest/services/Public_View_Angler_Access_Sites_/FeatureServer/0"
_URL = "https://dnr.maryland.gov/fisheries/pages/index.aspx"


def _species_by_water(limit=None):
    by = {}
    for feat in fetch_arcgis(_SITES, out_fields="Waterbody_1,FishTypes_1", limit=limit, page_size=2000):
        p = feat.get("properties", {})
        wb = (p.get("Waterbody_1") or "").strip().lower()
        fish = p.get("FishTypes_1") or ""
        if wb and fish:
            by.setdefault(wb, set()).update(s.strip() for s in fish.split(",") if s.strip())
    return by


def scrape(limit=None):
    print("[MD] Fetching MD DNR angler-access species...")
    species_by_water = _species_by_water(limit=limit)
    print(f"[MD] species for {len(species_by_water)} waters. Fetching lakes...")
    features = fetch_arcgis(_LAYER, where="LAKENAME<>''",
                            out_fields="LAKENAME,COUNTY,ACRES", limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("LAKENAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("ACRES")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("COUNTY") or "").title() or None,
            area=f"{round(acres, 1)} Acres" if acres else "Unknown",
            species=sorted(species_by_water.get(name.lower(), set())), url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[MD] Collected {len(records)} lakes ({withsp} with species).")
    return records
