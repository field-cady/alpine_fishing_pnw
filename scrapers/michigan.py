"""Michigan state scraper (Michigan DNR).

Base lakes come from the DNR "IFR Lake Deep Points" layer (named inland lakes
with county + coordinates). Species are attached from the DNR "Fish Atlas"
layer (one point per species observation, pre-snapped per waterbody); we
aggregate the inland-lake ('inlk') observations onto a coarse coordinate grid
and match each lake to that grid. Species are thus best-effort by location.

Lakes:  https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/DNRHydrologyOPENDATA/FeatureServer/0
Atlas:  https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/DNRFisheriesDataOPENDATA/FeatureServer/0
"""

from .base import make_record, fetch_arcgis, geometry_centroid

STATE_NAME = "Michigan"
STATE_CODE = "mi"

_LAKES = "https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/DNRHydrologyOPENDATA/FeatureServer/0"
_ATLAS = "https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/DNRFisheriesDataOPENDATA/FeatureServer/0"
_URL = "https://www.michigan.gov/dnr/things-to-do/fishing"


def _species_grid(limit=None):
    """Aggregate inland-lake Fish Atlas species onto a ~1km coord grid."""
    grid = {}
    feats = fetch_arcgis(_ATLAS, where="Water='inlk'",
                         out_fields="CommonName", limit=limit, page_size=2000)
    for f in feats:
        name = (f.get("properties", {}).get("CommonName") or "").strip()
        if not name:
            continue
        lat, lon = geometry_centroid(f.get("geometry"))
        if lat is None:
            continue
        grid.setdefault((round(lat, 2), round(lon, 2)), set()).add(name)
    return grid


def _lookup(grid, lat, lon):
    species = set()
    la, lo = round(lat, 2), round(lon, 2)
    for dla in (-0.01, 0.0, 0.01):
        for dlo in (-0.01, 0.0, 0.01):
            species |= grid.get((round(la + dla, 2), round(lo + dlo, 2)), set())
    return species


def scrape(limit=None):
    print("[MI] Building Fish Atlas species grid...")
    grid = _species_grid(limit=limit)
    print(f"[MI] {len(grid)} species grid cells. Fetching lakes...")
    features = fetch_arcgis(_LAKES, out_fields="LakeName,County,Latitude,Longitude",
                            limit=limit, page_size=2000)

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
            species=sorted(_lookup(grid, lat, lon)), url=_URL,
        ))
    records.sort(key=lambda r: r["name"])
    withsp = sum(1 for r in records if r["species"])
    print(f"[MI] Collected {len(records)} lakes ({withsp} with species).")
    return records
