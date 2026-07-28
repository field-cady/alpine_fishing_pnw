"""Colorado state scraper (Colorado Parks & Wildlife).

Source: CPW Colorado Fishing Atlas ArcGIS MapServer (Fishing locations, layer
3), hosted by CSU/NREL. Point features with a name, county, elevation and a
coarse stocking category. We keep only water bodies (not stream/river spots).

No per-species list is exposed by the REST layer, so ``species`` is left empty
and the stocking category is recorded in ``description``.

Layer: https://ndismaps.nrel.colostate.edu/arcgis/rest/services/FishingAtlas2025/FishingInfo2025/MapServer/3
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Colorado"
STATE_CODE = "co"

_LAYER = "https://ndismaps.nrel.colostate.edu/arcgis/rest/services/FishingAtlas2025/FishingInfo2025/MapServer/3"
_URL = "https://cpw.state.co.us/thingstodo/Pages/Fishing.aspx"


def scrape(limit=None):
    print("[CO] Fetching CPW Fishing Atlas water bodies...")
    features = fetch_arcgis(
        _LAYER,
        where="LOC_TYPE='Water Body'",
        out_fields="DOW_NAME,FA_NAME,FA_NAME2,ELEV_FT,COUNTYNAME,STOCKED,xval,yval",
        limit=limit, page_size=2000,
    )
    print(f"[CO] {len(features)} water bodies.")

    records = []
    for feat in features:
        p = feat.get("properties", {})
        # FA_NAME is sometimes a placeholder; fall back to DOW_NAME / FA_NAME2.
        name = ""
        for k in ("FA_NAME", "DOW_NAME", "FA_NAME2"):
            v = (p.get(k) or "").strip()
            if v and "purposely left blank" not in v.lower():
                name = v
                break
        if not name:
            continue

        lat, lon = p.get("yval"), p.get("xval")
        if lat is None or lon is None:
            lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue

        elev = p.get("ELEV_FT")
        stocked = (p.get("STOCKED") or "").strip()
        records.append(make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon,
            elevation=float(elev) if elev else None,
            county=p.get("COUNTYNAME"),
            species=[], url=_URL,
            description=f"Stocking: {stocked}" if stocked and stocked.lower() != "no" else "",
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[CO] Collected {len(records)} water bodies.")
    return records
