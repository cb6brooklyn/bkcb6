#!/usr/bin/env python3
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
from shapely import wkt

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_PATH = ROOT / 'data' / 'cb6_boundary.geojson'
OUT_PATH = ROOT / 'data' / 'cb6_dot_recent.json'
URL = 'https://nycstreets.net/Public/Permits/PermitSearchMobile/'
OPEN_DATA_URL = 'https://data.cityofnewyork.us/resource/tqtj-sjs8.json'
today = datetime.now(timezone.utc).date()
WINDOW_START = (today - timedelta(days=90)).isoformat()
WINDOW_END   = (today + timedelta(days=180)).isoformat()

DATE_RE = re.compile(r'/Date\((\d+)\)/')
KEEP_KEYS = {
    'PermitNumber', 'PermitteeName', 'PermitTypeDesc', 'PermitPurpose', 'PermitHouseNumber',
    'OnStreetName', 'FromStreetName', 'ToStreetName', 'BoroughName', 'SpecificLocation',
    'Status', 'IsPDFExists', 'Wkt', 'IssuedWorkStartDate', 'IssuedWorkEndDate', 'PermitIssueDateFrom'
}


def load_boundary_wgs84():
    data = json.loads(BOUNDARY_PATH.read_text())
    feature = data['features'][0] if isinstance(data, dict) and 'features' in data else data
    return shape(feature['geometry'])


def boundary_extent_wkt(boundary_wgs84) -> str:
    transformer = Transformer.from_crs('EPSG:4326', 'EPSG:2263', always_xy=True)
    boundary_2263 = transform(transformer.transform, boundary_wgs84)
    xmin, ymin, xmax, ymax = boundary_2263.bounds
    return (
        'POLYGON((' 
        f'{xmin} {ymin}, {xmax} {ymin}, {xmax} {ymax}, {xmin} {ymax}, {xmin} {ymin}'
        '))'
    )


def parse_date(value: str) -> str:
    match = DATE_RE.fullmatch(str(value or '').strip())
    if not match:
        return ''
    ts = int(match.group(1)) / 1000
    return datetime.fromtimestamp(ts, timezone.utc).date().isoformat()


def clean_text(value):
    if value is None:
        return ''
    return str(value).strip()


def keep_row(row: dict, boundary_wgs84) -> bool:
    raw_wkt = row.get('Wkt')
    if not raw_wkt:
        return False
    try:
        geom_2263 = wkt.loads(raw_wkt)
    except Exception:
        return False
    transformer = Transformer.from_crs('EPSG:2263', 'EPSG:4326', always_xy=True)
    geom_wgs84 = transform(transformer.transform, geom_2263)
    return geom_wgs84.intersects(boundary_wgs84)


def clean_row(row: dict) -> dict:
    kept = {k: clean_text(row.get(k)) if k != 'IsPDFExists' else bool(row.get(k)) for k in KEEP_KEYS}
    kept['permitissuedate'] = parse_date(row.get('PermitIssueDateFrom'))
    kept['permitnumber'] = kept.pop('PermitNumber')
    kept['permitteename'] = kept.pop('PermitteeName')
    kept['permittypedesc'] = kept.pop('PermitTypeDesc')
    kept['permitpurposecomments'] = kept.pop('PermitPurpose')
    kept['permithousenumber'] = kept.pop('PermitHouseNumber')
    kept['onstreetname'] = kept.pop('OnStreetName')
    kept['fromstreetname'] = kept.pop('FromStreetName')
    kept['tostreetname'] = kept.pop('ToStreetName')
    kept['boroughname'] = kept.pop('BoroughName')
    kept['permitlocationcomments'] = kept.pop('SpecificLocation')
    kept['permitstatusshortdesc'] = kept.pop('Status')
    kept['wkt'] = kept.pop('Wkt')
    kept['issuedworkstartdate'] = parse_date(row.get('IssuedWorkStartDate'))
    kept['issuedworkenddate'] = parse_date(row.get('IssuedWorkEndDate'))
    kept['ispdfexists'] = bool(row.get('IsPDFExists'))
    return kept


def fetch_open_data(boundary_wgs84):
    """Fallback: fetch from NYC Open Data when nycstreets.net is unavailable."""
    transformer = Transformer.from_crs('EPSG:2263', 'EPSG:4326', always_xy=True)
    where = (
        f"boroughname='BROOKLYN' AND ("
        f"(issuedworkstartdate IS NOT NULL AND issuedworkenddate IS NOT NULL "
        f"AND issuedworkstartdate <= '{WINDOW_END}' AND issuedworkenddate >= '{WINDOW_START}') "
        f"OR (permitissuedate >= '{WINDOW_START}' AND permitissuedate <= '{WINDOW_END}'))"
    )
    select = ','.join([
        'permitnumber','applicationtrackingid','permitissuedate',
        'issuedworkstartdate','issuedworkenddate','boroughname',
        'permithousenumber','onstreetname','fromstreetname','tostreetname',
        'permitteename','permitstatusshortdesc','permittypedesc',
        'permitseriesshortdesc','permitlocationcomments','permitpurposecomments','wkt',
    ])
    all_rows, offset = [], 0
    print(f'Fetching from NYC Open Data (window {WINDOW_START} to {WINDOW_END})...', flush=True)
    while True:
        params = {'$select': select, '$where': where, '$limit': 50000, '$offset': offset, '$order': 'permitissuedate DESC'}
        resp = requests.get(OPEN_DATA_URL, params=params, timeout=120)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_rows.extend(batch)
        print(f'  {len(all_rows):,} rows...', flush=True)
        if len(batch) < 50000:
            break
        offset += 50000
    filtered = []
    for row in all_rows:
        raw_wkt = row.get('wkt', '')
        if raw_wkt and keep_row({'Wkt': raw_wkt}, boundary_wgs84):  # keep_row expects 'Wkt' key
            filtered.append({
                'IssuedWorkEndDate':   row.get('issuedworkenddate', ''),
                'IssuedWorkStartDate': row.get('issuedworkstartdate', ''),
                'PermitIssueDateFrom': row.get('permitissuedate', ''),
                'IsPDFExists': False,
                'permitissuedate':     (row.get('permitissuedate') or '')[:10],
                'permitnumber':        (row.get('permitnumber') or '').strip(),
                'permitteename':       (row.get('permitteename') or '').strip(),
                'permittypedesc':      (row.get('permittypedesc') or row.get('permitseriesshortdesc') or '').strip(),
                'permitpurposecomments': (row.get('permitpurposecomments') or '').strip(),
                'permithousenumber':   (row.get('permithousenumber') or '').strip(),
                'onstreetname':        (row.get('onstreetname') or '').strip(),
                'fromstreetname':      (row.get('fromstreetname') or '').strip(),
                'tostreetname':        (row.get('tostreetname') or '').strip(),
                'boroughname':         (row.get('boroughname') or '').strip(),
                'permitlocationcomments': (row.get('permitlocationcomments') or '').strip(),
                'permitstatusshortdesc': (row.get('permitstatusshortdesc') or '').strip(),
                'wkt':                 raw_wkt,
                'issuedworkstartdate': (row.get('issuedworkstartdate') or '')[:10],
                'issuedworkenddate':   (row.get('issuedworkenddate') or '')[:10],
                'ispdfexists': False,
            })
    return filtered


def main() -> None:
    boundary_wgs84 = load_boundary_wgs84()
    filtered = None
    try:
        extent_wkt = boundary_extent_wkt(boundary_wgs84)
        resp = requests.get(URL, params={'Wkt': extent_wkt}, timeout=90)
        resp.raise_for_status()
        rows = resp.json()
        filtered = [clean_row(row) for row in rows if keep_row(row, boundary_wgs84)]
        source = 'NYC Streets PermitSearchMobile'
        description = 'Current CB6 DOT street permits returned by the NYC Streets live permit extent endpoint and filtered to the CB6 boundary.'
        print(f'nycstreets.net: {len(filtered)} rows')
    except Exception as e:
        print(f'nycstreets.net unavailable ({e}), falling back to NYC Open Data...', flush=True)
        filtered = fetch_open_data(boundary_wgs84)
        source = 'NYC Open Data – Street Construction Permits 2022-Present (tqtj-sjs8)'
        description = 'Current and upcoming CB6 Brooklyn DOT street permits from NYC Open Data, filtered to the CB6 boundary.'
    filtered.sort(key=lambda row: (row.get('permitissuedate', ''), row.get('permitnumber', '')), reverse=True)
    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'source': source,
        'description': description,
        'record_count': len(filtered),
        'rows': filtered,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(f'Wrote {len(filtered)} rows to {OUT_PATH}')


if __name__ == '__main__':
    main()
