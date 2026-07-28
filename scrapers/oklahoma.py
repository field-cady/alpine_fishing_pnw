"""Oklahoma state scraper (Oklahoma Water Resources Board).

Source: OWRB "Lakes of Oklahoma" ArcGIS MapServer (points), the official lake
gazetteer -- 147 major lakes with area and normal-pool elevation. No species/
county in the layer.

Layer: https://owrb.csa.ou.edu/server/rest/services/Surface_Water/LOK_Lakes/MapServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Oklahoma"
STATE_CODE = "ok"

_LAYER = "https://owrb.csa.ou.edu/server/rest/services/Surface_Water/LOK_Lakes/MapServer/0"
_URL = "https://www.wildlifedepartment.com/fishing"


def scrape(limit=None):
    print("[OK] Fetching OWRB lakes of Oklahoma...")
    features = fetch_arcgis(_LAYER, out_fields="name_full,norm_area,norm_elev",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("name_full") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("norm_area")
        elev = p.get("norm_elev")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            elevation=float(elev) if elev else None,
            area=f"{acres} Acres" if acres else "Unknown", url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[OK] Collected {len(records)} lakes.")
    return records
