"""California state scraper (CDFW).

Source: CDFW "Planting Location" open dataset (ds2897), served as an ArcGIS
REST FeatureServer. Each feature is a fish-planting event with a water name,
fish type, county and coordinates. We aggregate events per water body into one
record, collecting the set of fish types stocked there.

Layer: https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/biosds2897_fmu/FeatureServer/0
Portal: https://data.ca.gov/dataset/planting-location-cdfw-ds2897
"""

from .base import make_record, fetch_arcgis

STATE_NAME = "California"
STATE_CODE = "ca"

_LAYER = "https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/biosds2897_fmu/FeatureServer/0"
_PORTAL_URL = "https://nrm.dfg.ca.gov/FishPlants/"


def scrape(limit=None):
    """Scrape CDFW planting locations and return one record per water body."""
    print("[CA] Fetching CDFW planting locations (ds2897)...")
    features = fetch_arcgis(_LAYER, limit=limit)
    print(f"[CA] {len(features)} planting events; aggregating by water...")

    # Group planting events into one record per water body.
    waters = {}
    for feat in features:
        p = feat.get("properties", {})
        lat, lon = p.get("Lat"), p.get("Lon")
        if lat is None or lon is None:
            continue
        name = (p.get("WaterName") or "").strip()
        if not name:
            continue
        key = p.get("DfwWaterId") or name

        w = waters.get(key)
        if w is None:
            w = waters[key] = {
                "name": name,
                "lat": lat,
                "lon": lon,
                "county": p.get("Counties"),
                "species": set(),
                "last_plant": None,
            }
        fish = (p.get("FishType") or "").strip()
        if fish:
            w["species"].add(fish)
        week = p.get("WeekOfPlantStart")
        if week and (w["last_plant"] is None or week > w["last_plant"]):
            w["last_plant"] = week

    records = []
    for w in waters.values():
        description = f"Last stocked: {w['last_plant']}" if w["last_plant"] else ""
        records.append(make_record(
            name=w["name"],
            state=STATE_NAME,
            lat=w["lat"],
            lon=w["lon"],
            county=w["county"],
            species=sorted(w["species"]),
            url=_PORTAL_URL,
            description=description,
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[CA] Collected {len(records)} distinct waters.")
    return records
