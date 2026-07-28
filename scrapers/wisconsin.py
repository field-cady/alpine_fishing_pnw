"""Wisconsin state scraper (Wisconsin DNR).

Source: WDNR 24k Hydrography Waterbodies ArcGIS MapServer (polygons). We keep
named lakes (HYDROTYPE 706) and use the polygon centroid for coordinates and
Shape area for acreage. Species live on per-WBIC "Find A Lake" pages and are
not fetched here.

Layer: https://dnrmaps.wi.gov/arcgis2/rest/services/TS_AGOL_STAGING_SERVICES/EN_AGOL_STAGING_SurfaceWater_WTM/MapServer/1
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Wisconsin"
STATE_CODE = "wi"

_LAYER = "https://dnrmaps.wi.gov/arcgis2/rest/services/TS_AGOL_STAGING_SERVICES/EN_AGOL_STAGING_SurfaceWater_WTM/MapServer/1"
_URL = "https://dnr.wisconsin.gov/topic/Lakes"
_SQM_PER_ACRE = 4046.8564


def scrape(limit=None):
    print("[WI] Fetching WDNR named lakes (HYDROTYPE 706)...")
    features = fetch_arcgis(
        _LAYER,
        where="HYDROTYPE=706 AND WATERBODY_NAME<>'Unnamed'",
        out_fields="WATERBODY_NAME,WATERBODY_WBIC,SHAPE.AREA",
        limit=limit, page_size=1000,
    )
    print(f"[WI] {len(features)} named lake polygons.")

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("WATERBODY_NAME") or "").strip()
        if not name or name.lower() == "unnamed":
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        # The area field key varies (SHAPE.AREA / SHAPE_AREA); find any AREA key.
        area_sqm = next((v for k, v in p.items() if "AREA" in k.upper() and v), None)
        area = f"{round(area_sqm / _SQM_PER_ACRE, 1)} Acres" if area_sqm else "Unknown"
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=area, url=_URL,
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[WI] Collected {len(records)} lakes.")
    return records
