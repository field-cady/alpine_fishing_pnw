"""Michigan state scraper (Michigan DNR).

Source: Michigan DNR "IFR MI Lake Deep Points" ArcGIS FeatureServer -- a clean
one-row-per-lake point layer of 2,651 named inland lakes with county and
coordinates. Species are not available on this layer (the Fish Atlas layer
uses unjoinable water codes).

Layer: https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/DNRHydrologyOPENDATA/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Michigan"
STATE_CODE = "mi"

_LAYER = "https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/DNRHydrologyOPENDATA/FeatureServer/0"
_URL = "https://www.michigan.gov/dnr/things-to-do/fishing"


def scrape(limit=None):
    print("[MI] Fetching Michigan DNR inland lakes...")
    features = fetch_arcgis(_LAYER, out_fields="LakeName,County,Latitude,Longitude",
                            limit=limit, page_size=2000)
    print(f"[MI] {len(features)} lakes.")

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("LakeName") or "").strip()
        if not name:
            continue
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("County") or "").title() or None,
            url=_URL,
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[MI] Collected {len(records)} lakes.")
    return records
