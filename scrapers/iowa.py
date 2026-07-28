"""Iowa state scraper (Iowa DNR).

Base: Iowa DNR "fishing reports" waterbodies (WATERBODYNAME, a `code` id,
coords). Species: each water's "Fish Iowa" lake-details page lists "Popular
Fish Species"; joined 1:1 by ``code``.

Base:  https://programs.iowadnr.gov/geospatial/rest/services/fisheries/fishingreports/MapServer/0
Pages: https://programs.iowadnr.gov/lakemanagement/fishiowa/LakeDetails/<code>
"""

import concurrent.futures
import re

import requests

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Iowa"
STATE_CODE = "ia"

_LAYER = "https://programs.iowadnr.gov/geospatial/rest/services/fisheries/fishingreports/MapServer/0"
_PAGE = "https://programs.iowadnr.gov/lakemanagement/fishiowa/LakeDetails/{}"
_HEADERS = {"User-Agent": "Mozilla/5.0"}
_SPECIES_RE = re.compile(r'fishspeciesdetail"><a[^>]*>([^<]+)</a>', re.IGNORECASE)


def _page_species(code):
    try:
        txt = requests.get(_PAGE.format(code), headers=_HEADERS, timeout=20).text
    except Exception:
        return code, []
    return code, [m.strip() for m in _SPECIES_RE.findall(txt) if m.strip()]


def scrape(limit=None):
    print("[IA] Fetching Iowa DNR waterbodies...")
    features = fetch_arcgis(_LAYER, out_fields="WATERBODYNAME,hydrographyName,code",
                            limit=limit, page_size=1000)
    rows = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WATERBODYNAME") or p.get("hydrographyName") or "").strip()
        code = (p.get("code") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        rows.append((name, lat, lon, code))

    codes = sorted({r[3] for r in rows if r[3]})
    print(f"[IA] scraping species for {len(codes)} lake pages...")
    species_by_code = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for code, sp in ex.map(lambda c: _page_species(c), codes):
            species_by_code[code] = sp

    records = [make_record(name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
                           species=sorted(set(species_by_code.get(code, []))), url=_PAGE.format(code) if code else "https://www.iowadnr.gov/things-to-do/fishing")
               for name, lat, lon, code in rows]
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[IA] Collected {len(records)} waters ({withsp} with species).")
    return records
