"""North Carolina state scraper (NC Wildlife Resources Commission).

Source: NCWRC "Public Fishing Areas" ArcGIS FeatureServer (points) via NC
OneMap. We keep lentic waters (LAKE/POND), deduped by area name; county
present, no species/area/elevation.

Layer: https://services1.arcgis.com/YfqBAUM5nWR3yhGP/arcgis/rest/services/NCWRC_Public_Fishing_Areas_view/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "North Carolina"
STATE_CODE = "nc"

_LAYER = "https://services1.arcgis.com/YfqBAUM5nWR3yhGP/arcgis/rest/services/NCWRC_Public_Fishing_Areas_view/FeatureServer/0"
_URL = "https://www.ncwildlife.org/fishing"


def scrape(limit=None):
    print("[NC] Fetching NCWRC public fishing areas (lakes/ponds)...")
    features = fetch_arcgis(
        _LAYER,
        where="Waterbody_Type IN ('LAKE','POND')",
        out_fields="PFA_Name,Latitude,Longitude,County,Waterbody_Type",
        limit=limit, page_size=1000,
    )
    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("PFA_Name") or "").strip()
        if not name or name in waters:
            continue
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        waters[name] = make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("County") or "").title() or None, url=_URL,
            description=(p.get("Waterbody_Type") or "").title(),
        )
    records = sorted(waters.values(), key=lambda r: r["name"])
    print(f"[NC] Collected {len(records)} waters.")
    return records
