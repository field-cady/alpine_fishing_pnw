"""Arkansas state scraper (Arkansas Game & Fish Commission).

Base: AGFC "WaterBodyList" lake-like waters (fname, acreage, centroid).
Species: AGFC has no general per-water species layer; only the Family &
Community Fishing Program locations expose stocked species (catfish/trout),
joined by name. So most waters have no species (documented gap).

Base: https://gisec2.agfc.com/arcgis/rest/services/Fisheries/WaterBodyList_Service/FeatureServer/0
FCFP: https://gisec2.agfc.com/arcgis/rest/services/Fisheries/FCFP_Locations/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Arkansas"
STATE_CODE = "ar"

_LAYER = "https://gisec2.agfc.com/arcgis/rest/services/Fisheries/WaterBodyList_Service/FeatureServer/0"
_FCFP = "https://gisec2.agfc.com/arcgis/rest/services/Fisheries/FCFP_Locations/FeatureServer/0"
_URL = "https://www.agfc.com/fishing/"


def _fcfp_species(limit=None):
    by = {}
    for feat in fetch_arcgis(_FCFP, out_fields="lake,catfish_tr", limit=limit, page_size=1000):
        p = feat.get("properties", {})
        name = (p.get("lake") or "").strip().lower()
        cat = (p.get("catfish_tr") or "").strip().lower()
        if not name:
            continue
        sp = set()
        if cat in ("catfish", "both"):
            sp.add("Channel Catfish")
        if cat in ("trout", "both"):
            sp.add("Rainbow Trout")
        if sp:
            by[name] = sp
    return by


def scrape(limit=None):
    print("[AR] Fetching AGFC community-fishing species...")
    fcfp = _fcfp_species(limit=limit)
    print(f"[AR] species for {len(fcfp)} community ponds. Fetching waterbodies...")
    features = fetch_arcgis(
        _LAYER, where="ftype IN ('Lake','Storage Reservoir','Fishing Pond')",
        out_fields="fname,gis_acres,acres,ftype", limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("fname") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("gis_acres") or p.get("acres")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=f"{round(float(acres), 1)} Acres" if acres else "Unknown",
            species=sorted(fcfp.get(name.lower(), set())), url=_URL,
            description=(p.get("ftype") or "").strip(),
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[AR] Collected {len(records)} waters ({withsp} with species).")
    return records
