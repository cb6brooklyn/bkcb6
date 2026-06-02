#!/usr/bin/env python3
"""Build the CB6 film permits feed from the live NYC Open Data Film Permits
dataset (tg4x-b46p), filtered to Brooklyn records whose community board list
includes 6.

Note: NYC deliberately delays publishing film permits by ~3 months for public
safety reasons (an agreement with City Council), so the most recent few months
will always be absent from the source data.

If a local CSV export is present it is used only as a fallback when the live
API is unreachable.
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / 'data' / 'cb6_film_permits.json'

API_URL = 'https://data.cityofnewyork.us/resource/tg4x-b46p.json'
SOURCE_PAGE = 'https://data.cityofnewyork.us/City-Government/Film-Permits/tg4x-b46p/about_data'
HEADERS = {'User-Agent': 'BKCB6 permits site updater/1.0 (public civic information feed builder)'}

# Optional manual fallback (used only if the live API fails AND the file exists).
FALLBACK_CSV = Path('/home/ubuntu/upload/Film_Permits_20260416.csv')


def parse_board_list(value) -> list:
    return [part.strip() for part in str(value or '').split(',') if part.strip()]


def parse_datetime_api(value: str) -> str:
    text = str(value or '').strip().replace('Z', '')
    if not text:
        return ''
    for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(text, fmt).isoformat()
        except ValueError:
            continue
    return text


def parse_datetime_csv(value: str) -> str:
    text = str(value or '').strip()
    if not text:
        return ''
    try:
        return datetime.strptime(text, '%m/%d/%Y %I:%M:%S %p').isoformat()
    except ValueError:
        return text


def keep_cb6(boards: list) -> bool:
    return '6' in boards


def clean_api_row(row: dict) -> dict:
    boards = parse_board_list(row.get('communityboard_s'))
    return {
        'event_id': str(row.get('eventid', '')).strip(),
        'event_type': str(row.get('eventtype', '')).strip(),
        'start_datetime': parse_datetime_api(row.get('startdatetime', '')),
        'end_datetime': parse_datetime_api(row.get('enddatetime', '')),
        'entered_on': parse_datetime_api(row.get('enteredon', '')),
        'event_agency': str(row.get('eventagency', '')).strip(),
        'parking_held': ' '.join(str(row.get('parkingheld', '')).split()),
        'borough': str(row.get('borough', '')).strip(),
        'community_boards': boards,
        'police_precincts': parse_board_list(row.get('policeprecinct_s')),
        'category': str(row.get('category', '')).strip(),
        'subcategory': str(row.get('subcategoryname', '')).strip(),
        'country': str(row.get('country', '')).strip(),
        'zip_codes': parse_board_list(row.get('zipcode_s')),
    }


def clean_csv_row(row: dict) -> dict:
    boards = parse_board_list(row.get('CommunityBoard(s)', ''))
    return {
        'event_id': str(row.get('EventID', '')).strip(),
        'event_type': str(row.get('EventType', '')).strip(),
        'start_datetime': parse_datetime_csv(row.get('StartDateTime', '')),
        'end_datetime': parse_datetime_csv(row.get('EndDateTime', '')),
        'entered_on': parse_datetime_csv(row.get('EnteredOn', '')),
        'event_agency': str(row.get('EventAgency', '')).strip(),
        'parking_held': ' '.join(str(row.get('ParkingHeld', '')).split()),
        'borough': str(row.get('Borough', '')).strip(),
        'community_boards': boards,
        'police_precincts': parse_board_list(row.get('PolicePrecinct(s)', '')),
        'category': str(row.get('Category', '')).strip(),
        'subcategory': str(row.get('SubCategoryName', '')).strip(),
        'country': str(row.get('Country', '')).strip(),
        'zip_codes': parse_board_list(row.get('ZipCode(s)', '')),
    }


def fetch_live() -> list:
    rows: list = []
    offset = 0
    page = 50000
    while True:
        params = {
            '$where': "upper(borough)='BROOKLYN'",
            '$limit': page,
            '$offset': offset,
            '$order': 'startdatetime DESC',
        }
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=120)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page:
            break
        offset += page
    cleaned = [clean_api_row(r) for r in rows]
    return [r for r in cleaned if keep_cb6(r['community_boards'])]


def fetch_fallback() -> list:
    if not FALLBACK_CSV.exists():
        return []
    rows: list = []
    with FALLBACK_CSV.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if str(row.get('Borough', '')).strip().lower() != 'brooklyn':
                continue
            if not keep_cb6(parse_board_list(row.get('CommunityBoard(s)', ''))):
                continue
            rows.append(clean_csv_row(row))
    return rows


def main() -> None:
    source = API_URL
    try:
        rows = fetch_live()
    except Exception as exc:
        print(f'Live film API failed ({exc}); attempting CSV fallback.')
        rows = fetch_fallback()
        source = str(FALLBACK_CSV) if rows else f'{API_URL} (no data; fallback unavailable)'

    rows.sort(key=lambda item: (item['start_datetime'], item['event_id']), reverse=True)
    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'source': 'NYC Open Data Film Permits (tg4x-b46p)',
        'source_url': SOURCE_PAGE,
        'source_file': source,
        'description': ('Brooklyn Community Board 6 film permits from the live NYC Open Data '
                        'Film Permits dataset, filtered to Brooklyn records whose community '
                        'board list includes 6. NYC delays publishing film permits by about '
                        'three months for public safety, so the most recent months are absent.'),
        'record_count': len(rows),
        'rows': rows,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(f'Wrote {len(rows)} rows to {OUT_PATH} (source: {source})')


if __name__ == '__main__':
    main()
