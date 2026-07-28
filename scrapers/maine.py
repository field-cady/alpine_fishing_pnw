"""Maine state scraper (Maine Office of GIS / MDIFW).

Base: Maine GIS "PublicMasterWaters" lentic waters (name, lat/long, acres,
mgtwbid). Species: MDIFW "Heritage Fish Waters" (wild brook trout / arctic
charr and last-stocked species), joined by MIDAS id (mgtwbid <-> WATCODE).
Only the ~589 heritage/managed trout waters get species.

Waters:   https://gis.maine.gov/arcgis/rest/services/Hosted/PublicMasterWaters/FeatureServer/1
Heritage: https://gis.maine.gov/mapservices/rest/services/ifw/Maine_Heritage_Fish_Waters/MapServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Maine"
STATE_CODE = "me"

_LAYER = "https://gis.maine.gov/arcgis/rest/services/Hosted/PublicMasterWaters/FeatureServer/1"
_HERITAGE = "https://gis.maine.gov/mapservices/rest/services/ifw/Maine_Heritage_Fish_Waters/MapServer/0"
_URL = "https://www.maine.gov/ifw/fishing-boating/fishing/"

_CODES = {"BKT": "Brook Trout", "CHR": "Arctic Charr", "LKT": "Lake Trout",
          "RBT": "Rainbow Trout", "SPC": "Splake", "SPK": "Splake",
          "LLS": "Landlocked Salmon", "BNT": "Brown Trout"}


def _decode(*values):
    out = set()
    for v in values:
        if not v:
            continue
        for tok in str(v).replace("-", ",").split(","):
            tok = tok.strip().upper()
            if tok in _CODES:
                out.add(_CODES[tok])
    return out


def _species_by_midas(limit=None):
    by = {}
    for feat in fetch_arcgis(_HERITAGE, out_fields="WATCODE_NUMBER,HRTG_FISH,SpeciesLastStocked",
                             limit=limit, page_size=2000):
        p = feat.get("properties", {})
        midas = p.get("WATCODE_NUMBER")
        if midas is None:
            continue
        sp = _decode(p.get("HRTG_FISH"), p.get("SpeciesLastStocked"))
        if sp:
            by[int(midas)] = by.get(int(midas), set()) | sp
    return by


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def scrape(limit=None):
    print("[ME] Fetching MDIFW heritage-fish species...")
    species_by_midas = _species_by_midas(limit=limit)
    print(f"[ME] species for {len(species_by_midas)} waters. Fetching lentic waters...")
    features = fetch_arcgis(_LAYER, where="wtype='Lentic'",
                            out_fields="name,lat,long,acres,mgtwbid", limit=limit, page_size=2000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("name") or "").strip()
        lat, lon = _to_float(p.get("lat")), _to_float(p.get("long"))
        if not name or lat is None or lon is None:
            continue
        try:
            midas = int(str(p.get("mgtwbid") or "").strip() or -1)
        except ValueError:
            midas = -1
        acres = p.get("acres")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=f"{acres} Acres" if acres else "Unknown",
            species=sorted(species_by_midas.get(midas, set())), url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[ME] Collected {len(records)} waters ({withsp} with species).")
    return records
