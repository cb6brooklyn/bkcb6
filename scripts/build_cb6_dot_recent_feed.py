#!/usr/bin/env python3
import json
import re
from datetime import datetime, timezone
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


def main() -> None:
    boundary_wgs84 = load_boundary_wgs84()
    extent_wkt = boundary_extent_wkt(boundary_wgs84)
    resp = requests.get(URL, params={'Wkt': extent_wkt}, timeout=90)
    resp.raise_for_status()
    rows = resp.json()
    filtered = [clean_row(row) for row in rows if keep_row(row, boundary_wgs84)]
    filtered.sort(key=lambda row: (row.get('permitissuedate', ''), row.get('permitnumber', '')), reverse=True)
    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'source': 'NYC Streets PermitSearchMobile',
        'description': 'Current CB6 DOT street permits returned by the NYC Streets live permit extent endpoint and filtered to the CB6 boundary.',
        'record_count': len(filtered),
        'rows': filtered,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(f'Wrote {len(filtered)} rows to {OUT_PATH}')


if __name__ == '__main__':
    main()
