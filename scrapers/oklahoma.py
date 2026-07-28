"""Oklahoma state scraper (OWRB + ODWC).

Base: OWRB "Lakes of Oklahoma" (name, area, elevation, coords). Species:
ODWC's "Where to Fish" per-lake pages list "Fish Species of Interest";
discovered from the paginated index and joined to lakes by normalized name.

Base:  https://owrb.csa.ou.edu/server/rest/services/Surface_Water/LOK_Lakes/MapServer/0
Pages: https://www.wildlifedepartment.com/fishing/wheretofish/<region>/<slug>
"""

import concurrent.futures
import re

import requests
from bs4 import BeautifulSoup

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Oklahoma"
STATE_CODE = "ok"

_LAYER = "https://owrb.csa.ou.edu/server/rest/services/Surface_Water/LOK_Lakes/MapServer/0"
_INDEX = "https://www.wildlifedepartment.com/fishing/wheretofish?page={}"
_BASE = "https://www.wildlifedepartment.com"
_HEADERS = {"User-Agent": "Mozilla/5.0"}
_URL = "https://www.wildlifedepartment.com/fishing"


def _norm(name):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\b(lake|reservoir|city)\b", " ", name.lower()))


def _discover_pages():
    """Return {normalized lake name: page url} from the paginated index."""
    pages = {}
    for pg in range(0, 12):
        try:
            html = requests.get(_INDEX.format(pg), headers=_HEADERS, timeout=30).text
        except Exception:
            break
        found = re.findall(r'href="(/fishing/wheretofish/(?:northeast|northwest|central|southeast|southwest|southcentral)/[a-z0-9\-]+)"', html)
        if not found:
            break
        for href in set(found):
            slug = href.rsplit("/", 1)[-1]
            pages[_norm(slug.replace("-", " "))] = _BASE + href
    return pages


def _page_species(url):
    try:
        html = requests.get(url, headers=_HEADERS, timeout=20).text
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return []
    out = []
    for div in soup.select("[class*='species-of-interest']"):
        for a in div.find_all("a"):
            t = a.get_text(strip=True)
            if not t:
                continue
            parts = [x.strip() for x in t.split(",")]
            # source is "Category, Type" (e.g. "Bass, Smallmouth" -> "Smallmouth Bass")
            out.append(f"{parts[1]} {parts[0]}" if len(parts) == 2 else t)
    return out


def scrape(limit=None):
    print("[OK] Discovering ODWC lake pages...")
    pages = _discover_pages()
    print(f"[OK] {len(pages)} ODWC lake pages. Fetching OWRB lakes...")
    features = fetch_arcgis(_LAYER, out_fields="name_full,norm_area,norm_elev", limit=limit, page_size=1000)

    lakes = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("name_full") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        lakes.append((name, lat, lon, p.get("norm_area"), p.get("norm_elev"), pages.get(_norm(name))))

    urls = sorted({l[5] for l in lakes if l[5]})
    species_by_url = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for url, sp in zip(urls, ex.map(_page_species, urls)):
            species_by_url[url] = sp

    records = []
    for name, lat, lon, acres, elev, url in lakes:
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            elevation=float(elev) if elev else None,
            area=f"{acres} Acres" if acres else "Unknown",
            species=sorted(set(species_by_url.get(url, []))), url=url or _URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[OK] Collected {len(records)} lakes ({withsp} with species).")
    return records
