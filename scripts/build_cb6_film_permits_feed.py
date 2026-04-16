#!/usr/bin/env python3
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = Path('/home/ubuntu/upload/Film_Permits_20260416.csv')
OUT_PATH = ROOT / 'data' / 'cb6_film_permits.json'


def parse_board_list(value: str) -> list[str]:
    return [part.strip() for part in str(value or '').split(',') if part.strip()]


def parse_datetime(value: str) -> str:
    text = str(value or '').strip()
    if not text:
        return ''
    dt = datetime.strptime(text, '%m/%d/%Y %I:%M:%S %p')
    return dt.isoformat()


def clean_row(row: dict) -> dict:
    start_iso = parse_datetime(row.get('StartDateTime', ''))
    end_iso = parse_datetime(row.get('EndDateTime', ''))
    entered_iso = parse_datetime(row.get('EnteredOn', ''))
    parking_held = ' '.join(str(row.get('ParkingHeld', '')).split())
    return {
        'event_id': str(row.get('EventID', '')).strip(),
        'event_type': str(row.get('EventType', '')).strip(),
        'start_datetime': start_iso,
        'end_datetime': end_iso,
        'entered_on': entered_iso,
        'event_agency': str(row.get('EventAgency', '')).strip(),
        'parking_held': parking_held,
        'borough': str(row.get('Borough', '')).strip(),
        'community_boards': parse_board_list(row.get('CommunityBoard(s)', '')),
        'police_precincts': parse_board_list(row.get('PolicePrecinct(s)', '')),
        'category': str(row.get('Category', '')).strip(),
        'subcategory': str(row.get('SubCategoryName', '')).strip(),
        'country': str(row.get('Country', '')).strip(),
        'zip_codes': parse_board_list(row.get('ZipCode(s)', '')),
    }


def load_rows() -> list[dict]:
    rows: list[dict] = []
    with SOURCE_CSV.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if str(row.get('Borough', '')).strip().lower() != 'brooklyn':
                continue
            boards = parse_board_list(row.get('CommunityBoard(s)', ''))
            if '6' not in boards:
                continue
            rows.append(clean_row(row))
    rows.sort(key=lambda item: (item['start_datetime'], item['event_id']), reverse=True)
    return rows


def main() -> None:
    rows = load_rows()
    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'source_file': str(SOURCE_CSV),
        'description': 'Brooklyn Community Board 6 film permits derived from the attached film permit CSV, filtered to Brooklyn records whose community board list includes 6.',
        'record_count': len(rows),
        'rows': rows,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(f'Wrote {len(rows)} rows to {OUT_PATH}')


if __name__ == '__main__':
    main()
