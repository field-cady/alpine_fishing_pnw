"""Pennsylvania state scraper (PA Fish & Boat Commission via PASDA).

Base lakes: PFBC "Lakes Point" (layer 19) -- name, county, acreage, coords.
Species: companion layers on the same PASDA service, joined by ``GIS_Key``:
  - layer 27 "WWCW Fisheries Lakes" -- warm/coolwater species as Yes columns
  - layer 12 "Best Fishing Waters" -- adds trout species columns
  - layer 1  "Stocked Trout Waterbodies" -- membership implies trout

Service: https://services.pasda.psu.edu/server/rest/services/pasda/PAFishBoat/MapServer
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Pennsylvania"
STATE_CODE = "pa"

_SVC = "https://services.pasda.psu.edu/server/rest/services/pasda/PAFishBoat/MapServer"
_LAKES = _SVC + "/19"
_WWCW = _SVC + "/27"
_BEST = _SVC + "/12"
_TROUT = _SVC + "/1"
_URL = "https://www.fishandboat.com/Fish/FishingBoating/Pages/default.aspx"

# Per-species "Yes" columns (names are truncated in the source).
_SPECIES_COLS = {
    "Black_Crap": "Black Crappie", "Bluegill": "Bluegill", "Bullheads": "Bullhead",
    "Chain_Pick": "Chain Pickerel", "Common_Car": "Common Carp",
    "Flathead_C": "Flathead Catfish", "Muskellung": "Muskellunge",
    "Largemouth": "Largemouth Bass", "Channel_Ca": "Channel Catfish",
    "Northern_P": "Northern Pike", "Pumpkinsee": "Pumpkinseed",
    "Redbreast_": "Redbreast Sunfish", "Redear_Sun": "Redear Sunfish",
    "Rock_Bass": "Rock Bass", "Sauger": "Sauger", "Saugeye": "Saugeye",
    "Smallmouth": "Smallmouth Bass", "Spotted_Ba": "Spotted Bass",
    "Striped_Ba": "Striped Bass", "Tiger_Musk": "Tiger Muskie", "Walleye": "Walleye",
    "White_Bass": "White Bass", "White_Crap": "White Crappie",
    "White_Perc": "White Perch", "Yellow_Per": "Yellow Perch",
    "Brook_trou": "Brook Trout", "Brown_Trou": "Brown Trout", "Rainbow_Tr": "Rainbow Trout",
}


def _flag_species(layer, species_by_key, limit=None):
    for feat in fetch_arcgis(layer, out_fields="*", limit=limit, page_size=2000):
        p = feat.get("properties", {})
        key = p.get("GIS_Key")
        if not key:
            continue
        for col, name in _SPECIES_COLS.items():
            if str(p.get(col)).strip().lower() == "yes":
                species_by_key.setdefault(key, set()).add(name)


def scrape(limit=None):
    print("[PA] Fetching PFBC species (WWCW + best-waters + trout)...")
    species_by_key = {}
    _flag_species(_WWCW, species_by_key, limit=limit)
    _flag_species(_BEST, species_by_key, limit=limit)
    for feat in fetch_arcgis(_TROUT, out_fields="GIS_Key", limit=limit, page_size=2000):
        key = feat.get("properties", {}).get("GIS_Key")
        if key:
            species_by_key.setdefault(key, set()).add("Trout")

    print(f"[PA] species for {len(species_by_key)} waters. Fetching lakes...")
    features = fetch_arcgis(_LAKES, out_fields="WtrName,County,Latitude,Longitude,AreaAcres,GIS_Key",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WtrName") or "").strip()
        if not name:
            continue
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("AreaAcres")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("County") or "").title() or None,
            area=f"{acres} Acres" if acres else "Unknown",
            species=sorted(species_by_key.get(p.get("GIS_Key"), set())), url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[PA] Collected {len(records)} lakes ({withsp} with species).")
    return records
