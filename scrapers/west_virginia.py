"""West Virginia state scraper (WVDNR).

Source: WVDNR "Public Fishing Lakes" ArcGIS MapServer (polygons) via the WV GIS
Technical Center. Species are per-species presence flags (1/0) across nine
columns; centroid used for coordinates.

Layer: https://services.wvgis.wvu.edu/arcgis/rest/services/Applications/dnrRec_fishing/MapServer/7
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "West Virginia"
STATE_CODE = "wv"

_LAYER = "https://services.wvgis.wvu.edu/arcgis/rest/services/Applications/dnrRec_fishing/MapServer/7"
_URL = "https://wvdnr.gov/fishing/"

# boolean species columns -> common name
_SPECIES_COLS = {
    "Trout": "Trout", "LrgmthBass": "Largemouth Bass", "SmmthBass": "Smallmouth Bass",
    "StripBass": "Striped Bass", "WhtBass": "White Bass", "Walleye": "Walleye",
    "Musky": "Muskellunge", "Crappie": "Crappie", "ChanCatfish": "Channel Catfish",
}


def scrape(limit=None):
    print("[WV] Fetching WVDNR public fishing lakes...")
    out = "LakeName,County_1,GIS_Acres," + ",".join(_SPECIES_COLS)
    features = fetch_arcgis(_LAYER, out_fields=out, limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("LakeName") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        species = [common for col, common in _SPECIES_COLS.items()
                   if str(p.get(col)).strip() in ("1", "1.0")]
        acres = p.get("GIS_Acres")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("County_1") or "").title() or None,
            area=f"{round(acres, 1)} Acres" if acres else "Unknown",
            species=species, url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[WV] Collected {len(records)} lakes.")
    return records
