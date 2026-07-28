"""Indiana state scraper (Indiana DNR Fish & Wildlife).

Source: IDNR "Fish Access" ArcGIS FeatureServer (points) via IndianaMap. Each
feature is a fishing-access site with a waterbody, county and free-text
species. We keep standing waters and aggregate access sites into one record
per waterbody, unioning the species text.

Layer: https://gisdata.in.gov/server/rest/services/Hosted/Fish_Access_RO/FeatureServer/0
"""

from .base import make_record, fetch_arcgis

STATE_NAME = "Indiana"
STATE_CODE = "in"

_LAYER = "https://gisdata.in.gov/server/rest/services/Hosted/Fish_Access_RO/FeatureServer/0"
_URL = "https://www.in.gov/dnr/fish-and-wildlife/fishing/"


def _split_species(*values):
    out = []
    for v in values:
        if v:
            out.extend(s.strip() for s in str(v).split(",") if s.strip())
    return out


def scrape(limit=None):
    print("[IN] Fetching IDNR fishing-access sites (lakes)...")
    features = fetch_arcgis(
        _LAYER,
        where="water_type IN ('Lake','Reservoir','Pond','Pit')",
        out_fields="waterbody,lat_y,long_x,county,species,species2",
        limit=limit, page_size=2000,
    )
    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("waterbody") or "").strip()
        lat, lon = p.get("lat_y"), p.get("long_x")
        if not name or lat is None or lon is None:
            continue
        w = waters.get(name)
        if w is None:
            w = waters[name] = {"lat": lat, "lon": lon,
                                "county": p.get("county"), "species": set()}
        w["species"].update(_split_species(p.get("species"), p.get("species2")))

    records = [make_record(
        name=name.title(), state=STATE_NAME, lat=w["lat"], lon=w["lon"],
        county=(w["county"] or "").title() or None,
        species=sorted(w["species"]), url=_URL,
    ) for name, w in waters.items()]
    records.sort(key=lambda r: r["name"])
    print(f"[IN] Collected {len(records)} waters.")
    return records
