"""Pennsylvania state scraper (PA Fish & Boat Commission).

Source: PFBC Fisheries data hosted on PASDA, ArcGIS MapServer layer 19 (Lakes
Point). Point features with name, county and acreage for 465 PFBC-database
lakes. Species (stocked trout, warm/coolwater) live on companion layers and
are not joined here.

Layer: https://services.pasda.psu.edu/server/rest/services/pasda/PAFishBoat/MapServer/19
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Pennsylvania"
STATE_CODE = "pa"

_LAYER = "https://services.pasda.psu.edu/server/rest/services/pasda/PAFishBoat/MapServer/19"
_URL = "https://www.fishandboat.com/Fish/FishingBoating/Pages/default.aspx"


def scrape(limit=None):
    print("[PA] Fetching PFBC lakes (PASDA)...")
    features = fetch_arcgis(
        _LAYER, out_fields="WtrName,County,Latitude,Longitude,AreaAcres",
        limit=limit, page_size=1000,
    )
    print(f"[PA] {len(features)} lakes.")

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WtrName") or "").strip()
        if not name:
            continue
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("AreaAcres")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("County") or "").title() or None,
            area=f"{acres} Acres" if acres else "Unknown",
            url=_URL,
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[PA] Collected {len(records)} lakes.")
    return records
