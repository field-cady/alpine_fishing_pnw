"""Minnesota state scraper (Minnesota DNR).

Base lakes come from the MN DNR "Lakes surveyed by MNDNR" GIS layer (name,
county, acreage, DOW id). Species are enriched per lake from the DNR LakeFinder
JSON API, keyed by the 8-digit DOW number.

GIS:        https://enterprise.gisdata.mn.gov/aghost/rest/services/us_mn_state_dnr/env_lakes_surveyed_by_mndnr/FeatureServer/0
LakeFinder: http://services.dnr.state.mn.us/api/lakefinder/by_id/v1/?id=<DOW>&format=json
"""

import concurrent.futures

import requests

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Minnesota"
STATE_CODE = "mn"

_LAYER = "https://enterprise.gisdata.mn.gov/aghost/rest/services/us_mn_state_dnr/env_lakes_surveyed_by_mndnr/FeatureServer/0"
_LAKEFINDER = "http://services.dnr.state.mn.us/api/lakefinder/by_id/v1/?id={}&format=json"
_URL = "https://www.dnr.state.mn.us/lakefind/index.html"


def _species_for_dow(dow):
    try:
        r = requests.get(_LAKEFINDER.format(dow), timeout=15)
        results = r.json().get("results") or []
        if not results:
            return dow, []
        fish = results[0].get("fishSpecies") or []
        species = []
        for chunk in fish:
            species += [s.strip() for s in str(chunk).split(",") if s.strip()]
        return dow, species
    except Exception:
        return dow, []


def scrape(limit=None):
    print("[MN] Fetching MN DNR surveyed lakes...")
    features = fetch_arcgis(
        _LAYER, out_fields="pw_basin_name,pw_parent_name,cty_name,acres,dowlknum",
        limit=limit, page_size=1000,
    )

    lakes = []
    dows = set()
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("pw_basin_name") or p.get("pw_parent_name") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        dow = str(p.get("dowlknum") or "").strip()
        lakes.append((p, name, lat, lon, dow))
        if dow:
            dows.add(dow)

    print(f"[MN] {len(lakes)} lakes; fetching species for {len(dows)} DOW ids via LakeFinder...")
    species_by_dow = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for i, (dow, sp) in enumerate(ex.map(_species_for_dow, dows), 1):
            species_by_dow[dow] = sp
            if i % 500 == 0:
                print(f"[MN]   {i}/{len(dows)} LakeFinder lookups...")

    records = []
    for p, name, lat, lon, dow in lakes:
        acres = p.get("acres")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("cty_name") or "").title() or None,
            area=f"{round(acres, 1)} Acres" if acres else "Unknown",
            species=species_by_dow.get(dow, []), url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[MN] Collected {len(records)} lakes ({withsp} with species).")
    return records
