import csv
import json
from pathlib import Path
from collections import defaultdict

import shapefile
from pyproj import Transformer
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.ops import transform

ROOT = Path('/home/ubuntu/bkcb6_publish_20260414_2000')
CB_GEOJSON = ROOT / 'community-district-boundaries.geojson'
ED_SHP = ROOT / 'tmp_elections/nyed_zip/nyed_26a1/nyed.shp'
CSV_PATH = ROOT / 'tmp_elections/mayor_edlevel.csv'
OUT_PATH = ROOT / 'data/mayor_cb_winner_margin.json'

BOROUGHS = {
    '1': {'slug': 'manhattan', 'short': 'MN', 'name': 'Manhattan', 'valid_districts': set(range(1, 13))},
    '2': {'slug': 'bronx', 'short': 'BX', 'name': 'Bronx', 'valid_districts': set(range(1, 13))},
    '3': {'slug': 'brooklyn', 'short': 'BK', 'name': 'Brooklyn', 'valid_districts': set(range(1, 19))},
    '4': {'slug': 'queens', 'short': 'QN', 'name': 'Queens', 'valid_districts': set(range(1, 15))},
    '5': {'slug': 'statenisland', 'short': 'SI', 'name': 'Staten Island', 'valid_districts': set(range(1, 4))},
}

CANDIDATES = {
    'mamdani': ['zohran kwame mamdani'],
    'cuomo': ['andrew m. cuomo'],
    'sliwa': ['curtis a. sliwa'],
}

transformer = Transformer.from_crs('EPSG:4326', 'EPSG:2263', always_xy=True)


def normalize_boro_cd(raw):
    code = str(raw)
    if code.endswith('.0'):
        code = code[:-2]
    code = code.strip()
    if len(code) == 2:
        code = code[0] + code[1].zfill(2)
    return code


def label_from_boro_cd(boro_cd):
    borough = BOROUGHS[boro_cd[0]]
    district = int(boro_cd[1:])
    return f"{borough['short']}CB{district}"


def long_label_from_boro_cd(boro_cd):
    borough = BOROUGHS[boro_cd[0]]
    district = int(boro_cd[1:])
    return f"{borough['name']} Community Board {district}"


def pct(value, total):
    return round((value / total * 100.0) if total else 0.0, 1)


def find_candidate(unit_name):
    u = (unit_name or '').lower()
    for key, names in CANDIDATES.items():
        if any(name in u for name in names):
            return key
    return None


with CB_GEOJSON.open() as f:
    cb_geo = json.load(f)

cb_polygons = {}
for feat in cb_geo['features']:
    boro_cd = normalize_boro_cd(feat['properties']['boro_cd'])
    borough = BOROUGHS.get(boro_cd[0])
    district = int(boro_cd[1:])
    if not borough or district not in borough['valid_districts']:
        continue
    geom = shape(feat['geometry'])
    geom_2263 = transform(transformer.transform, geom)
    cb_polygons[boro_cd] = geom_2263

ed_to_cb = {}
r = shapefile.Reader(str(ED_SHP))
for sr in r.iterShapeRecords():
    elect_dist = int(sr.record[0])
    shp = sr.shape
    pts = shp.points
    parts = list(shp.parts) + [len(pts)]
    polys = []
    for i in range(len(parts) - 1):
        ring = pts[parts[i]:parts[i + 1]]
        if len(ring) >= 3:
            try:
                polys.append(Polygon(ring))
            except Exception:
                pass
    if not polys:
        continue
    geom = polys[0] if len(polys) == 1 else MultiPolygon(polys)
    centroid = geom.representative_point()
    cb_match = None
    for boro_cd, cb_geom in cb_polygons.items():
        if cb_geom.contains(centroid):
            cb_match = boro_cd
            break
    if cb_match:
        ed_to_cb[elect_dist] = cb_match

cb_totals = defaultdict(lambda: {'mamdani': 0, 'cuomo': 0, 'sliwa': 0, 'ed_results': defaultdict(lambda: {'mamdani': 0, 'cuomo': 0, 'sliwa': 0})})

with CSV_PATH.open(newline='', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = ['AD', 'ED', 'County', 'EDAD Status', 'Event', 'Party/Independent Body', 'Office/Position Title', 'District Key', 'VoteFor', 'Unit Name', 'Tally']
    column_count = len(header)
    for raw_row in reader:
        if len(raw_row) < column_count * 2:
            continue
        row = dict(zip(header, raw_row[column_count:column_count * 2]))
        if row.get('Office/Position Title') != 'Mayor':
            continue
        candidate = find_candidate(row.get('Unit Name'))
        if not candidate:
            continue
        try:
            ad = int(row['AD'])
            ed = int(row['ED'])
            tally = int(float(row['Tally'] or 0))
        except Exception:
            continue
        elect_dist = ad * 1000 + ed
        cb = ed_to_cb.get(elect_dist)
        if not cb:
            continue
        cb_totals[cb][candidate] += tally
        cb_totals[cb]['ed_results'][elect_dist][candidate] += tally

features = []
by_borough = {info['slug']: [] for info in BOROUGHS.values()}
max_margin = 0.0

for feat in cb_geo['features']:
    boro_cd = normalize_boro_cd(feat['properties']['boro_cd'])
    borough = BOROUGHS.get(boro_cd[0])
    district_number = int(boro_cd[1:])
    if not borough or district_number not in borough['valid_districts']:
        continue
    totals = cb_totals.get(boro_cd)
    if not totals:
        continue
    m = totals['mamdani']
    c = totals['cuomo']
    s = totals['sliwa']
    total_votes = m + c + s
    winner = 'mamdani' if m >= c else 'cuomo'
    loser = 'cuomo' if winner == 'mamdani' else 'mamdani'
    winner_votes = totals[winner]
    loser_votes = totals[loser]
    margin_pct = pct(winner_votes - loser_votes, total_votes)
    max_margin = max(max_margin, margin_pct)
    ed_results = totals['ed_results']
    winner_ed_count = sum(1 for vals in ed_results.values() if vals[winner] >= vals[loser] and vals[winner] >= vals['sliwa'])
    total_eds = len(ed_results)
    district = district_number
    summary = {
        'boro_cd': boro_cd,
        'borough_slug': borough['slug'],
        'borough_name': borough['name'],
        'district_number': district,
        'district_label': label_from_boro_cd(boro_cd),
        'district_name': long_label_from_boro_cd(boro_cd),
        'winner': winner,
        'winner_name': 'Mamdani' if winner == 'mamdani' else 'Cuomo',
        'loser_name': 'Cuomo' if winner == 'mamdani' else 'Mamdani',
        'mamdani_votes': m,
        'cuomo_votes': c,
        'sliwa_votes': s,
        'total_votes': total_votes,
        'mamdani_pct': pct(m, total_votes),
        'cuomo_pct': pct(c, total_votes),
        'sliwa_pct': pct(s, total_votes),
        'margin_pct': round(margin_pct, 1),
        'winner_ed_count': winner_ed_count,
        'total_eds': total_eds,
    }
    features.append(summary)
    by_borough[borough['slug']].append(summary)

for slug, items in by_borough.items():
    items.sort(key=lambda x: x['district_number'])

payload = {
    'max_margin_pct': round(max_margin, 1),
    'boroughs': by_borough,
    'districts': {item['boro_cd']: item for item in features},
}

with OUT_PATH.open('w') as f:
    json.dump(payload, f, indent=2)

print('WROTE', OUT_PATH)
print('MAX_MARGIN', round(max_margin, 1))
for slug, items in by_borough.items():
    if not items:
        continue
    top = max(items, key=lambda x: x['margin_pct'])
    print(slug, len(items), top['district_label'], top['winner_name'], top['margin_pct'])
