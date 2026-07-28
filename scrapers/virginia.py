"""Virginia state scraper (Virginia DWR).

Base lakes: VA DWR "Public Fishing Lakes" ArcGIS layer (NAME, XCenter/YCenter
centroids). Species: each lake's DWR "waterbody" web page lists broad species
categories (Bass, Catfish, Trout, Panfish, Crappie, Sunfish...) with a
present / best-bet / no status; we keep the present + best-bet ones. The page
slug is derived from the lake name.

Base:  https://services.dwr.virginia.gov/arcgis/rest/services/HUB_Layers/DWR_Public_Fishing_Lakes/FeatureServer/0
Pages: https://dwr.virginia.gov/waterbody/<slug>/
"""

import concurrent.futures
import re

import requests
from bs4 import BeautifulSoup

from .base import make_record, fetch_arcgis

STATE_NAME = "Virginia"
STATE_CODE = "va"

_LAYER = "https://services.dwr.virginia.gov/arcgis/rest/services/HUB_Layers/DWR_Public_Fishing_Lakes/FeatureServer/0"
_PAGE = "https://dwr.virginia.gov/waterbody/{}/"
_HEADERS = {"User-Agent": "Mozilla/5.0"}
_URL = "https://dwr.virginia.gov/fishing/"


def _slug(name):
    s = name.lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def _page_species(slug):
    try:
        r = requests.get(_PAGE.format(slug), headers=_HEADERS, timeout=20)
        if r.status_code != 200:
            return slug, []
        soup = BeautifulSoup(r.text, "lxml")
    except Exception:
        return slug, []
    species = []
    for icon in soup.select("[class*='fish-local-'][class*='-icon']"):
        cls = " ".join(icon.get("class") or [])
        if "present-icon" not in cls and "best-bet-icon" not in cls:
            continue  # skip 'no' rows and menu icon
        row = icon.find_parent(["li", "tr", "div"])
        if not row:
            continue
        # label is the text before the status glyph
        label = re.split(r"[✔★✘]", row.get_text(" ", strip=True))[0].strip()
        if label:
            species.append(label)
    return slug, species


def scrape(limit=None):
    print("[VA] Fetching Virginia DWR public fishing lakes...")
    features = fetch_arcgis(_LAYER, out_fields="NAME,XCenter,YCenter,Boat_Motor",
                            limit=limit, page_size=1000)
    lakes = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("NAME") or "").strip()
        lat, lon = p.get("YCenter"), p.get("XCenter")
        if name and lat is not None and lon is not None:
            lakes.append((name, lat, lon, _slug(name), (p.get("Boat_Motor") or "").strip()))

    print(f"[VA] scraping species for {len(lakes)} lake pages...")
    species_by_slug = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for slug, sp in ex.map(lambda l: _page_species(l[3]), lakes):
            species_by_slug[slug] = sp

    records = []
    for name, lat, lon, slug, boat in lakes:
        records.append(make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon,
            species=species_by_slug.get(slug, []), url=_PAGE.format(slug),
            description=boat,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[VA] Collected {len(records)} lakes ({withsp} with species).")
    return records
