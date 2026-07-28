"""Shared helpers for the state scrapers.

This module defines the common lake record schema and the normalization
routines that used to live in ``merge_data.py``. Because normalization now
happens here, every ``state_lakes_<code>.jsonl`` file already uses the same
schema and ``merge_data.py`` can simply concatenate them.

Common record schema (one JSON object per line in the jsonl files)::

    {
        "name":        str,            # required
        "state":       str,            # e.g. "Washington"
        "lat":         float | None,
        "lon":         float | None,
        "elevation":   float | None,   # feet
        "area":        str,            # e.g. "12.0 Acres" or "Unknown"
        "county":      str | None,
        "species":     list[str],      # normalized, Title Case
        "url":         str,
        "description": str,            # optional, "" when unknown
        ...                            # states may add extra fields freely
    }
"""

import json
import os
import re

import requests

# Repo root is the parent of the scrapers/ package directory.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")


def data_path(*parts):
    """Return an absolute path inside the repo's data/ directory."""
    return os.path.join(DATA_DIR, *parts)


def make_record(name, state, lat=None, lon=None, elevation=None, area=None,
                county=None, species=None, url="", description="", **extra):
    """Build a lake record in the common schema.

    Species are normalized here so every state emits identical species names.
    ``area`` is coerced to a human-readable string. Extra keyword arguments are
    passed through unchanged so a state can attach its own fields.
    """
    record = {
        "name": name,
        "state": state,
        "lat": lat,
        "lon": lon,
        "elevation": elevation,
        "area": area if area else "Unknown",
        "county": county,
        "species": normalize_species(species or []),
        "url": url,
        "description": description or "",
    }
    record.update(extra)
    return record


def write_jsonl(path, records):
    """Write records to a jsonl file (one JSON object per line)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def fetch_arcgis(layer_url, where="1=1", out_fields="*", limit=None,
                 page_size=1000, timeout=60):
    """Page through an ArcGIS REST FeatureServer/MapServer layer.

    Returns a list of GeoJSON-style features (``{"properties": {...},
    "geometry": {...}}``). Many state fish & wildlife agencies publish their
    data as ArcGIS services, so this is the workhorse for those states.

    ``limit`` caps the number of features fetched (used for smoke runs).
    """
    query_url = layer_url.rstrip("/") + "/query"
    features = []
    offset = 0
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "f": "geojson",
            "returnGeometry": "true",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        }
        r = requests.get(query_url, params=params, timeout=timeout)
        data = r.json()
        batch = data.get("features", [])
        if not batch:
            break
        features.extend(batch)
        if limit is not None and len(features) >= limit:
            return features[:limit]
        if len(batch) < page_size:
            break
        offset += len(batch)
    return features


def geometry_centroid(geometry):
    """Return (lat, lon) for a GeoJSON geometry, or (None, None).

    Handles Point directly and averages the vertices of Polygon/LineString
    (and their Multi* variants) as a cheap centroid -- good enough to place a
    marker for a lake polygon.
    """
    if not geometry:
        return None, None
    gtype = geometry.get("type")
    coords = geometry.get("coordinates")
    if coords is None:
        return None, None

    pts = []

    def collect(c):
        # A coordinate pair is [lon, lat]; anything else is a nested list.
        if (isinstance(c, (list, tuple)) and len(c) >= 2
                and all(isinstance(x, (int, float)) for x in c[:2])):
            pts.append((c[0], c[1]))
        elif isinstance(c, (list, tuple)):
            for sub in c:
                collect(sub)

    if gtype == "Point":
        collect(coords)
    else:
        collect(coords)

    if not pts:
        return None, None
    lon = sum(p[0] for p in pts) / len(pts)
    lat = sum(p[1] for p in pts) / len(pts)
    return lat, lon


def normalize_species(species_list):
    """Normalize a messy list of species strings to canonical Title Case names.

    Moved verbatim (behavior-preserving) from the old ``merge_data.py`` so that
    Washington, Oregon and Idaho all produce identical species labels.
    """
    normalized = set()
    for s in species_list:
        # Lowercase for easier matching
        s = s.lower().strip()

        # Strip off anything after a period or open parenthesis
        s = s.split('.')[0]
        s = s.split('(')[0]
        s = s.strip()

        # Remove common prefixes/suffixes
        prefixes_to_remove = ['some ', 'stocked ', 'native ', 'the occasional ', 'surplus hatchery ']
        for p in prefixes_to_remove:
            if s.startswith(p):
                s = s[len(p):].strip()

        suffixes_to_remove = [' when available', ' m largemouth bass', ' largemouth bass', ' \xa0odfw']
        for suf in suffixes_to_remove:
            if s.endswith(suf):
                s = s[:-len(suf)].strip()

        if not s:
            continue

        # Map common variations to a standard name
        if s in ['rainbow', 'yellow trout', 'rainbow x']: s = 'rainbow trout'
        if s == 'brook': s = 'brook trout'
        if s in ['brown', 'brown trout.']: s = 'brown trout'
        if s in ['bullhead', 'bullhead ameiurus', 'bullhead catfish', 'brown bullhead catfish']: s = 'brown bullhead'
        if s == 'eastern brook': s = 'eastern brook trout'
        if 'steelhead' in s: s = 'steelhead'
        if s in ['coho', 'coho slamon']: s = 'coho salmon'
        if s in ['chinook', 'chinook slamon']: s = 'chinook salmon'
        if 'crappie pomoxis' in s: s = 'crappie'
        if 'cutbow' in s: s = 'cutthroat x rainbow trout'
        if s == 'cutthroat troutm': s = 'cutthroat trout'
        if 'bluegill lepomis' in s: s = 'bluegill'
        if 'pumpkinseed lepomis' in s or s == 'pumpkinseed sunfish': s = 'pumpkinseed'
        if 'burbot' in s: s = 'burbot'
        if 'goldfish' in s: s = 'goldfish'
        if 'kokanee oncorhynchus' in s: s = 'kokanee'
        if 'splake salvelinus' in s: s = 'splake'
        if 'tench tinca' in s: s = 'tench'
        if 'walleye stizostedion' in s: s = 'walleye'
        if 'warmouth lepomis' in s: s = 'warmouth'
        if 'cottus cottus' in s: s = 'sculpin'
        if 'catostomus sp' in s: s = 'sucker'
        if 'dace rhinichthys' in s: s = 'dace'
        if 'minnow cyprinus' in s: s = 'minnow'
        if 'prosopium sp' in s: s = 'whitefish'

        if 'bluegill / pumpkinseed / sunfish' in s:
            normalized.update(['Bluegill', 'Pumpkinseed', 'Sunfish'])
            continue

        # Ignore junk data
        junk = ['which provides picnic areas', 'except for w', 'are encouraged to release', 'other recreational amenities', 'restrooms on site', 'these lakes are considered', 'salmon and', 'hiking trails', 'to be caught', 'salamander', 'fry oncorhynchus']
        is_junk = False
        for j in junk:
            if j in s or 'http' in s:
                is_junk = True
                break

        if is_junk or len(s) < 3:
            continue

        normalized.add(s.title())

    return sorted(list(normalized))


def clean_description(desc):
    """Strip HTML and metadata lines from an ODFW placemark description.

    Moved verbatim from the old ``merge_data.py``; used by the Oregon scraper.
    """
    if not desc:
        return ""
    desc = re.sub(r'<img[^>]*>', '', desc, flags=re.IGNORECASE)

    lines = re.split(r'<br\s*/?>', desc, flags=re.IGNORECASE)
    clean_lines = []

    skip_prefixes = [
        'longitude', 'latitude', 'longitudedirection', 'latitudedirection',
        'stock interval', 'maximumdepth', 'maximum depth',
        'year stocked', 'elevation', 'acerage', 'size, acres', 'county',
        'species', 'fish species', 'stocking method', 'comments',
        'odfw recreation report', 'trout stocking schedule', 'stocking schedule'
    ]

    for line in lines:
        line = re.sub(r'<[^>]+>', '', line).strip()
        if not line:
            continue

        # Check if line matches a coordinate pattern like 43.60N 122.10W
        if re.match(r'^\d+\.\d+[NS]\s+\d+\.\d+[EW]$', line):
            continue

        is_skip = False
        for sp in skip_prefixes:
            if line.lower().startswith(sp):
                is_skip = True
                break
        if is_skip:
            continue

        clean_lines.append(line)

    return " ".join(clean_lines)
