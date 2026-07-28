"""New Mexico state scraper (NM Dept of Game & Fish).

Source: NMDGF "Fishing Waters Map" ArcGIS FeatureServer, layer 5 (Fishing
Access). Point features with a waterbody name and species encoded as numeric
codes (Species1..Species6). No public code->name lookup was found, so species
are omitted rather than emitted as meaningless numbers. Access points are
deduped to one record per waterbody; wadeable-stream access is dropped.

Layer: https://services2.arcgis.com/CjbW1bVhK4dB3WOa/arcgis/rest/services/Fishing_Waters_Map/FeatureServer/5
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "New Mexico"
STATE_CODE = "nm"

_LAYER = "https://services2.arcgis.com/CjbW1bVhK4dB3WOa/arcgis/rest/services/Fishing_Waters_Map/FeatureServer/5"
_URL = "https://www.wildlife.state.nm.us/fishing/"


def scrape(limit=None):
    print("[NM] Fetching NMDGF fishing waters...")
    features = fetch_arcgis(_LAYER, out_fields="Waterbody_Name,Access_Type",
                            limit=limit, page_size=1000)
    print(f"[NM] {len(features)} access points.")

    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Waterbody_Name") or "").strip()
        if not name:
            continue
        access = (p.get("Access_Type") or "").lower()
        if any(w in access for w in ("stream", "river", "creek")):
            continue  # keep standing waters only
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None or name in waters:
            continue
        waters[name] = make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon, url=_URL,
        )

    records = sorted(waters.values(), key=lambda r: r["name"])
    print(f"[NM] Collected {len(records)} waters (species codes unmapped -> omitted).")
    return records
