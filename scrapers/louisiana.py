"""Louisiana state scraper (LA Dept of Wildlife & Fisheries).

Source: LDWF "Inland Waterbodies with Management Plans" ArcGIS FeatureServer
(polygons). Name, popular species (free text) and a free-text size string;
centroid used for coordinates.

Layer: https://services1.arcgis.com/6euNCaGPCgCzgAVF/arcgis/rest/services/Inland_Waterbodies_with_Management_Plans04152024/FeatureServer/0
"""

import re

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Louisiana"
STATE_CODE = "la"

_LAYER = "https://services1.arcgis.com/6euNCaGPCgCzgAVF/arcgis/rest/services/Inland_Waterbodies_with_Management_Plans04152024/FeatureServer/0"
_URL = "https://www.wlf.louisiana.gov/page/freshwater-fishing"


def _parse_species(text):
    if not text:
        return []
    parts = re.split(r"[;,]| and ", text)
    return [p.strip() for p in parts if p.strip()]


def _parse_acres(size):
    if size and "acre" in size.lower():
        m = re.search(r"([\d,]+(?:\.\d+)?)\s*acre", size, re.IGNORECASE)
        if m:
            return f"{m.group(1).replace(',', '')} Acres"
    return "Unknown"


def scrape(limit=None):
    print("[LA] Fetching LDWF inland waterbodies...")
    features = fetch_arcgis(_LAYER, out_fields="Name,Popular_Sp,Size",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Name") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=_parse_acres(p.get("Size")),
            species=_parse_species(p.get("Popular_Sp")), url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[LA] Collected {len(records)} waters.")
    return records
