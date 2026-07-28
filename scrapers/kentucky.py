"""Kentucky state scraper (KDFWR).

Base: KDFWR "Fishing Access Sites" ArcGIS (WaterBody, WID, coords), deduped per
waterbody. Species: each water's KDFWR detail page lists regulated species in a
table; joined by WID.

Base:  https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Fish_Wildlife_WGS84WM/MapServer/2
Pages: https://app.fw.ky.gov/fisheries/waterbodydetail.aspx?wid=<WID>
"""

import concurrent.futures

import requests
from bs4 import BeautifulSoup

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Kentucky"
STATE_CODE = "ky"

_LAYER = "https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Fish_Wildlife_WGS84WM/MapServer/2"
_PAGE = "https://app.fw.ky.gov/fisheries/waterbodydetail.aspx?wid={}"
_HEADERS = {"User-Agent": "Mozilla/5.0"}
_URL = "https://fw.ky.gov/Fish/Pages/default.aspx"


def _wid_species(wid):
    try:
        html = requests.get(_PAGE.format(wid), headers=_HEADERS, timeout=20).text
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return wid, []
    species = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        first = cells[0].get_text(strip=True)
        # species rows are ALL-CAPS common names in the first cell
        if first and first.isupper() and 2 < len(first) < 40 and any(c.isalpha() for c in first):
            species.append(first.title())
    return wid, species


def scrape(limit=None):
    print("[KY] Fetching KDFWR access sites...")
    features = fetch_arcgis(_LAYER, out_fields="WaterBody,WID,Latitude,Longitude",
                            limit=limit, page_size=1000)
    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WaterBody") or "").strip()
        if not name or name in waters:
            continue
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        waters[name] = {"lat": lat, "lon": lon, "wid": p.get("WID")}

    wids = sorted({w["wid"] for w in waters.values() if w["wid"] is not None},
                  key=lambda x: str(x))
    print(f"[KY] scraping species for {len(wids)} waterbody pages...")
    species_by_wid = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        for wid, sp in ex.map(lambda w: _wid_species(w), wids):
            species_by_wid[wid] = sp

    records = [make_record(name=name.title(), state=STATE_NAME, lat=w["lat"], lon=w["lon"],
                           species=sorted(set(species_by_wid.get(w["wid"], []))), url=_URL)
               for name, w in waters.items()]
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[KY] Collected {len(records)} waters ({withsp} with species).")
    return records
