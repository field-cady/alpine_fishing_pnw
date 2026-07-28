"""South Dakota state scraper (SD Game, Fish & Parks).

Source: SDGFP "Urban Community Fisheries" ArcGIS FeatureServer (points). This
is only the urban/community-fisheries subset (no statewide fishable-lakes API
is public), but it carries name, county, species, acreage and elevation.

Layer: https://services.arcgis.com/jWPBXspaQsJStWX8/arcgis/rest/services/Urban_Community_Fisheries_-_Staff_Edits_view/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "South Dakota"
STATE_CODE = "sd"

_LAYER = "https://services.arcgis.com/jWPBXspaQsJStWX8/arcgis/rest/services/Urban_Community_Fisheries_-_Staff_Edits_view/FeatureServer/0"
_URL = "https://gfp.sd.gov/fishing/"


def scrape(limit=None):
    print("[SD] Fetching SDGFP urban community fisheries...")
    features = fetch_arcgis(
        _LAYER,
        out_fields="Name,Latitude,Longitude,County,Species,OtherSpecies,Acres,OutletElevation",
        limit=limit, page_size=1000,
    )
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("Name") or "").strip()
        lat, lon = p.get("Latitude"), p.get("Longitude")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if not name or lat is None:
            continue
        raw = ",".join(x for x in (p.get("Species"), p.get("OtherSpecies")) if x)
        species = [s.strip() for s in raw.split(",") if s.strip()]
        acres = p.get("Acres")
        elev = p.get("OutletElevation")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            elevation=float(elev) if elev else None,
            county=(p.get("County") or "").title() or None,
            area=f"{acres} Acres" if acres else "Unknown",
            species=species, url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[SD] Collected {len(records)} waters.")
    return records
