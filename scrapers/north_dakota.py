"""North Dakota state scraper (ND Game & Fish Department).

Source: NDGF "Fishing Waters" ArcGIS MapServer. Rich layer: name, native
lat/lon fields, county, full species names, acreage and current elevation.

Layer: https://ndgishub.nd.gov/arcgis/rest/services/Applications/GNF_FishingWaters/MapServer/0
"""

from .base import make_record, fetch_arcgis

STATE_NAME = "North Dakota"
STATE_CODE = "nd"

_LAYER = "https://ndgishub.nd.gov/arcgis/rest/services/Applications/GNF_FishingWaters/MapServer/0"
_URL = "https://gf.nd.gov/fishing"


def scrape(limit=None):
    print("[ND] Fetching NDGF fishing waters...")
    features = fetch_arcgis(
        _LAYER,
        out_fields="Lake_Name,latitude,longitude,County,SportfishLong,Acres,CurrentElevation",
        limit=limit, page_size=1000,
    )
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Lake_Name") or "").strip()
        lat, lon = p.get("latitude"), p.get("longitude")
        if not name or lat is None or lon is None:
            continue
        species = [s.strip() for s in (p.get("SportfishLong") or "").replace(";", ",").split(",") if s.strip()]
        county = (p.get("County") or "").strip()
        if county.lower() in ("", "not specified"):
            county = None
        acres = p.get("Acres")
        elev = p.get("CurrentElevation")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            elevation=float(elev) if elev else None,
            county=county.title() if county else None,
            area=f"{acres} Acres" if acres else "Unknown",
            species=species, url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[ND] Collected {len(records)} waters.")
    return records
