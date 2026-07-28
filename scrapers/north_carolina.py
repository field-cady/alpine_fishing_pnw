"""North Carolina state scraper (NC Wildlife Resources Commission).

Base lakes: NCWRC "Public Fishing Areas" ArcGIS layer (LAKE/POND, name, county,
coords). Species: NCWRC's public "Fishing Areas" app JSON endpoints
(ncpaws.org), joined by fishing-area name.

Base: https://services1.arcgis.com/YfqBAUM5nWR3yhGP/arcgis/rest/services/NCWRC_Public_Fishing_Areas_view/FeatureServer/0
API:  https://www.ncpaws.org/NCWRCMaps/FishingAreas/Home/{GetFilteredFishingAreas,GetFishingAreaInfo}
"""

import concurrent.futures

import requests

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "North Carolina"
STATE_CODE = "nc"

_LAYER = "https://services1.arcgis.com/YfqBAUM5nWR3yhGP/arcgis/rest/services/NCWRC_Public_Fishing_Areas_view/FeatureServer/0"
_LIST = "https://www.ncpaws.org/NCWRCMaps/FishingAreas/Home/GetFilteredFishingAreas"
_INFO = "https://www.ncpaws.org/NCWRCMaps/FishingAreas/Home/GetFishingAreaInfo?locationID={}"
_HEADERS = {"User-Agent": "Mozilla/5.0"}
_URL = "https://www.ncwildlife.org/fishing"


def _name_to_id():
    try:
        rows = requests.get(_LIST, headers=_HEADERS, timeout=60).json()
    except Exception as e:
        print(f"[NC] fishing-area list failed: {e}")
        return {}
    return {(r.get("locationName") or "").strip().upper(): r.get("locationID")
            for r in rows if r.get("locationName") and r.get("locationID")}


def _species_for_id(loc_id):
    try:
        d = requests.get(_INFO.format(loc_id), headers=_HEADERS, timeout=20).json()
        return loc_id, [s.get("commonName", "").strip()
                        for s in (d.get("speciesInfo") or []) if s.get("commonName")]
    except Exception:
        return loc_id, []


def scrape(limit=None):
    print("[NC] Fetching NCWRC fishing-area index...")
    name_to_id = _name_to_id()
    features = fetch_arcgis(_LAYER, where="Waterbody_Type IN ('LAKE','POND')",
                            out_fields="PFA_Name,Latitude,Longitude,County,Waterbody_Type",
                            limit=limit, page_size=1000)
    # Resolve species only for the lakes we actually have.
    needed = {}
    for feat in features:
        nm = (feat.get("properties", {}).get("PFA_Name") or "").strip().upper()
        if nm in name_to_id:
            needed[nm] = name_to_id[nm]
    print(f"[NC] fetching species for {len(needed)} matched areas...")
    species_by_name = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_species_for_id, lid): nm for nm, lid in needed.items()}
        for fut in concurrent.futures.as_completed(futures):
            nm = futures[fut]
            _, sp = fut.result()
            species_by_name[nm] = sp

    records, seen = [], set()
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("PFA_Name") or "").strip()
        if not name or name.upper() in seen:
            continue
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        seen.add(name.upper())
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("County") or "").title() or None,
            species=species_by_name.get(name.upper(), []), url=_URL,
            description=(p.get("Waterbody_Type") or "").title(),
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[NC] Collected {len(records)} waters ({withsp} with species).")
    return records
