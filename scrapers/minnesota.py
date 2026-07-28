"""Minnesota state scraper (Minnesota DNR).

Source: MN DNR "Lakes surveyed by MNDNR" ArcGIS FeatureServer (polygons) via
the MN Geospatial Commons. Gives name, county and acreage for 4,383 lakes.
Per-lake species are available from the DNR LakeFinder JSON API keyed by DOW
number, but that is 4k+ calls; species enrichment is left as a follow-up and
`species` is empty for now (see scrapers/README.md).

Layer: https://enterprise.gisdata.mn.gov/aghost/rest/services/us_mn_state_dnr/env_lakes_surveyed_by_mndnr/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Minnesota"
STATE_CODE = "mn"

_LAYER = "https://enterprise.gisdata.mn.gov/aghost/rest/services/us_mn_state_dnr/env_lakes_surveyed_by_mndnr/FeatureServer/0"
_URL = "https://www.dnr.state.mn.us/lakefind/index.html"


def scrape(limit=None):
    print("[MN] Fetching MN DNR surveyed lakes...")
    features = fetch_arcgis(
        _LAYER,
        out_fields="pw_basin_name,pw_parent_name,cty_name,acres,dowlknum",
        limit=limit, page_size=1000,
    )
    print(f"[MN] {len(features)} lakes.")

    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("pw_basin_name") or p.get("pw_parent_name") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("acres")
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            county=(p.get("cty_name") or "").title() or None,
            area=f"{round(acres, 1)} Acres" if acres else "Unknown",
            url=_URL,
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[MN] Collected {len(records)} lakes.")
    return records
