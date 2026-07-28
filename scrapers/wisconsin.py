"""Wisconsin state scraper (Wisconsin DNR).

Base lakes come from the WDNR 24k Hydrography named-lakes layer (name, WBIC,
centroid, acreage). Species are attached from WDNR's Fish Stocking Summary API,
aggregated per waterbody name. NOTE: this only reflects DNR-STOCKED species
(walleye, muskellunge, trout, salmon, sturgeon, etc.) -- naturally reproducing
bass/panfish populations are not captured.

Lakes:    https://dnrmaps.wi.gov/arcgis2/rest/services/TS_AGOL_STAGING_SERVICES/EN_AGOL_STAGING_SurfaceWater_WTM/MapServer/1
Stocking: https://apps.dnr.wi.gov/fisheriesmanagement/Public/Summary/LoadResults
"""

import requests

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Wisconsin"
STATE_CODE = "wi"

_LAYER = "https://dnrmaps.wi.gov/arcgis2/rest/services/TS_AGOL_STAGING_SERVICES/EN_AGOL_STAGING_SurfaceWater_WTM/MapServer/1"
_STOCK = "https://apps.dnr.wi.gov/fisheriesmanagement/Public/Summary/LoadResults"
_URL = "https://dnr.wisconsin.gov/topic/Lakes"
_SQM_PER_ACRE = 4046.8564
_YEARS = range(2014, 2025)


def _stocking_species_by_name():
    """{UPPERCASE waterbody name -> set(species)} from the WDNR stocking API."""
    out = {}
    for year in _YEARS:
        try:
            r = requests.post(_STOCK, timeout=60, data={
                "draw": 1, "start": 0, "length": 20000,
                "STOCKING_YEAR": year, "SPECIES_NAME": "", "COUNTY_CODE": "",
                "STOCKED_WB_NAME": "", "LOCAL_WB_NAME": "",
            })
            rows = r.json().get("data", [])
        except Exception as e:
            print(f"[WI] stocking {year} failed: {e}")
            continue
        for row in rows:
            wb = (row.get("STOCKED_WB_NAME") or "").strip().upper()
            sp = (row.get("SPECIES_NAME") or "").strip()
            if wb and sp:
                out.setdefault(wb, set()).add(sp.title())
    return out


def scrape(limit=None):
    print("[WI] Fetching WDNR stocking species...")
    stock = _stocking_species_by_name()
    print(f"[WI] stocking species for {len(stock)} waters. Fetching lakes...")
    features = fetch_arcgis(
        _LAYER, where="HYDROTYPE=706 AND WATERBODY_NAME<>'Unnamed'",
        out_fields="WATERBODY_NAME,WATERBODY_WBIC,SHAPE.AREA", limit=limit, page_size=1000,
    )
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WATERBODY_NAME") or "").strip()
        if not name or name.lower() == "unnamed":
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        area_sqm = next((v for k, v in p.items() if "AREA" in k.upper() and v), None)
        area = f"{round(area_sqm / _SQM_PER_ACRE, 1)} Acres" if area_sqm else "Unknown"
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon, area=area,
            species=sorted(stock.get(name.upper(), set())), url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[WI] Collected {len(records)} lakes ({withsp} with stocked-species).")
    return records
