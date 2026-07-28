"""Oregon state scraper (ODFW hike-in lakes).

ODFW publishes its hike-in lakes as Google My Maps embedded on a myodfw.com
article. This scraper discovers those maps, downloads their KML into
``data/oregon_kmls/`` (kept as a reproducible cache), then parses the
placemarks into normalized common-schema records.
"""

import glob
import os
import re
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from .base import make_record, clean_description, data_path

STATE_NAME = "Oregon"
STATE_CODE = "or"

_ARTICLE_URL = 'https://myodfw.com/articles/stocking-oregons-hike-lakes'
_KML_DIR = data_path("oregon_kmls")
_NS = {'kml': 'http://www.opengis.net/kml/2.2'}

# Lakes called out in the article prose but not present in the maps.
_EXPLICIT_LAKES = [
    {"name": "Hawk Lake", "description": "Wallowa Mountains"},
    {"name": "Veda Lake", "description": "Mt. Hood"},
    {"name": "Lake Legore", "description": "Eagle Cap Wilderness - Oregon's highest lake"},
]


def _discover_map_ids():
    response = requests.get(_ARTICLE_URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    map_ids = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'google.com/maps/d/viewer' in href or 'google.com/maps/d/u/' in href:
            match = re.search(r'mid=([^&]+)', href)
            if match:
                map_ids.append(match.group(1))
    return list(set(map_ids))


def _download_kmls(limit=None):
    """Download the ODFW map KMLs into the cache dir; returns the file paths."""
    map_ids = _discover_map_ids()
    if limit is not None:
        map_ids = map_ids[:limit]
    os.makedirs(_KML_DIR, exist_ok=True)
    print(f"[OR] Downloading {len(map_ids)} map region KML(s)...")
    paths = []
    for i, map_id in enumerate(map_ids, 1):
        kml_url = f"https://www.google.com/maps/d/kml?mid={map_id}&forcekml=1"
        try:
            r = requests.get(kml_url)
            path = os.path.join(_KML_DIR, f"region_{i}_{map_id}.kml")
            with open(path, 'wb') as f:
                f.write(r.content)
            paths.append(path)
        except Exception as e:
            print(f"[OR] Error downloading map {map_id}: {e}")
    return paths


def _extract_from_description(desc_text):
    """Pull species / area / elevation out of a raw placemark description."""
    species = []
    match = re.search(r'Fish species:?\s*([^\<]+)', desc_text, re.IGNORECASE)
    if match:
        species = [s.strip().title() for s in re.split(r',| and ', match.group(1)) if s.strip()]

    area = None
    for pat in (r'Size, acres:\s*([\d\.]+)', r'([\d\,\.]+)-acre', r'([\d\,\.]+) acres in size'):
        m = re.search(pat, desc_text, re.IGNORECASE)
        if m:
            area = m.group(1).replace(',', '')
            break

    elevation = None
    for pat in (r'Elevation \(ft\):\s*([\d\,\.]+)', r'elevation of ([\d\,\.]+)\s*(?:ft|feet)',
                r'elevation is ([\d\,\.]+)\s*(?:ft|feet)'):
        m = re.search(pat, desc_text, re.IGNORECASE)
        if m:
            elevation = float(m.group(1).replace(',', ''))
            break

    return species, area, elevation


def _parse_kml_files(paths):
    records = []
    seen_names = set()
    for path in paths:
        try:
            root = ET.parse(path).getroot()
        except Exception as e:
            print(f"[OR] Error parsing {path}: {e}")
            continue

        for placemark in root.findall('.//kml:Placemark', _NS):
            name_elem = placemark.find('kml:name', _NS)
            if name_elem is None or not name_elem.text:
                continue
            name = name_elem.text.strip()

            species, area, elevation, description = [], None, None, ""
            desc_elem = placemark.find('kml:description', _NS)
            if desc_elem is not None and desc_elem.text:
                raw = desc_elem.text.strip()
                species, area, elevation = _extract_from_description(raw)
                description = clean_description(raw)

            lat = lon = None
            point = placemark.find('.//kml:Point', _NS)
            if point is not None:
                coords_elem = point.find('kml:coordinates', _NS)
                if coords_elem is not None and coords_elem.text:
                    coords = coords_elem.text.strip().split(',')
                    if len(coords) >= 2:
                        lon = float(coords[0])
                        lat = float(coords[1])

            # ODFW maps only give us mappable lakes when coords are present.
            if lat is None or lon is None:
                continue

            seen_names.add(name)
            records.append(make_record(
                name=name,
                state=STATE_NAME,
                lat=lat,
                lon=lon,
                elevation=elevation,
                area=f"{area} Acres" if area else "Unknown",
                species=species,
                url=_ARTICLE_URL,
                description=description,
            ))
    return records, seen_names


def scrape(limit=None):
    """Scrape ODFW hike-in lakes and return normalized records.

    ``limit`` caps the number of map regions downloaded (used for smoke runs).
    """
    paths = _download_kmls(limit=limit)
    records, seen_names = _parse_kml_files(paths)

    # Fold in prose-only lakes we haven't already seen. They carry no
    # coordinates, so like the map lakes without a Point they won't render;
    # they're kept for completeness / future geocoding.
    for el in _EXPLICIT_LAKES:
        if el['name'] not in seen_names:
            records.append(make_record(
                name=el['name'],
                state=STATE_NAME,
                url=_ARTICLE_URL,
                description=el['description'],
            ))

    records.sort(key=lambda r: r['name'])
    print(f"[OR] Collected {len(records)} lakes.")
    return records
