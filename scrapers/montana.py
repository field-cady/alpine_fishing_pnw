"""Montana state scraper (Montana FWP).

Source: Montana Fish, Wildlife & Parks "FishViewer" ArcGIS MapServer, layer 38
(Fish Stocking Records). Each feature is a stocking event (point) with a
waterbody name and one species. We aggregate events per waterbody and union the
species. County / elevation / area are not available from this layer.

Layer: https://fwp-gis.mt.gov/arcgis/rest/services/fish/fishViewer/MapServer/38
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Montana"
STATE_CODE = "mt"

_LAYER = "https://fwp-gis.mt.gov/arcgis/rest/services/fish/fishViewer/MapServer/38"
_URL = "https://fwp.mt.gov/fish"


def scrape(limit=None):
    print("[MT] Fetching FWP fish stocking records (layer 38)...")
    features = fetch_arcgis(_LAYER, out_fields="WATERBODY,SPECIES",
                            limit=limit, page_size=2000)
    print(f"[MT] {len(features)} stocking events; aggregating by waterbody...")

    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WATERBODY") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        # Key on name + coarse location so distinct waters sharing a name stay
        # separate while repeated plantings of one water merge.
        key = (name, round(lat, 2), round(lon, 2))
        w = waters.get(key)
        if w is None:
            w = waters[key] = {"name": name, "lat": lat, "lon": lon, "species": set()}
        sp = (p.get("SPECIES") or "").strip()
        if sp:
            w["species"].add(sp)

    records = [make_record(
        name=w["name"], state=STATE_NAME, lat=w["lat"], lon=w["lon"],
        species=sorted(w["species"]), url=_URL,
    ) for w in waters.values()]

    records.sort(key=lambda r: r["name"])
    print(f"[MT] Collected {len(records)} distinct waters.")
    return records
