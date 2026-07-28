"""Delaware state scraper (DNREC).

Source: Delaware FirstMap "DE_Public_Ponds" ArcGIS FeatureServer (points).
Layer 9 has the major fishing ponds (name, county, area); layer 10 has small
ponds with per-species presence flags. We merge both by name.

Service: https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Hydrology/DE_Public_Ponds/FeatureServer
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Delaware"
STATE_CODE = "de"

_SERVICE = "https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Hydrology/DE_Public_Ponds/FeatureServer"
_URL = "https://dnrec.alpha.delaware.gov/fish-wildlife/fishing/"

_SPECIES_COLS = {
    "LARGEBASS": "Largemouth Bass", "BLUEGILL": "Bluegill",
    "BLCCRAPPIE": "Black Crappie", "CHAINPICK": "Chain Pickerel",
    "CHANCATFISH": "Channel Catfish", "TROUT": "Trout",
}


def scrape(limit=None):
    print("[DE] Fetching Delaware public ponds...")
    waters = {}

    # Layer 9: major ponds (name/county/area)
    for feat in fetch_arcgis(_SERVICE + "/9", out_fields="POND,COUNTY,SURFAREA",
                             limit=limit, page_size=1000):
        p = feat.get("properties", {})
        name = (p.get("POND") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("SURFAREA")
        waters[name.lower()] = make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("COUNTY") or "").title() or None,
            area=f"{acres} Acres" if acres else "Unknown", url=_URL,
        )

    # Layer 10: small ponds with species flags
    out = "GNIS_NAME,ACRES," + ",".join(_SPECIES_COLS)
    for feat in fetch_arcgis(_SERVICE + "/10", out_fields=out, limit=limit, page_size=1000):
        p = feat.get("properties", {})
        name = (p.get("GNIS_NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        species = [common for col, common in _SPECIES_COLS.items()
                   if str(p.get(col)).strip().lower() in ("yes", "y", "1")]
        acres = p.get("ACRES")
        rec = make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=f"{acres} Acres" if acres else "Unknown",
            species=species, url=_URL,
        )
        waters[name.lower()] = rec  # prefer the species-bearing record

    records = sorted(waters.values(), key=lambda r: r["name"])
    print(f"[DE] Collected {len(records)} ponds.")
    return records
