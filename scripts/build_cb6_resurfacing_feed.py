#!/usr/bin/env python3
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
FALLBACK_CSV = Path('/home/ubuntu/upload/CB6_Street_Resurfacing_Schedule_20260416.csv')
OUT_PATH = ROOT / 'data' / 'cb6_street_resurfacing.json'
CSV_URL = 'https://data.cityofnewyork.us/api/views/xnfm-u3k5/rows.csv?accessType=DOWNLOAD'
HEADERS = {'User-Agent': 'BKCB6 permits site updater/1.0 (public civic information feed builder)'}


def parse_date(value: str) -> str:
    text = str(value or '').strip()
    if not text:
        return ''
    return datetime.strptime(text, '%m/%d/%Y').date().isoformat()


def fetch_csv_rows() -> tuple[str, list[dict[str, str]]]:
    try:
        response = requests.get(CSV_URL, headers=HEADERS, timeout=120)
        response.raise_for_status()
        text = response.text
        source = CSV_URL
    except Exception:
        text = FALLBACK_CSV.read_text(encoding='utf-8-sig')
        source = str(FALLBACK_CSV)
    reader = csv.DictReader(io.StringIO(text))
    rows = [
        row for row in reader
        if str(row.get('Borough Name', '')).strip().upper() == 'BROOKLYN'
        and str(row.get('Community Board', '')).strip() == '306'
    ]
    rows.sort(key=lambda row: (row.get('Date', ''), row.get('On Street Name', ''), row.get('Work Schedule Project Location ID', '')), reverse=True)
    return source, rows


def clean_row(row: dict[str, str]) -> dict[str, Any]:
    iso_date = parse_date(row.get('Date', ''))
    on_street = str(row.get('On Street Name', '')).strip()
    from_street = str(row.get('From Street Name', '')).strip()
    to_street = str(row.get('To Street Name', '')).strip()
    address = on_street
    if on_street and from_street and to_street:
        address = f'{on_street} between {from_street} and {to_street}'
    elif on_street and from_street:
        address = f'{on_street} at {from_street}'
    elif not address:
        address = 'Street location not provided'
    return {
        'project_location_id': str(row.get('Work Schedule Project Location ID', '')).strip(),
        'borough_name': str(row.get('Borough Name', '')).strip(),
        'day': str(row.get('Day', '')).strip(),
        'date': iso_date,
        'on_street_name': on_street,
        'from_street_name': from_street,
        'to_street_name': to_street,
        'community_board': str(row.get('Community Board', '')).strip(),
        'area': str(row.get('Area', '')).strip(),
        'work_type': str(row.get('Work Type', '')).strip(),
        'crew_type': str(row.get('Crew Type', '')).strip(),
        'shift_type': str(row.get('Shift Type', '')).strip(),
        'oft_code': str(row.get('OFTCode', '')).strip(),
        'location_segment_id': str(row.get('Location Segment ID', '')).strip(),
        'location_wkt': str(row.get('Location WKT', '')).strip(),
        'location_node_id': str(row.get('Location Node ID', '')).strip(),
        'address': address,
    }


def main() -> None:
    source, rows = fetch_csv_rows()
    cleaned = [clean_row(row) for row in rows]
    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'source': 'Street Resurfacing Schedule',
        'source_url': 'https://data.cityofnewyork.us/Transportation/Street-Resurfacing-Schedule/xnfm-u3k5/about_data',
        'source_file': source,
        'description': 'Brooklyn Community Board 6 street resurfacing schedule rows filtered from the official NYC Open Data resurfacing dataset.',
        'record_count': len(cleaned),
        'rows': cleaned,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(f'Wrote {len(cleaned)} rows to {OUT_PATH}')


if __name__ == '__main__':
    main()
