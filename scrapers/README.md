# State scrapers — coverage & data sources

Each state is a module in this package exposing `STATE_NAME`, `STATE_CODE`, and
`scrape(limit=None)`, and is registered in `scrapers/__init__.py`. Running
`python scrape_all.py` writes `data/state_lakes_<code>.jsonl` for every
registered state; `python merge_data.py` concatenates them into
`data/all_states.json` (what the map loads).

All records share the common schema defined in `base.py`
(`name, state, lat, lon, elevation, area, county, species, url, description`).
Data availability varies wildly by state — see the notes below. Where a field
isn't available from a state's source it's left null / `"Unknown"` / empty.

## Source types (best → worst)

- **API / ArcGIS / open-data** — queryable, structured, re-runnable. Preferred.
- **KML / file download** — structured but static-ish.
- **HTML scrape** — brittle, parser-dependent.
- **None found** — no usable public source located; documented and skipped.

## Coverage

| State | Code | Source | Type | Notes |
|-------|------|--------|------|-------|
| Washington | wa | WDFW High Lakes listings | HTML | Alpine lakes >2500 ft; rich species + elevation + `starting`/`overabundant` flags. |
| Oregon | or | ODFW hike-in lakes (Google My Maps KML) | KML | Descriptions common; county absent; some prose-only lakes have no coords. |
| Idaho | id | IDFG Fishing Planner API (`body=3` high-mountain subset) | API | County present; no elevation. |
| California | ca | CDFW Planting Location (ds2897) ArcGIS FeatureServer | API | Stocked waters incl. some rivers; `FishType` is coarse ("Trout"/"Catfish"); no elevation/area. |
| Montana | mt | Montana FWP FishViewer stocking records (layer 38) | API | Stocked waters only; rich species; no county/elevation/area. A few (~3) events carry bad coordinates. |

_Last updated as states are added below._
