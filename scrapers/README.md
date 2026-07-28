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
| Wyoming | wy | WGFD Fishing Guide "Lakes" ArcGIS FeatureServer | API | Lakes/reservoirs only; species from `GameFishPresent`; area present; elevation sparse (~9%); no county. Centroid of polygon used for lat/lon. |
| Colorado | co | CPW Fishing Atlas ArcGIS MapServer (Fishing locations) | API | Water bodies only (streams filtered out); county + elevation present; **no species list** exposed (only a stocking category, kept in `description`). |
| Utah | ut | UDWR Fish Stocking Events ArcGIS FeatureServer (lakes layer + species table) | API | Lakes only; species joined from related stocking table by water id; no county/elevation/area. |
| Nevada | nv | NDOW Fishable Waters ArcGIS FeatureServer (lakes layer) | API | Lakes/reservoirs only; species decoded from FISH1..FISH11 abbreviation codes (a few uncommon codes may pass through unmapped); county present; no elevation/area. |

| New Mexico | nm | NMDGF Fishing Waters Map (ArcGIS layer 5) | API | Standing waters only (streams dropped), deduped to one per waterbody; species are numeric codes with no public lookup, so omitted; no county/elevation/area. |

| Texas | tx | TWDB Texas Reservoirs (ArcGIS) | API | Reservoir names + polygon centroids only; no species/county/elevation (TPWD stocking is HTML-only). |

| Minnesota | mn | MN DNR surveyed lakes (ArcGIS, MN Geospatial Commons) | API | Name, county, acreage for 4,383 lakes; per-lake species available via DNR LakeFinder API (4k+ calls) — deferred, species empty for now. |

_Last updated as states are added below._
