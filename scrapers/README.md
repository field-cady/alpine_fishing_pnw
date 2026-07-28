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
| Wisconsin | wi | WDNR 24k Hydro Waterbodies (ArcGIS) | API | Named lakes (HYDROTYPE 706), centroid + acreage; species on per-WBIC pages (not fetched); no county/elevation. |
| Michigan | mi | Michigan DNR IFR Lake Deep Points (ArcGIS) | API | Inland lakes with county + coordinates; no species/area/elevation. Great Lakes excluded. |
| New York | ny | NYSDEC Recommended Fishing Lakes & Ponds (data.ny.gov Socrata) | API | Curated ~320 waters with species, county, acreage, coordinates. Not exhaustive. |
| Pennsylvania | pa | PFBC lakes via PASDA (ArcGIS layer 19) | API | 465 PFBC-database lakes with county + acreage; species on companion trout layers (not joined); no elevation. |
| Georgia | ga | GADNR WRD Waterbodies (ArcGIS) | API | 110 named lakes/reservoirs with area; no species/county/elevation. |
| Illinois | il | IDNR Lake Depth & Capacity (ArcGIS) | API | Only ~43 bathymetry-surveyed lakes reliably queryable (full public-waters layer times out); area + normal-pool elevation; no species/county. |
| Indiana | in | IDNR Fish Access sites (ArcGIS, IndianaMap) | API | Access sites deduped per waterbody; free-text species + county present; no area/elevation. |
| Kentucky | ky | KDFWR Fishing Access Sites (ArcGIS) | API | 125 waterbodies (access sites deduped); no species/county/area (only on HTML detail pages). |
| Missouri | mo | MDC Fishing Interactive Map (ArcGIS) | API | MDC-managed waters with acreage; no species/county/elevation. |
| Ohio | oh | ODNR DOW Lakes bathymetry (ArcGIS) | API | 321 major lakes with acreage (polygon centroids); no species/county/elevation. |
| Tennessee | tn | TWRA Boating & Fishing Access Sites (ArcGIS) | API | Access sites deduped per water body; county present; no species/area/elevation. |
| Virginia | va | Virginia DWR Public Fishing Lakes (ArcGIS) | API | 193 DWR-managed lakes with precomputed centroids; no species/county/elevation. |

| Alabama | al | ADCNR Public Fishing Lakes (ArcGIS) | API | Only 20 state public fishing lakes; no species/county/area/elevation. |
| Arkansas | ar | AGFC WaterBodyList (ArcGIS) | API | Lake-like waters (filtered by ftype), polygon centroids + acreage; county is a numeric code (omitted); no species/elevation. |
| Florida | fl | FWC LAKES_POINTS (ArcGIS) | API | 3,859 named lakes with county (label points); no species/area/elevation. |
| Iowa | ia | Iowa DNR fishing reports (ArcGIS) | API | Fishing-report waterbodies, name + coords only; species on per-code report pages; no county/area/elevation. |
| Kansas | ks | KDWP Fishing Atlas (ArcGIS) | API | Reservoirs / state fishing lakes / community lakes with acreage; no species/county/elevation. |
| North Carolina | nc | NCWRC Public Fishing Areas (ArcGIS, NC OneMap) | API | Lentic waters (LAKE/POND) deduped; county present; no species/area/elevation. |
| Oklahoma | ok | OWRB Lakes of Oklahoma (ArcGIS) | API | 147 major lakes with area + normal-pool elevation; no species/county. |
| South Carolina | sc | SCDNR Public Water Access (ArcGIS) | API | Lakes/ponds deduped from access points; species (SpeciesList) + county present; no area/elevation. |
| Louisiana | la | LDWF Inland Waterbodies (ArcGIS) | API | Named lakes/reservoirs with popular species (free text) + parsed acreage; polygon centroids; no parish/elevation. |
| Nebraska | ne | NGPC Public Fishing Spots (ArcGIS) | API | Precomputed centroids, county, species (comma list) and acreage. |
| North Dakota | nd | NDGF Fishing Waters (ArcGIS) | API | Rich: full species names, county, acreage and current elevation. |
| South Dakota | sd | SDGFP Urban Community Fisheries (ArcGIS) | API | Only the urban/community subset (~76); species, county, acreage, outlet elevation. No statewide public API. |
| West Virginia | wv | WVDNR Public Fishing Lakes (WV GIS Tech Center) | API | Species from nine presence-flag columns; county + acreage; polygon centroids; no elevation. |
| Maine | me | Maine GIS PublicMasterWaters (ArcGIS) | API | 5,781 lentic waters with acreage; no species/county/elevation (species live in MDIFW surveys, not fetched). |
## No usable source found (documented gaps)

These states were researched but no machine-queryable public source was located.
They are intentionally not registered in `SCRAPERS`; revisit if a source appears.

| State | Code | What was tried |
|-------|------|----------------|
| Arizona | az | AZGFD publishes stocking only via a JS-driven "Fish & Boat AZ" web app and an HTML stocking schedule; no public FeatureServer/named-water API found. Options: capture the app's XHR API, or scrape + geocode the HTML schedule. |
