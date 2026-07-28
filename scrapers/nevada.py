"""Nevada state scraper (Nevada Department of Wildlife).

Source: NDOW "Fishable Waters" ArcGIS FeatureServer, layer 1 (Fishable Lakes &
Reservoirs). Polygon features with a name, county and up to 11 species slots
encoded as short abbreviation codes (FISH1..FISH11). Rivers are a separate
layer we don't use.

Layer: https://services.arcgis.com/RyxlXSfFi87rAosq/arcgis/rest/services/NDOWFishableWaters/FeatureServer/1
"""

import re

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Nevada"
STATE_CODE = "nv"

_LAYER = "https://services.arcgis.com/RyxlXSfFi87rAosq/arcgis/rest/services/NDOWFishableWaters/FeatureServer/1"
_URL = "https://www.ndow.org/activity/fishing/"

# NDOW fish abbreviation codes -> common names. Unmapped codes are kept as-is
# (uppercased) so nothing is silently invented; see scrapers/README.md.
_FISH_CODES = {
    "RB": "Rainbow Trout", "BN": "Brown Trout", "BK": "Brook Trout",
    "CT": "Cutthroat Trout", "MK": "Lake Trout", "KOK": "Kokanee",
    "KO": "Kokanee", "BG": "Bluegill", "LMB": "Largemouth Bass",
    "SMB": "Smallmouth Bass", "SB": "Striped Bass", "WB": "White Bass",
    "WP": "Wiper", "CC": "Channel Catfish", "BB": "Brown Bullhead",
    "WE": "Walleye", "YP": "Yellow Perch", "CP": "Crappie",
    "WH": "Mountain Whitefish", "SP": "Sacramento Perch",
}

_FISH_KEY = re.compile(r"^FISH\d+_?$")


def scrape(limit=None):
    print("[NV] Fetching NDOW fishable lakes & reservoirs...")
    features = fetch_arcgis(_LAYER, limit=limit, page_size=1000)
    print(f"[NV] {len(features)} lake polygons.")

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue

        species = []
        for key, val in p.items():
            if not _FISH_KEY.match(key.upper()):
                continue
            code = (val or "").strip().upper()
            if not code:
                continue
            species.append(_FISH_CODES.get(code, code.title()))

        records.append(make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon,
            county=p.get("COUNTY_NAM"),
            species=species, url=_URL,
            description=(p.get("TYPE") or "").strip(),
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[NV] Collected {len(records)} lakes.")
    return records
