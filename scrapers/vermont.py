"""Vermont state scraper (Vermont Fish & Wildlife).

Source: Vermont ANR "Fishing Access Areas" ArcGIS MapServer (points). Point
features with water name, town/county, acreage and per-species presence flags
("Yes"/"No") across many columns.

Layer: https://anrmaps.vermont.gov/arcgis/rest/services/Open_Data/OPENDATA_ANR_TOURISM_SP_NOCACHE_v2/MapServer/163
"""

import re

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Vermont"
STATE_CODE = "vt"

_LAYER = "https://anrmaps.vermont.gov/arcgis/rest/services/Open_Data/OPENDATA_ANR_TOURISM_SP_NOCACHE_v2/MapServer/163"
_URL = "https://vtfishandwildlife.com/fish"

# Candidate per-species boolean columns ("Yes"/"No"). Missing ones are ignored,
# so listing extras is harmless.
_SPECIES_COLS = [
    "BrookTrout", "BrownTrout", "RainbowTrout", "LakeTrout", "LandlockedSalmon",
    "Walleye", "NorthernPike", "LargemouthBass", "SmallmouthBass", "YellowPerch",
    "ChainPickerel", "Muskellunge", "BlackCrappie", "Bullhead", "Panfish",
    "WhitePerch", "RockBass", "Pumpkinseed", "Bluegill", "Sunfish", "Salmon",
    "Sauger", "Sturgeon", "Bowfin", "Catfish", "Carp", "Cisco", "Whitefish",
    "Burbot", "Shad", "Crappie",
]


def _spaced(name):
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def scrape(limit=None):
    print("[VT] Fetching Vermont fishing access areas...")
    # Request all fields: the species columns vary, and naming a nonexistent
    # outField makes ArcGIS reject the whole query.
    features = fetch_arcgis(_LAYER, out_fields="*", limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WaterBody") or "").strip()
        if not name:
            continue
        lat, lon = p.get("CoordY"), p.get("CoordX")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        species = [_spaced(col) for col in _SPECIES_COLS
                   if str(p.get(col)).strip().lower() == "yes"]
        acres = p.get("LakeArea")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("County") or "").title() or None,
            area=f"{acres} Acres" if acres else "Unknown",
            species=species, url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[VT] Collected {len(records)} waters.")
    return records
