"""Rhode Island state scraper (RI DEM / RIGIS).

Source: RIGIS "Lakes and Ponds 24K" ArcGIS FeatureServer (polygons). Named
waterbodies with acreage and a trout-stocked flag (recorded as Trout when set);
centroid used for coordinates. No elevation; county not cleanly available.

Layer: https://services2.arcgis.com/S8zZg9pg23JUEexQ/arcgis/rest/services/HYDRO_Lakes_and_Ponds_24K/FeatureServer/1
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Rhode Island"
STATE_CODE = "ri"

_LAYER = "https://services2.arcgis.com/S8zZg9pg23JUEexQ/arcgis/rest/services/HYDRO_Lakes_and_Ponds_24K/FeatureServer/1"
_URL = "https://dem.ri.gov/natural-resources-bureau/fish-wildlife/freshwater-fisheries"


def scrape(limit=None):
    print("[RI] Fetching RIGIS lakes and ponds...")
    features = fetch_arcgis(_LAYER, where="NAME IS NOT NULL AND NAME<>''",
                            out_fields="NAME,ACRES,Trout_Stk", limit=limit, page_size=2000)
    records = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("NAME") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(feat.get("geometry"))
        if lat is None:
            continue
        acres = p.get("ACRES")
        species = ["Trout"] if str(p.get("Trout_Stk")).strip().upper() in ("Y", "YES", "1") else []
        records.append(make_record(
            name=name.title(), state=STATE_NAME, lat=lat, lon=lon,
            area=f"{acres} Acres" if acres else "Unknown",
            species=species, url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    print(f"[RI] Collected {len(records)} waters.")
    return records
