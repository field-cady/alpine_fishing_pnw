"""Utah state scraper (Utah Division of Wildlife Resources).

Source: UDWR "Fish Stocking Events 1979-2024" ArcGIS FeatureServer.
Layer 0 ("UDWR Lakes") holds the named waters with coordinates; a related
table (layer 2) holds stocking events with species. We read the waters from
layer 0 and attach species by joining the distinct (water id, species) pairs
from the table on ``DWR_WATER_ID``. Streams live in a separate layer.

Service: https://services.arcgis.com/ZzrwjTRez6FJiOq4/arcgis/rest/services/UDWR_Fish_Stocking_Events_1979_2024_VIEW/FeatureServer
"""

import requests

from .base import make_record, fetch_arcgis

STATE_NAME = "Utah"
STATE_CODE = "ut"

_SERVICE = "https://services.arcgis.com/ZzrwjTRez6FJiOq4/arcgis/rest/services/UDWR_Fish_Stocking_Events_1979_2024_VIEW/FeatureServer"
_LAKES = _SERVICE + "/0"
_STOCK_TABLE = _SERVICE + "/2"
_URL = "https://dwrapps.utah.gov/dwr/fishstocking"


def _species_by_water():
    """Return {DWR_WATER_ID: set(species)} from the stocking table."""
    mapping = {}
    offset = 0
    while True:
        params = {
            "where": "1=1",
            "outFields": "DWR_WATER_ID,COMMMON_NAME",
            "returnDistinctValues": "true",
            "returnGeometry": "false",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": 2000,
        }
        r = requests.get(_STOCK_TABLE + "/query", params=params, timeout=60)
        feats = r.json().get("features", [])
        if not feats:
            break
        for f in feats:
            a = f.get("attributes", {})
            wid = a.get("DWR_WATER_ID")
            sp = (a.get("COMMMON_NAME") or "").strip()
            if wid and sp:
                mapping.setdefault(wid, set()).add(sp)
        if len(feats) < 2000:
            break
        offset += len(feats)
    return mapping


def scrape(limit=None):
    print("[UT] Fetching UDWR species-by-water table...")
    species_map = _species_by_water()
    print(f"[UT] Species for {len(species_map)} waters. Fetching lakes...")

    features = fetch_arcgis(
        _LAKES,
        out_fields="WaterName,Lat_Y,Long_X,DWR_WATER_ID,Stocked_YN",
        limit=limit, page_size=2000,
    )
    print(f"[UT] {len(features)} lake features.")

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WaterName") or "").strip()
        lat, lon = p.get("Lat_Y"), p.get("Long_X")
        if not name or not lat or not lon:
            continue
        wid = p.get("DWR_WATER_ID")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            species=sorted(species_map.get(wid, set())), url=_URL,
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[UT] Collected {len(records)} lakes.")
    return records
