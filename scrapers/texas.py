"""Texas state scraper (TWDB reservoirs + TPWD species).

Base reservoirs come from the TWDB "Texas Reservoirs" polygon layer (name +
centroid). Species are scraped from TPWD's per-lake "where to fish" pages,
which list each reservoir's "Predominant Fish Species", and joined to the
reservoirs by normalized name.

Reservoirs: https://services3.arcgis.com/O0h7Kr4STkhD6uiU/arcgis/rest/services/Texas_Reservoirs/FeatureServer/0
TPWD lakes: https://tpwd.texas.gov/fishboat/fish/recreational/lakes/
"""

import re
import time

import requests
from bs4 import BeautifulSoup

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Texas"
STATE_CODE = "tx"

_LAYER = "https://services3.arcgis.com/O0h7Kr4STkhD6uiU/arcgis/rest/services/Texas_Reservoirs/FeatureServer/0"
_LAKELIST = "https://tpwd.texas.gov/fishboat/fish/recreational/lakes/lakelist.phtml"
_LAKEBASE = "https://tpwd.texas.gov/fishboat/fish/recreational/lakes/"
_URL = "https://tpwd.texas.gov/fishboat/fish/"


def _norm(name):
    n = name.lower()
    n = re.sub(r"\b(lake|reservoir|lk|res)\b", " ", n)
    return re.sub(r"[^a-z0-9]", "", n)


def _tpwd_species_by_name(limit=None):
    """Scrape TPWD lake pages -> {normalized reservoir name: set(species)}."""
    try:
        idx = requests.get(_LAKELIST, timeout=60).text
    except Exception as e:
        print(f"[TX] lake list failed: {e}")
        return {}
    # Lake links are bare relative slugs, e.g. href="conroe" or href="bois_darc/"
    slugs = sorted(set(re.findall(r'href="([a-z0-9_]+)/?"', idx)))
    slugs = [s for s in slugs if s not in ("index", "lakelist", "cfl")]
    if limit is not None:
        slugs = slugs[:limit]

    out = {}
    for slug in slugs:
        try:
            html = requests.get(_LAKEBASE + slug + "/", timeout=30).text
        except Exception:
            continue
        soup = BeautifulSoup(html, "lxml")
        # Take only the anchors under the "Predominant Fish Species" heading.
        head = soup.find(lambda t: t.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'strong', 'b')
                         and 'Predominant Fish Species' in t.get_text())
        species = []
        if head:
            ul = head.find_next("ul")
            if ul:
                species = [a.get_text(strip=True) for a in ul.find_all("a", href=True)
                           if "/huntwild/wild/species/" in a["href"] and a.get_text(strip=True)]
        title = soup.find(["h1", "h2"])
        name = title.get_text(strip=True) if title else slug
        if species:
            out.setdefault(_norm(name), set()).update(species)
            out.setdefault(_norm(slug), set()).update(species)
        time.sleep(0.15)
    return out


def scrape(limit=None):
    print("[TX] Scraping TPWD lake species...")
    species_by_name = _tpwd_species_by_name(limit=limit)
    print(f"[TX] species for {len(species_by_name)} TPWD lakes. Fetching reservoirs...")
    features = fetch_arcgis(_LAYER, out_fields="RES_NAME,TYPE", limit=limit, page_size=1000)

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("RES_NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        species = species_by_name.get(_norm(name), set())
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            species=sorted(species), url=_URL,
            description=(p.get("TYPE") or "").strip(),
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[TX] Collected {len(records)} reservoirs ({withsp} with species).")
    return records
