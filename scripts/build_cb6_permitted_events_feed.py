#!/usr/bin/env python3
import csv
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
FALLBACK_CSV = Path('/home/ubuntu/upload/CB6_Permitted_Events_20260416.csv')
OUT_PATH = ROOT / 'data' / 'cb6_permitted_events.json'
GEOCODE_CACHE_PATH = ROOT / 'data' / 'cb6_permitted_event_geocodes.json'
EVENTS_CSV_URL = 'https://data.cityofnewyork.us/api/views/tvpp-9vvx/rows.csv?accessType=DOWNLOAD'
PARKS_GEOJSON_URL = 'https://data.cityofnewyork.us/resource/c5vm-g2dk.geojson'
HEADERS = {'User-Agent': 'BKCB6 permits site updater/1.0 (public civic information feed builder)'}


def parse_list(value: str) -> list[str]:
    return [part.strip() for part in str(value or '').split(',') if part.strip()]


def parse_datetime(value: str) -> str:
    text = str(value or '').strip()
    if not text:
        return ''
    return datetime.strptime(text, '%m/%d/%Y %I:%M:%S %p').isoformat()


def normalize_board_token(value: str) -> str:
    token = str(value or '').strip().lstrip('0')
    return token or '0'


def is_cb6_event(row: dict[str, Any]) -> bool:
    if str(row.get('Event Borough', '')).strip().lower() != 'brooklyn':
        return False
    boards = {normalize_board_token(part) for part in parse_list(row.get('Community Board', ''))}
    return '6' in boards


def fetch_csv_rows() -> list[dict[str, str]]:
    try:
        response = requests.get(EVENTS_CSV_URL, headers=HEADERS, timeout=120)
        response.raise_for_status()
        text = response.text
        source = EVENTS_CSV_URL
    except Exception:
        text = FALLBACK_CSV.read_text(encoding='utf-8-sig')
        source = str(FALLBACK_CSV)
    reader = csv.DictReader(io.StringIO(text))
    rows = [row for row in reader if is_cb6_event(row)]
    rows.sort(key=lambda row: (row.get('Start Date/Time', ''), row.get('Event ID', '')), reverse=True)
    return source, rows


def load_geocode_cache() -> dict[str, dict[str, float]]:
    if not GEOCODE_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(GEOCODE_CACHE_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}


def save_geocode_cache(cache: dict[str, dict[str, float]]) -> None:
    GEOCODE_CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding='utf-8')


def fetch_parks_lookup() -> dict[str, dict[str, Any]]:
    params = {
        '$where': "borough='B' AND communityboard='306'",
        '$limit': 10000,
    }
    response = requests.get(f'{PARKS_GEOJSON_URL}?{urlencode(params)}', headers=HEADERS, timeout=120)
    response.raise_for_status()
    payload = response.json()
    lookup: dict[str, dict[str, Any]] = {}
    for feature in payload.get('features', []):
        props = feature.get('properties') or {}
        key = str(props.get('cemsid', '')).strip()
        geom = feature.get('geometry')
        if not key or not geom:
            continue
        try:
            centroid = shape(geom).centroid
            lookup[key] = {
                'geometry': geom,
                'lat': float(centroid.y),
                'lng': float(centroid.x),
                'name': str(props.get('name') or props.get('subpropertyname') or props.get('propertyname') or '').strip(),
            }
        except Exception:
            continue
    return lookup


def build_geocode_query(row: dict[str, Any]) -> str:
    parts = [
        str(row.get('Event Location', '')).strip(),
        str(row.get('Event Street Side', '')).strip(),
        'Brooklyn, New York',
    ]
    return ', '.join(part for part in parts if part)


def geocode_location(query: str, cache: dict[str, dict[str, float]]) -> dict[str, float]:
    if not query:
        return {}
    if query in cache:
        return cache[query]
    response = requests.get(
        'https://nominatim.openstreetmap.org/search',
        params={'q': query, 'format': 'jsonv2', 'limit': 1},
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    rows = response.json()
    if rows:
        hit = rows[0]
        result = {'lat': float(hit['lat']), 'lng': float(hit['lon'])}
        cache[query] = result
        time.sleep(1)
        return result
    cache[query] = {}
    time.sleep(1)
    return {}


def clean_row(row: dict[str, str], parks_lookup: dict[str, dict[str, Any]], geocode_cache: dict[str, dict[str, float]]) -> dict[str, Any]:
    cemsids = parse_list(row.get('CEMSID', ''))
    park_match = next((parks_lookup.get(cemsid) for cemsid in cemsids if cemsid in parks_lookup), None)
    geocode_query = ''
    lat = None
    lng = None
    geometry = None
    geometry_source = ''
    if park_match:
        lat = park_match['lat']
        lng = park_match['lng']
        geometry = park_match['geometry']
        geometry_source = 'parks-permit-areas'
    else:
        geocode_query = build_geocode_query(row)
        geocoded = geocode_location(geocode_query, geocode_cache) if geocode_query else {}
        lat = geocoded.get('lat')
        lng = geocoded.get('lng')
        geometry_source = 'nominatim' if geocoded else ''
    start_iso = parse_datetime(row.get('Start Date/Time', ''))
    end_iso = parse_datetime(row.get('End Date/Time', ''))
    location = str(row.get('Event Location', '')).strip()
    street_side = str(row.get('Event Street Side', '')).strip()
    address = ' — '.join(part for part in [location, street_side] if part) or 'Location not provided'
    return {
        'event_id': str(row.get('Event ID', '')).strip(),
        'event_name': str(row.get('Event Name', '')).strip(),
        'start_datetime': start_iso,
        'end_datetime': end_iso,
        'event_agency': str(row.get('Event Agency', '')).strip(),
        'event_type': str(row.get('Event Type', '')).strip(),
        'event_borough': str(row.get('Event Borough', '')).strip(),
        'event_location': location,
        'event_street_side': street_side,
        'street_closure_type': str(row.get('Street Closure Type', '')).strip(),
        'community_boards': parse_list(row.get('Community Board', '')),
        'police_precincts': parse_list(row.get('Police Precinct', '')),
        'cemsids': cemsids,
        'address': address,
        'lat': lat,
        'lng': lng,
        'geojson_geometry': geometry,
        'geometry_source': geometry_source,
        'geocode_query': geocode_query,
    }


def main() -> None:
    source, rows = fetch_csv_rows()
    parks_lookup = fetch_parks_lookup()
    geocode_cache = load_geocode_cache()
    cleaned = [clean_row(row, parks_lookup, geocode_cache) for row in rows]
    save_geocode_cache(geocode_cache)
    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'source': 'NYC Permitted Event Information',
        'source_url': 'https://data.cityofnewyork.us/City-Government/NYC-Permitted-Event-Information/tvpp-9vvx/about_data',
        'source_file': source,
        'description': 'Brooklyn Community Board 6 permitted events filtered from the official NYC Permitted Event Information dataset and mapped by CEMSID-linked park permit areas when available, with limited geocoding fallback for non-park locations.',
        'record_count': len(cleaned),
        'mapped_count': sum(1 for row in cleaned if isinstance(row.get('lat'), (int, float)) and isinstance(row.get('lng'), (int, float))),
        'rows': cleaned,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(f'Wrote {len(cleaned)} rows to {OUT_PATH}')


if __name__ == '__main__':
    main()
