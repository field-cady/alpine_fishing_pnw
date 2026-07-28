"""Washington state scraper (WDFW high lakes).

Scrapes the WDFW high-lakes listings at wdfw.wa.gov, then emits normalized
common-schema records. The ``starting`` / ``overabundant`` flags WDFW exposes
are preserved as extra fields on each record.
"""

import time

import requests
from bs4 import BeautifulSoup

from .base import make_record

STATE_NAME = "Washington"
STATE_CODE = "wa"

_ALL_URL = 'https://wdfw.wa.gov/fishing/locations/high-lakes?name=&county=All&species=&order=title&sort=asc&page='
_STARTING_URL = 'https://wdfw.wa.gov/fishing/locations/high-lakes/getting-started?name=&county=All&species=&order=title&sort=asc&page='
_OVERABUNDANT_URL = 'https://wdfw.wa.gov/fishing/locations/high-lakes/overabundant?name=&county=All&species=&order=title&sort=asc&page='

MIN_ELEVATION = 2500.0

SPECIES_MAP = {
    "21178": "Brook trout",
    "21419": "Brown bullhead",
    "21173": "Brown trout",
    "74140": "Cutthroat trout",
    "21184": "Golden trout",
    "21152": "Rainbow trout",
}


def _parse_table_from_page(txt):
    soup = BeautifulSoup(txt, features="lxml")
    tabulka = soup.find("table")
    if not tabulka:
        return []
    rows = []
    fields = ['name', 'area', 'elevation', 'county', 'location']
    tbody = tabulka.find('tbody')
    if not tbody:
        return []
    for row in tbody.findAll('tr'):
        col = row.findAll('td')
        if len(col) != 5:
            continue
        rows.append(dict(zip(fields, col)))
    return rows


def _html_to_row(r):
    """Parse a single table row into a raw dict (pre-normalization)."""
    try:
        name = r["name"].find("a").string.strip()
        # Append ' Lake' if it's missing a common descriptor
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
    all_rows = []
    while True:
        if max_pages is not None and i >= max_pages:
            break
        r = requests.get(url_base + str(i))
        parsed = _parse_table_from_page(r.text)
        rows = [row for row in (_html_to_row(rw) for rw in parsed if rw) if row]
        if not rows:
            break
        all_rows.extend(rows)
        i += 1
        time.sleep(0.3)  # Be nice to the server
    return all_rows


def scrape(limit=None):
    """Scrape WDFW high lakes and return normalized records.

    ``limit`` caps the number of listing pages fetched per query (used for
    smoke runs); ``None`` fetches everything.
    """
    print("[WA] Fetching all high lakes...")
    all_rows = _get_rows_from_all_pages(_ALL_URL, max_pages=limit)
    all_rows = [lk for lk in all_rows if lk['elevation'] > MIN_ELEVATION]

    print("[WA] Fetching overabundant lakes...")
    overabundant_urls = {lk['url'] for lk in _get_rows_from_all_pages(_OVERABUNDANT_URL, max_pages=limit)}

    print("[WA] Fetching starting lakes...")
    starting_urls = {lk['url'] for lk in _get_rows_from_all_pages(_STARTING_URL, max_pages=limit)}

    # url -> list of species names
    lake_species = {}
    for sp_id, sp_name in SPECIES_MAP.items():
        print(f"[WA] Fetching lakes with {sp_name}...")
        sp_url = f"https://wdfw.wa.gov/fishing/locations/high-lakes?name=&county=All&species={sp_id}&order=title&sort=asc&page="
        for lk in _get_rows_from_all_pages(sp_url, max_pages=limit):
            lake_species.setdefault(lk['url'], []).append(sp_name)

    records = []
    for lk in all_rows:
        records.append(make_record(
            name=lk['name'],
            state=STATE_NAME,
            lat=lk['lat'],
            lon=lk['lon'],
            elevation=lk['elevation'],
            area=lk['area'],
            county=lk['county'],
            species=lake_species.get(lk['url'], []),
            url=lk['url'],
            starting=lk['url'] in starting_urls,
            overabundant=lk['url'] in overabundant_urls,
        ))

    print(f"[WA] Collected {len(records)} lakes.")
    return records
