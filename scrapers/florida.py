"""Florida state scraper (Florida FWC).

Base lakes come from FWC "LAKES_POINTS" (named lakes with county + coords).
FWC exposes no per-lake species list; the only queryable species source is the
county-level "Fish Ranges" layer (species present per county). We attach those
county species to each lake -- so Florida species are COUNTY-LEVEL ranges, not
per-lake surveys.

Lakes:  https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/LAKES_POINTS/FeatureServer/0
Ranges: https://gis.myfwc.com/hosting/rest/services/Projects_FWC/Fish_Range_Map/MapServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Florida"
STATE_CODE = "fl"

_LAKES = "https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/LAKES_POINTS/FeatureServer/0"
_RANGES = "https://gis.myfwc.com/hosting/rest/services/Projects_FWC/Fish_Range_Map/MapServer/0"
_URL = "https://myfwc.com/fishing/freshwater/"


def _species_by_county(limit=None):
    by = {}
    for f in fetch_arcgis(_RANGES, out_fields="COUNTY,SpeciesPresent", limit=limit, page_size=2000):
        p = f.get("properties", {})
        county = (p.get("COUNTY") or "").strip().lower()
        raw = p.get("SpeciesPresent") or ""
        if county and raw:
            by[county] = [s.strip() for s in raw.split(",") if s.strip()]
    return by


def scrape(limit=None):
    print("[FL] Fetching FWC county fish ranges...")
    county_species = _species_by_county(limit=limit)
    print(f"[FL] species for {len(county_species)} counties. Fetching lakes...")
    features = fetch_arcgis(_LAKES, out_fields="NAME,COUNTY", limit=limit, page_size=2000)

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        county = (p.get("COUNTY") or "").strip()
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=county.title() or None,
            species=county_species.get(county.lower(), []), url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[FL] Collected {len(records)} lakes ({withsp} with county-level species).")
    return records
