"""Maryland state scraper (Maryland DNR / iMAP).

Source: Maryland iMAP "MD_Waterbodies" ArcGIS FeatureServer, layer 3 (Lakes -
Detailed). Named lakes with county and acreage; centroid used for coordinates.
No species/elevation.

Layer: https://mdgeodata.md.gov/imap/rest/services/Hydrology/MD_Waterbodies/FeatureServer/3
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Maryland"
STATE_CODE = "md"

_LAYER = "https://mdgeodata.md.gov/imap/rest/services/Hydrology/MD_Waterbodies/FeatureServer/3"
_URL = "https://dnr.maryland.gov/fisheries/pages/index.aspx"


def scrape(limit=None):
    print("[MD] Fetching Maryland lakes...")
    features = fetch_arcgis(_LAYER, where="LAKENAME<>''",
                            out_fields="LAKENAME,COUNTY,ACRES",
                            limit=limit, page_size=1000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("LAKENAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("ACRES")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("COUNTY") or "").title() or None,
            area=f"{round(acres, 1)} Acres" if acres else "Unknown", url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[MD] Collected {len(records)} lakes.")
    return records
