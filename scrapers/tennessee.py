"""Tennessee state scraper (TWRA).

Base: TWRA "Boating & Fishing Access Sites" (Body_of_Wa, county, coords),
deduped per water body. Species: TWRA "where to fish" reservoir pages list
species in prose; discovered by probing the four region paths for each water's
slug and keyword-extracting species. Only the major reservoirs have pages.

Base:  https://tnmap.tn.gov/arcgis/rest/services/ENVIRONMENTAL/TWRA/MapServer/1
Pages: https://www.tn.gov/twra/fishing/where-to-fish/<region>/<slug>-reservoir.html
"""

import concurrent.futures
import re

import requests

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Tennessee"
STATE_CODE = "tn"

_LAYER = "https://tnmap.tn.gov/arcgis/rest/services/ENVIRONMENTAL/TWRA/MapServer/1"
_REGIONS = ["east-tennessee-r4", "west-tennessee-r1", "middle-tennessee-r2", "cumberland-plateau-r3"]
_PAGE = "https://www.tn.gov/twra/fishing/where-to-fish/{}/{}-reservoir.html"
_HEADERS = {"User-Agent": "Mozilla/5.0"}
_URL = "https://www.tn.gov/twra/fishing.html"

_KEYWORDS = {
    "largemouth bass": "Largemouth Bass", "smallmouth bass": "Smallmouth Bass",
    "spotted bass": "Spotted Bass", "striped bass": "Striped Bass",
    "white bass": "White Bass", "yellow bass": "Yellow Bass",
    "hybrid": "Hybrid Striped Bass", "black crappie": "Black Crappie",
    "white crappie": "White Crappie", "crappie": "Crappie",
    "channel catfish": "Channel Catfish", "blue catfish": "Blue Catfish",
    "flathead catfish": "Flathead Catfish", "bluegill": "Bluegill",
    "redear": "Redear Sunfish", "walleye": "Walleye", "sauger": "Sauger",
    "muskie": "Muskellunge", "muskellunge": "Muskellunge",
    "rainbow trout": "Rainbow Trout", "brown trout": "Brown Trout",
    "brook trout": "Brook Trout",
}


def _slug(name):
    s = re.sub(r"\b(lake|reservoir|dam)\b", " ", name.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _fetch_species(name):
    slug = _slug(name)
    if not slug:
        return name, []
    for region in _REGIONS:
        try:
            r = requests.get(_PAGE.format(region, slug), headers=_HEADERS, timeout=20)
        except Exception:
            continue
        if r.status_code != 200:
            continue
        txt = r.text.lower()
        found = {v for k, v in _KEYWORDS.items() if k in txt}
        if found:
            return name, sorted(found)
    return name, []


def scrape(limit=None):
    print("[TN] Fetching TWRA access sites...")
    features = fetch_arcgis(_LAYER, out_fields="Body_of_Wa,Latitude,Longitude,County",
                            limit=limit, page_size=1000)
    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Body_of_Wa") or "").strip()
        if not name or name in waters:
            continue
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        waters[name] = {"lat": lat, "lon": lon, "county": p.get("County")}

    print(f"[TN] probing reservoir pages for {len(waters)} waters...")
    species_by_name = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        for name, sp in ex.map(_fetch_species, list(waters)):
            species_by_name[name] = sp

    records = [make_record(name=name.title(), state=STATE_NAME, lat=w["lat"], lon=w["lon"],
                           county=(w["county"] or "").title() or None,
                           species=species_by_name.get(name, []), url=_URL)
               for name, w in waters.items()]
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[TN] Collected {len(records)} waters ({withsp} with species).")
    return records
