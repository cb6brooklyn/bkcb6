import ast
import json
import re
from pathlib import Path

import requests

REPO = Path('/home/ubuntu/work/bkcb6_repo_1776697502')
SRC_HTML = REPO / 'lamp.html'
OUT = REPO / 'data' / 'liquor_cb6.json'
OUT.parent.mkdir(parents=True, exist_ok=True)

html = SRC_HTML.read_text()
poly_match = re.search(r'const\s+LAMP_CB6\s*=\s*(\[[\s\S]*?\]);', html)
if not poly_match:
    raise SystemExit('Could not locate LAMP_CB6 polygon in lamp.html')
polygon = ast.literal_eval(poly_match.group(1))

LAMP_CLASS_BEV = {340:'Full Liquor',370:'Full Liquor',423:'Full Liquor',349:'Full Liquor',243:'Full Liquor',346:'Full Liquor',240:'Wine & Beer',267:'Wine & Beer',138:'Wine & Beer',249:'Wine & Beer',361:'Wine & Beer',416:'Brewery / Special',15:'Brewery / Special',14:'Brewery / Special',25:'Brewery / Special',31:'Brewery / Special',52:'Brewery / Special',56:'Brewery / Special'}
LAMP_CLASS_DETAIL = {340:'Restaurant — Full Liquor',370:'Bar / Food & Beverage — Full Liquor',423:'Additional Bar — Full Liquor',349:'Club — Full Liquor',243:'Hotel — Full Liquor',346:'Catering Establishment — Full Liquor',240:'Restaurant — Wine & Beer',267:'Bar / Food & Beverage — Wine & Beer',138:'Food & Beverage — Wine & Beer',249:'Club — Wine & Beer',361:'Vessel — Wine & Beer',416:'Restaurant Brewer',15:'Farm Brewer',14:'Micro-Brewery',25:'Farm Cidery',31:'Winery',52:'Micro-Distillery',56:'Farm Distillery'}
ONSITE = set(LAMP_CLASS_BEV)


def pip(px, py, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def parse_point(value):
    if not value:
        return None
    if isinstance(value, dict):
        coords = value.get('coordinates') or []
        if len(coords) >= 2:
            return float(coords[1]), float(coords[0])
        return None
    m = re.search(r'POINT \(([-.0-9]+) ([-.0-9]+)\)', str(value))
    if not m:
        return None
    lon = float(m.group(1))
    lat = float(m.group(2))
    return lat, lon

all_rows = []
offset = 0
while True:
    url = 'https://data.ny.gov/resource/9s3h-dpkz.json'
    params = {
        '$where': "premisescounty='Kings'",
        '$limit': 1000,
        '$offset': offset,
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    page = r.json()
    if not page:
        break
    all_rows.extend(page)
    offset += len(page)
    if len(page) < 1000:
        break

filtered = []
for row in all_rows:
    raw_class = str(row.get('class') or row.get('Class') or '').strip()
    if not raw_class.isdigit():
        continue
    cls = int(raw_class)
    if cls not in ONSITE:
        continue
    pt = parse_point(row.get('georeference', ''))
    if not pt:
        continue
    lat, lon = pt
    if not pip(lon, lat, polygon):
        continue
    bev = LAMP_CLASS_BEV.get(cls, 'Unknown')
    detail = LAMP_CLASS_DETAIL.get(cls, str(cls))
    filtered.append({
        'license_id': row.get('licensepermitid') or row.get('license_permit_id') or row.get('serial_number') or '',
        'legal_name': row.get('legalname') or '',
        'dba': row.get('dba') or '',
        'address': row.get('actualaddressofpremises') or row.get('actual_address_of_premises') or row.get('premise_address') or '',
        'zip': row.get('zipcode') or row.get('zip') or '',
        'status': row.get('status') or row.get('license_status') or 'Issued',
        'bev': bev,
        'detail': detail,
        'class_code': cls,
        'lat': lat,
        'lon': lon,
        'search': ' | '.join(filter(None, [row.get('legalname',''), row.get('dba',''), row.get('actualaddressofpremises','') or row.get('actual_address_of_premises',''), bev, detail, row.get('status','') or row.get('license_status','')])).lower(),
    })

filtered.sort(key=lambda r: (r['bev'], r['legal_name'], r['dba'], r['address']))
stats = {}
for row in filtered:
    stats[row['bev']] = stats.get(row['bev'], 0) + 1

payload = {
    'source': 'NY Open Data SLA active and pending Kings County records filtered to the BKCB6 polygon on 2026-04-20',
    'total': len(filtered),
    'stats': stats,
    'records': filtered,
}
OUT.write_text(json.dumps(payload, indent=2))
print(f'wrote {len(filtered)} records to {OUT}')
for k, v in stats.items():
    print(f'{k}: {v}')
