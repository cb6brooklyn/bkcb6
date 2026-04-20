#!/usr/bin/env python3
import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

import requests

ROOT = Path('/home/ubuntu/work/bkcb6_repo_1776697502')
SCHOOLS_HTML = ROOT / 'schools.html'
OUT_POINTS = ROOT / 'schools_childcare_cb6.json'
OUT_DISTRICTS = ROOT / 'school_districts_cb6.geojson'
CACHE_FILE = ROOT / 'scripts' / 'school_geocode_cache.json'

DISTRICT_URL = (
    'https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/ArcGIS/rest/services/'
    'NYC_School_Districts/FeatureServer/0/query'
    '?where=SchoolDist+in+(13,15,20)'
    '&outFields=SchoolDist'
    '&returnGeometry=true'
    '&f=geojson'
)

session = requests.Session()
session.headers.update({
    'User-Agent': 'bkcb6-map-repair/1.0 (contact: local build script)'
})


def extract_school_records(html_text: str):
    match = re.search(r'const\s+SCHOOLS\s*=\s*(\[.*?\])\s*;\s*const\s+TYPE_LABELS', html_text, re.S)
    if not match:
        raise RuntimeError('Could not find SCHOOLS array in schools.html')
    array_text = match.group(1)
    array_text = re.sub(r'^\s*//.*$', '', array_text, flags=re.M)
    array_text = re.sub(r'([\{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', array_text)
    array_text = re.sub(r',\s*([}\]])', r'\1', array_text)
    return json.loads(array_text)


def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2) + '\n')


def geocode(address: str, cache: dict):
    key = f'{address}, Brooklyn, NY'
    if key in cache:
        return cache[key]
    url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&addressdetails=1&q=' + quote_plus(key)
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    results = resp.json()
    value = None
    if results:
        top = results[0]
        value = {
            'lat': float(top['lat']),
            'lon': float(top['lon']),
            'display_name': top.get('display_name', '')
        }
    cache[key] = value
    save_cache(cache)
    time.sleep(1.05)
    return value


def classify(record):
    t = (record.get('t') or '').lower().strip()
    if t in {'prek', '3k', 'childcare', 'daycare'}:
        return 'childcare'
    return 'school'


def build_point_dataset(records):
    cache = load_cache()
    features = []
    for idx, record in enumerate(records, start=1):
        addr = (record.get('a') or '').strip()
        geo = geocode(addr, cache)
        if not geo:
            continue
        features.append({
            'id': idx,
            'name': record.get('n', '').strip(),
            'address': addr,
            'website': record.get('w', '').strip(),
            'category': classify(record),
            'program_type': (record.get('t') or '').strip(),
            'lat': geo['lat'],
            'lon': geo['lon'],
            'geocoded_as': geo.get('display_name', '')
        })
    OUT_POINTS.write_text(json.dumps(features, indent=2) + '\n')
    return len(features)


def build_district_dataset():
    resp = session.get(DISTRICT_URL, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    OUT_DISTRICTS.write_text(json.dumps(data, indent=2) + '\n')
    return len(data.get('features', []))


def main():
    html_text = SCHOOLS_HTML.read_text()
    records = extract_school_records(html_text)
    point_count = build_point_dataset(records)
    district_count = build_district_dataset()
    print(json.dumps({
        'source_records': len(records),
        'point_features_written': point_count,
        'district_features_written': district_count,
        'points_file': str(OUT_POINTS),
        'districts_file': str(OUT_DISTRICTS),
    }, indent=2))


if __name__ == '__main__':
    main()
