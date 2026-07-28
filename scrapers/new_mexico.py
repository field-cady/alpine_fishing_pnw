"""New Mexico state scraper (NM Dept of Game & Fish).

Source: NMDGF "Fishing Waters Map" ArcGIS FeatureServer, layer 5 (Fishing
Access). Species are numeric codes in Species1..Species6; the code->name lookup
lives in those fields' coded-value DOMAIN, which we read from the layer
metadata. Wadeable-stream access is dropped; access points dedupe per water.

Layer: https://services2.arcgis.com/CjbW1bVhK4dB3WOa/arcgis/rest/services/Fishing_Waters_Map/FeatureServer/5
"""

import requests

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "New Mexico"
STATE_CODE = "nm"

_LAYER = "https://services2.arcgis.com/CjbW1bVhK4dB3WOa/arcgis/rest/services/Fishing_Waters_Map/FeatureServer/5"
_URL = "https://www.wildlife.state.nm.us/fishing/"
_SPECIES_FIELDS = [f"Species{i}" for i in range(1, 7)]


def _code_lookup():
    """Read the coded-value domain shared by the Species fields."""
    meta = requests.get(_LAYER, params={"f": "json"}, timeout=30).json()
    for field in meta.get("fields", []):
        if field.get("name") in _SPECIES_FIELDS and field.get("domain"):
            cv = field["domain"].get("codedValues") or []
            return {str(c["code"]): c["name"] for c in cv}
    return {}


def scrape(limit=None):
    print("[NM] Reading NMDGF species code domain...")
    codes = _code_lookup()
    print(f"[NM] {len(codes)} species codes. Fetching fishing waters...")
    out_fields = "Waterbody_Name,Access_Type," + ",".join(_SPECIES_FIELDS)
    features = fetch_arcgis(_LAYER, out_fields=out_fields, limit=limit, page_size=1000)

    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Waterbody_Name") or "").strip()
        if not name:
            continue
        access = (p.get("Access_Type") or "").lower()
        if any(w in access for w in ("stream", "river", "creek")):
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        species = set()
        for fld in _SPECIES_FIELDS:
            code = p.get(fld)
            if code not in (None, "", " "):
                species.add(codes.get(str(code).strip(), None))
        species.discard(None)
        w = waters.get(name)
        if w is None:
            waters[name] = {"lat": lat, "lon": lon, "species": set(species)}
        else:
            w["species"] |= species

    records = [make_record(name=n, state=STATE_NAME, lat=w["lat"], lon=w["lon"],
                           species=sorted(w["species"]), url=_URL)
               for n, w in waters.items()]
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[NM] Collected {len(records)} waters ({withsp} with species).")
    return records
