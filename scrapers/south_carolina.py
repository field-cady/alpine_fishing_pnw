"""South Carolina state scraper (SCDNR).

Source: SCDNR "Public Water Access" ArcGIS FeatureServer (points). Access
points are deduped per waterbody (lakes/ponds), unioning the per-access
SpeciesList. County present; no area/elevation.

Layer: https://services.arcgis.com/acgZYxoN5Oj8pDLa/arcgis/rest/services/South_Carolina_Public_Water_Access_PUBLIC_VIEW/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "South Carolina"
STATE_CODE = "sc"

_LAYER = "https://services.arcgis.com/acgZYxoN5Oj8pDLa/arcgis/rest/services/South_Carolina_Public_Water_Access_PUBLIC_VIEW/FeatureServer/0"
_URL = "https://www.dnr.sc.gov/fishing.html"


def scrape(limit=None):
    print("[SC] Fetching SCDNR public water access (lakes/ponds)...")
    features = fetch_arcgis(
        _LAYER,
        where="WaterbodyType IN ('Lake','Pond')",
        out_fields="Waterbody,Latitude,Longitude,County,SpeciesList",
        limit=limit, page_size=1000,
    )
    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Waterbody") or "").strip()
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if not name or lat is None:
            continue
        w = waters.get(name)
        if w is None:
            w = waters[name] = {"lat": lat, "lon": lon,
                                "county": p.get("County"), "species": set()}
        for s in (p.get("SpeciesList") or "").split(","):
            if s.strip():
                w["species"].add(s.strip())

    records = [make_record(
        name=name.title(), state=STATE_NAME, lat=w["lat"], lon=w["lon"],
        county=(w["county"] or "").title() or None,
        species=sorted(w["species"]), url=_URL,
    ) for name, w in waters.items()]
    records.sort(key=lambda r: r["name"])
    print(f"[SC] Collected {len(records)} waters.")
    return records
