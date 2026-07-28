"""Kentucky state scraper (KDFWR).

Source: KDFWR "Fishing Access Sites" ArcGIS MapServer (points) on the Kentucky
Geoportal. Access sites are deduped to one record per waterbody. No species /
county / area in the layer (those live only on HTML detail pages).

Layer: https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Fish_Wildlife_WGS84WM/MapServer/2
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Kentucky"
STATE_CODE = "ky"

_LAYER = "https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Fish_Wildlife_WGS84WM/MapServer/2"
_URL = "https://fw.ky.gov/Fish/Pages/default.aspx"


def scrape(limit=None):
    print("[KY] Fetching KDFWR fishing-access sites...")
    features = fetch_arcgis(_LAYER, out_fields="WaterBody,Latitude,Longitude",
                            limit=limit, page_size=1000)
    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WaterBody") or "").strip()
        if not name or name in waters:
            continue
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        waters[name] = make_record(name=name.title(), state=STATE_NAME,
                                    lat=lat, lon=lon, url=_URL)
    records = sorted(waters.values(), key=lambda r: r["name"])
    print(f"[KY] Collected {len(records)} waters.")
    return records
