#!/usr/bin/env python3
"""Build civic/stats.json: ACS 2023 5-year figures for every NYC community district (PUMA), borough, the city,
the state, every NY Assembly, State Senate and Congressional district, from data.census.gov; FRED unemployment
rates; and the asking rents from the site's rent maps."""
import json, subprocess, sys, time, re, os
OUT = sys.argv[1]
UA = 'Mozilla/5.0'
def get(url):
    for i in range(3):
        r = subprocess.run(['curl', '-s', '--max-time', '60', '-A', UA, url], capture_output=True)
        if r.stdout.strip():
            try: return json.loads(r.stdout)
            except Exception: pass
        time.sleep(3 + 3 * i)
    return None
TABLES = ['B01003', 'B01002', 'B19013', 'B25064', 'B25077', 'B25003', 'B25070', 'B23025', 'B17001', 'B25001']
GEOS = ['040XX00US36$7950000', '040XX00US36$0500000', '040XX00US36$6200000', '040XX00US36$6100000',
        '1600000US3651000', '0400000US36'] + [f'5001800US36{n:02d}' for n in range(1, 27)]
raw = {}   # geoid -> {table_var: value}
names = {}
for t in TABLES:
    for g in GEOS:
        d = get(f'https://data.census.gov/api/access/data/table?id=ACSDT5Y2023.{t}&g={g}')
        rows = (d or {}).get('response', {}).get('data') or []
        if not rows: print('EMPTY', t, g); continue
        hdr = rows[0]
        for r in rows[1:]:
            rec = dict(zip(hdr, r)); gid = rec['GEO_ID']; names[gid] = rec.get('NAME', '')
            for k, v in rec.items():
                if k.endswith('E') and k != 'NAME' and not k.endswith('EA') and v not in (None, '', '*****'):
                    try: raw.setdefault(gid, {})[k] = float(v)
                    except ValueError: pass
        time.sleep(0.4)
    print('table', t, 'geos', len(raw), flush=True)

def key_for(gid, name):
    if gid.startswith('795P200US36'):
        m = re.search(r'NYC-(Manhattan|Bronx|Brooklyn|Queens|Staten Island) Community Districts? ([\d &]+)--', name)
        if not m: return []
        b = {'Manhattan': '1', 'Bronx': '2', 'Brooklyn': '3', 'Queens': '4', 'Staten Island': '5'}[m.group(1)]
        return [b + f'{int(n):02d}' for n in re.findall(r'\d+', m.group(2))]
    if gid.startswith('0500000US36'):
        return {'36005': 'b2', '36047': 'b3', '36061': 'b1', '36081': 'b4', '36085': 'b5'}.get(gid[-5:], None) and [{'36005': 'b2', '36047': 'b3', '36061': 'b1', '36081': 'b4', '36085': 'b5'}[gid[-5:]]] or []
    if gid.startswith('620L800US36'): return [f'ad{int(gid[-3:])}']
    if gid.startswith('610U800US36'): return [f'sd{int(gid[-3:])}']
    if gid.startswith('5001800US36'): return [f'cd{int(gid[-2:])}']
    if gid == '1600000US3651000': return ['nyc']
    if gid == '0400000US36': return ['ny']
    return []
def pct(a, b): return round(100.0 * a / b, 1) if a is not None and b else None
areas = {}
for gid, v in raw.items():
    keys = key_for(gid, names.get(gid, ''))
    if not keys: continue
    g = v.get
    rec = {'name': names.get(gid, ''), 'geoid': gid, 'shared': len(keys) > 1,
           'pop': g('B01003_001E'), 'median_age': g('B01002_001E'), 'median_income': g('B19013_001E'),
           'median_rent': g('B25064_001E'), 'median_home_value': g('B25077_001E'), 'units': g('B25001_001E'),
           'renter_pct': pct(g('B25003_003E'), g('B25003_001E')),
           'rent_burden_pct': pct(sum(g(f'B25070_0{i:02d}E') or 0 for i in range(7, 11)), (g('B25070_001E') or 0) - (g('B25070_011E') or 0)),
           'unemployment_pct': pct(g('B23025_005E'), g('B23025_003E')),
           'poverty_pct': pct(g('B17001_002E'), g('B17001_001E'))}
    for k in keys: areas[k] = rec
# FRED
fred = {}
for key, sid, label in [('b3', 'NYKING7URN', 'Kings County'), ('b2', 'NYBRON5URN', 'Bronx County'), ('b1', 'NYNEWY1URN', 'New York County'),
                        ('b4', 'NYQUEE1URN', 'Queens County'), ('b5', 'NYRICH5URN', 'Richmond County'), ('nyc', 'NEWY636URN', 'New York City'),
                        ('ny', 'NYUR', 'New York State'), ('us', 'UNRATE', 'United States')]:
    r = subprocess.run(['curl', '-s', '--max-time', '30', f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}'], capture_output=True)
    lines = [l for l in r.stdout.decode().strip().split('\n') if re.match(r'\d{4}-\d\d-\d\d,[\d.]+$', l)]
    if lines:
        d, val = lines[-1].split(','); prev = lines[-13].split(',')[1] if len(lines) >= 13 else None
        fred[key] = {'series': sid, 'label': label, 'date': d, 'value': float(val), 'year_ago': float(prev) if prev else None,
                     'url': f'https://fred.stlouisfed.org/series/{sid}'}
# Rent maps (the site's data)
rents = {}
try:
    bk = json.load(open('/tmp/bkf/data/bk-rents.geojson'))
    for f in bk['features']:
        p = f['properties']; n = int(re.sub(r'\D', '', p['cb_code']))
        rents[f'3{n:02d}'] = {k: p.get(k) for k in ('rent_studio', 'rent_1br', 'rent_2br', 'rent_3br', 'rent_all')} | {'neighborhoods': p.get('neighborhoods', '')}
    roll = json.load(open('/tmp/bkf/data/rent-ranges-rollup.json'))
    for k, v in roll.items():
        kk = {'b:Manhattan': 'b1', 'b:Bronx': 'b2', 'b:Brooklyn': 'b3', 'b:Queens': 'b4', 'b:Staten Island': 'b5', 'x:NYC': 'nyc'}.get(k)
        if kk: rents[kk] = {x: v.get(x) for x in ('rent_studio', 'rent_1br', 'rent_2br', 'rent_3br', 'rent_all', 'range_lo', 'range_hi', 'sub_lo', 'sub_lo_name', 'sub_hi', 'sub_hi_name')}
except Exception as e: print('rents', e)
out = {'acs': {'source': 'U.S. Census Bureau, American Community Survey 2019-2023 5-year estimates', 'url': 'https://data.census.gov',
               'note': 'Community districts are Census public use microdata areas (PUMAs); Manhattan 1 & 2, 5 & 6 and the Bronx 1 & 2, 3 & 6 share one PUMA each.'},
       'fred': {'source': 'U.S. Bureau of Labor Statistics via FRED, Federal Reserve Bank of St. Louis', 'series': fred},
       'rents': {'source': 'bkcb6.app rent maps: median asking rents', 'areas': rents},
       'areas': areas}
json.dump(out, open(OUT, 'w'), separators=(',', ':'))
print('areas', len(areas), 'fred', len(fred), 'rents', len(rents))
print(json.dumps(areas.get('306')), json.dumps(areas.get('b3')), json.dumps(fred.get('b3')))
