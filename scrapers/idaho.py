"""Idaho state scraper (IDFG high mountain lakes).

IDFG's fishing planner exposes a JSON API. We first fetch the set of
high-mountain-lake ids (the ``body=3`` list), then pull the matching rows from
the master water list, and finally scrape each lake's page for its species.
Only the high-mountain subset is scraped, so this stays light on IDFG's
servers.
"""

import concurrent.futures
import json

import requests
from bs4 import BeautifulSoup

from .base import make_record, data_path

STATE_NAME = "Idaho"
STATE_CODE = "id"

_API_LIST = "https://idfg.idaho.gov/ifwis/fishingplanner/api/2.0/list/"
_WATER_URL = "https://idfg.idaho.gov/ifwis/fishingplanner/water/{}"
_HML_IDS_PATH = data_path("idaho_high_mountain_ids.json")


def _fetch_high_mountain_ids():
    """Fetch the set of high-mountain-lake ids and cache them to data/."""
    r = requests.get(_API_LIST, params={'body': '3', 'limit': 15000})
    rows = r.json().get('rows', [])
    ids = [d['id'] for d in rows if 'id' in d]
    with open(_HML_IDS_PATH, 'w') as f:
        json.dump(ids, f)
    print(f"[ID] {len(ids)} high mountain lake ids.")
    return set(ids)


def _fetch_water_list():
    r = requests.get(_API_LIST, params={'limit': 15000})
    return r.json().get('rows', [])


def _parse_species(html):
    soup = BeautifulSoup(html, 'html.parser')
    species = set()
    keywords = ['game fish', 'species observed', 'fish present']
    for h in soup.find_all(['h2', 'h3', 'h4']):
        if not any(kw in h.text.lower() for kw in keywords):
            continue
        ul = h.find_next_sibling('ul')
        if not ul:
            continue
        for li in ul.find_all('li'):
            li_text = li.text.strip()
            if '(' in li_text:
                li_text = li_text.split('(')[0].strip()
            if ' observed in ' in li_text:
                name_part = li_text.split(' observed in ')[0]
                words = name_part.split()
                if len(words) >= 4:
                    name_part = " ".join(words[:2])  # rough fallback
                li_text = name_part
            species.add(li_text)
    return list(species)


def _lat_lon_from_id(water_id):
    """Idaho ids encode coordinates: 7 digits lon, 6 digits lat."""
    id_str = str(water_id)
    if len(id_str) != 13:
        return None, None
    lon = -(float(id_str[:7]) / 10000.0)
    lat = float(id_str[7:]) / 10000.0
    return lat, lon


def _fetch_record(lake):
    """Fetch species for one lake row and build a normalized record."""
    water_id = lake.get('id')
    try:
        r = requests.get(_WATER_URL.format(water_id), timeout=10)
        species = _parse_species(r.text)
    except Exception as e:
        print(f"[ID] Error fetching {lake.get('name')}: {e}")
        species = []

    lat, lon = _lat_lon_from_id(water_id)
    size = lake.get('size')
    return make_record(
        name=lake.get('name', 'Unknown'),
        state=STATE_NAME,
        lat=lat,
        lon=lon,
        area=f"{size} Acres" if size else "Unknown",
        county=lake.get('loc', 'Unknown'),
        species=species,
        url=_WATER_URL.format(water_id),
    )


def scrape(limit=None):
    """Scrape IDFG high mountain lakes and return normalized records.

    ``limit`` caps the number of lakes scraped (used for smoke runs).
    """
    print("[ID] Fetching high mountain lake ids...")
    hml_ids = _fetch_high_mountain_ids()

    print("[ID] Fetching master water list...")
    waters = [w for w in _fetch_water_list()
              if w.get('layer') == 0 and w.get('id') in hml_ids]
    if limit is not None:
        waters = waters[:limit]
    print(f"[ID] Scraping species for {len(waters)} high mountain lakes...")

    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_fetch_record, w) for w in waters]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            rec = future.result()
            # Match previous behavior: only keep lakes we can place on the map.
            if rec['lat'] is not None and rec['lon'] is not None:
                records.append(rec)
            if i % 100 == 0:
                print(f"[ID] Processed {i}/{len(waters)}...")

    records.sort(key=lambda r: r['name'])
    print(f"[ID] Collected {len(records)} lakes.")
    return records
