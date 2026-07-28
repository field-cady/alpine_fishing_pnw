"""Washington state scraper (WDFW).

Two WDFW sources are combined for broad statewide coverage:

1. High Lakes -- the WDFW high-lakes HTML listings (alpine lakes >2500 ft).
   Trout-focused but carries elevation and the starting/overabundant flags.
2. Fish Washington lowland lakes -- the "Fish Washington" app ArcGIS MapServer
   (FishWA_2014_AllLakes_PROD). A base lake layer plus one point layer per
   species, giving kokanee, bass, walleye, muskie, perch, crappie, bluegill,
   bullhead and trout statewide.

The two sets are unioned and deduped by name + rounded coordinates so alpine
trout lakes and lowland warmwater/kokanee lakes both appear.
"""

import time

import requests
from bs4 import BeautifulSoup

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Washington"
STATE_CODE = "wa"

# --- Source 1: WDFW high lakes (HTML) ---------------------------------------
_ALL_URL = 'https://wdfw.wa.gov/fishing/locations/high-lakes?name=&county=All&species=&order=title&sort=asc&page='
_STARTING_URL = 'https://wdfw.wa.gov/fishing/locations/high-lakes/getting-started?name=&county=All&species=&order=title&sort=asc&page='
_OVERABUNDANT_URL = 'https://wdfw.wa.gov/fishing/locations/high-lakes/overabundant?name=&county=All&species=&order=title&sort=asc&page='
MIN_ELEVATION = 2500.0
SPECIES_MAP = {
    "21178": "Brook trout", "21419": "Brown bullhead", "21173": "Brown trout",
    "74140": "Cutthroat trout", "21184": "Golden trout", "21152": "Rainbow trout",
}

# --- Source 2: WDFW Fish Washington lowland lakes (ArcGIS) -------------------
_FISHWA = "https://geodataservices.wdfw.wa.gov/arcgis/rest/services/ApplicationServices/FishWA_2014_AllLakes_PROD/MapServer"
_FISHWA_BASE_LAYER = 2  # Lowland Lakes (base list)
_FISHWA_SPECIES_LAYERS = {
    4: "Rainbow Trout", 5: "Brown Trout", 6: "Brook Trout", 7: "Tiger Trout",
    8: "Coastal Cutthroat Trout", 9: "Kokanee", 10: "Largemouth Bass",
    11: "Smallmouth Bass", 12: "Walleye", 13: "Tiger Muskie", 14: "Brown Bullhead",
    15: "Yellow Perch", 16: "Black Crappie", 17: "Pumpkinseed", 18: "Bluegill",
}
_FISHWA_URL = "https://wdfw.wa.gov/fishing/locations"


# --------------------------------------------------------------------------- #
# Source 1: high lakes
# --------------------------------------------------------------------------- #
def _parse_table_from_page(txt):
    soup = BeautifulSoup(txt, features="lxml")
    table = soup.find("table")
    if not table:
        return []
    tbody = table.find('tbody')
    if not tbody:
        return []
    fields = ['name', 'area', 'elevation', 'county', 'location']
    rows = []
    for row in tbody.findAll('tr'):
        col = row.findAll('td')
        if len(col) != 5:
            continue
        rows.append(dict(zip(fields, col)))
    return rows


def _html_to_row(r):
    try:
        name = r["name"].find("a").string.strip()
        descriptors = ['lake', 'pond', 'pothole', 'reservoir', 'pot', 'lakes']
        if not any(d in name.lower() for d in descriptors):
            name += " Lake"
        url = "https://wdfw.wa.gov" + r["name"].find("a").get("href")
        elevation = r["elevation"].string.strip().replace(',', '').split()[0]
        county = r["county"].string.strip()
        area = r["area"].string.strip().split()[0] + " Acres"
        latlon = [x.string.strip() for x in r["location"].findAll("span")]
        return dict(name=name, url=url, elevation=float(elevation), county=county,
                    lat=float(latlon[0]), lon=float(latlon[1]), area=area)
    except Exception:
        return None


def _get_rows_from_all_pages(url_base, max_pages=None):
    i = 0
    out = []
    while True:
        if max_pages is not None and i >= max_pages:
            break
        r = requests.get(url_base + str(i))
        parsed = _parse_table_from_page(r.text)
        rows = [row for row in (_html_to_row(rw) for rw in parsed if rw) if row]
        if not rows:
            break
        out.extend(rows)
        i += 1
        time.sleep(0.3)
    return out


def _scrape_high_lakes(limit=None):
    print("[WA] Fetching high lakes (WDFW HTML)...")
    all_rows = [lk for lk in _get_rows_from_all_pages(_ALL_URL, max_pages=limit)
                if lk['elevation'] > MIN_ELEVATION]
    overabundant = {lk['url'] for lk in _get_rows_from_all_pages(_OVERABUNDANT_URL, max_pages=limit)}
    starting = {lk['url'] for lk in _get_rows_from_all_pages(_STARTING_URL, max_pages=limit)}

    lake_species = {}
    for sp_id, sp_name in SPECIES_MAP.items():
        sp_url = f"https://wdfw.wa.gov/fishing/locations/high-lakes?name=&county=All&species={sp_id}&order=title&sort=asc&page="
        for lk in _get_rows_from_all_pages(sp_url, max_pages=limit):
            lake_species.setdefault(lk['url'], []).append(sp_name)

    records = []
    for lk in all_rows:
        records.append(make_record(
            name=lk['name'], state=STATE_NAME, lat=lk['lat'], lon=lk['lon'],
            elevation=lk['elevation'], area=lk['area'], county=lk['county'],
            species=lake_species.get(lk['url'], []), url=lk['url'],
            starting=lk['url'] in starting, overabundant=lk['url'] in overabundant,
        ))
    print(f"[WA] High lakes: {len(records)}")
    return records


# --------------------------------------------------------------------------- #
# Source 2: Fish Washington lowland lakes
# --------------------------------------------------------------------------- #
def _fishwa_features(layer, limit=None):
    url = f"{_FISHWA}/{layer}"
    return fetch_arcgis(url, out_fields="LakeName,CountyName,ELEV,SurfaceAcres,PublicManagementType",
                        limit=limit, page_size=2000)


def _scrape_lowland(limit=None):
    print("[WA] Fetching Fish Washington lowland lakes (ArcGIS)...")
    lakes = {}   # (name.lower, county.lower) -> dict

    def touch(feat):
        p = feat.get("properties", {})
        name = (p.get("LakeName") or "").strip()
        if not name:
            return None
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            return None
        county = (p.get("CountyName") or "").strip()
        key = (name.lower(), county.lower())
        w = lakes.get(key)
        if w is None:
            w = lakes[key] = {
                "name": name, "county": county or None, "lat": lat, "lon": lon,
                "elevation": p.get("ELEV"), "acres": p.get("SurfaceAcres"),
                "mgmt": (p.get("PublicManagementType") or "").strip(), "species": set(),
            }
        return w

    # Base lake list (no species) then each per-species layer.
    for feat in _fishwa_features(_FISHWA_BASE_LAYER, limit=limit):
        touch(feat)
    for layer, species in _FISHWA_SPECIES_LAYERS.items():
        for feat in _fishwa_features(layer, limit=limit):
            w = touch(feat)
            if w is not None:
                w["species"].add(species)

    records = []
    for w in lakes.values():
        elev = w["elevation"]
        records.append(make_record(
            name=w["name"], state=STATE_NAME, lat=w["lat"], lon=w["lon"],
            elevation=float(elev) if elev else None,
            county=w["county"],
            area=f"{w['acres']} Acres" if w["acres"] else "Unknown",
            species=sorted(w["species"]), url=_FISHWA_URL,
            description=w["mgmt"],
        ))
    print(f"[WA] Lowland lakes: {len(records)}")
    return records


# --------------------------------------------------------------------------- #
def scrape(limit=None):
    """Union of WDFW high lakes and Fish Washington lowland lakes."""
    records = _scrape_high_lakes(limit) + _scrape_lowland(limit)

    # Dedup by name + coarse location; merge species and fill gaps.
    combined = {}
    for rec in records:
        key = (rec["name"].strip().lower(), round(rec["lat"], 2), round(rec["lon"], 2))
        cur = combined.get(key)
        if cur is None:
            combined[key] = rec
            continue
        cur["species"] = sorted(set(cur.get("species") or []) | set(rec.get("species") or []))
        for f in ("elevation", "county"):
            if not cur.get(f) and rec.get(f):
                cur[f] = rec[f]
        if cur.get("area") in (None, "Unknown") and rec.get("area") not in (None, "Unknown"):
            cur["area"] = rec["area"]
        for f in ("starting", "overabundant"):
            if rec.get(f):
                cur[f] = rec[f]

    out = sorted(combined.values(), key=lambda r: r["name"])
    print(f"[WA] Collected {len(out)} lakes (high + lowland, deduped).")
    return out
