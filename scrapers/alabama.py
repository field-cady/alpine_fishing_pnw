"""Alabama state scraper (ADCNR).

Base: ADCNR "Public Fishing Lakes" (name, coords, and a per-lake `Link` to its
Outdoor Alabama page). Species are keyword-scraped from each lake page (the 20
state PFLs are stocked with a small, well-known species set).

Layer: https://conservationgis.alabama.gov/adcnrweb/rest/services/PublicFishingLakes/MapServer/0
"""

import concurrent.futures

import requests

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Alabama"
STATE_CODE = "al"

_LAYER = "https://conservationgis.alabama.gov/adcnrweb/rest/services/PublicFishingLakes/MapServer/0"
_URL = "https://www.outdooralabama.com/fishing/public-fishing-lakes"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

_KEYWORDS = {
    "largemouth bass": "Largemouth Bass", "redear": "Redear Sunfish",
    "shellcracker": "Redear Sunfish", "channel catfish": "Channel Catfish",
    "black crappie": "Black Crappie", "white crappie": "White Crappie",
    "crappie": "Crappie", "bluegill": "Bluegill", "rainbow trout": "Rainbow Trout",
    "hybrid": "Hybrid Striped Bass",
}


def _page_species(link):
    if not link:
        return set()
    try:
        txt = requests.get(link, headers=_HEADERS, timeout=20).text.lower()
    except Exception:
        return set()
    return {name for kw, name in _KEYWORDS.items() if kw in txt}


def scrape(limit=None):
    print("[AL] Fetching ADCNR public fishing lakes + species pages...")
    features = fetch_arcgis(_LAYER, out_fields="Name,Link", limit=limit, page_size=1000)
    rows = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Name") or p.get("NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        rows.append((name, lat, lon, p.get("Link")))

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        species_lists = list(ex.map(lambda r: _page_species(r[3]), rows))

    records = [make_record(name=name, state=STATE_NAME, lat=lat, lon=lon,
                           species=sorted(sp), url=link or _URL)
               for (name, lat, lon, link), sp in zip(rows, species_lists)]
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[AL] Collected {len(records)} lakes ({withsp} with species).")
    return records
