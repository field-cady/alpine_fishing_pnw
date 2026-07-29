"""New York state scraper (NYS DEC).

Source: NYSDEC "Recommended Fishing Lakes and Ponds" open dataset on
data.ny.gov (Socrata JSON API). ~320 curated waters, each with species list,
county, acreage and coordinates.

Endpoint: https://data.ny.gov/resource/mw8j-wduf.json
"""

from .base import make_record, fetch_socrata

STATE_NAME = "New York"
STATE_CODE = "ny"

_ENDPOINT = "https://data.ny.gov/resource/mw8j-wduf.json"
_URL = "https://www.dec.ny.gov/outdoor/fishing.html"


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def scrape(limit=None):
    print("[NY] Fetching NYSDEC recommended fishing lakes (Socrata)...")
    rows = fetch_socrata(_ENDPOINT, limit=limit)
    print(f"[NY] {len(rows)} waters.")

    records = []
    for r in rows:
        name = (r.get("water") or "").strip()
        lat = _to_float(r.get("point_y"))
        lon = _to_float(r.get("point_x"))
        if not name or lat is None or lon is None:
            continue
        # Species are separated by " - " in this dataset (sometimes commas).
        raw = (r.get("fish_speci") or "").replace(",", " - ")
        species = [s.strip() for s in raw.split(" - ") if s.strip()]
        acres = r.get("acres_mile")
        weblink = r.get("weblink")
        url = weblink.get("url") if isinstance(weblink, dict) and weblink.get("url") else _URL
        records.append(make_record(
            name=name, state=STATE_NAME, lat=lat, lon=lon,
            county=r.get("county"),
            area=f"{acres} Acres" if acres else "Unknown",
            species=species, url=url,
        ))

    records.sort(key=lambda r: r["name"])
    print(f"[NY] Collected {len(records)} waters.")
    return records
