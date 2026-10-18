#!/usr/bin/env python3
"""Census profile of every community district, neighborhood and census tract in New York City, for /atlas/.

Source: American Community Survey 2020-2024 5-year estimates, the Census Bureau's table-based summary files
(www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF), every census tract in the five boroughs.
Tracts are placed in a community district and a neighborhood (data/community-districts.geojson,
data/nta-boundaries.geojson) by the Census Bureau's internal point for the tract (2024 Gazetteer); 2020 tracts nest
in 2020 neighborhoods and community district tabulation areas, so each tract falls in exactly one.
Counts are summed from tracts. Medians cannot be summed: median household income and median gross rent are
interpolated within the Census income and rent brackets of the summed counts (the method NYC Planning uses for
its community district profiles), and mean commute time uses the midpoints of the commute-time brackets.

Writes data/atlas/acs.json (every measure for every board, neighborhood, borough and the city) and
data/atlas/tracts.json (every measure for every tract, keyed by GEOID) and data/atlas/tracts.topo-ready.geojson.
python3 tools/build_acs_atlas.py <scratch dir>"""
import csv, io, json, math, os, re, subprocess, sys, zipfile
import shapefile
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = sys.argv[1]
OUT = os.path.join(ROOT, 'data', 'atlas'); os.makedirs(OUT, exist_ok=True)
BASE = 'https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-%s.dat'
COUNTY = {'005': '2', '047': '3', '061': '1', '081': '4', '085': '5'}
BORON = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
TABLES = ['B01003', 'B01001', 'B03002', 'B15003', 'B05002', 'C16001', 'B19001', 'C17002', 'B23025', 'B08301', 'B08303',
          'B25003', 'B25063', 'B25070', 'B25002', 'B25034', 'B25024', 'B25044', 'B28002', 'B27010', 'B18101', 'B21001',
          'B25008', 'B11001', 'B25014']


def table(t):
    cache = os.path.join(SCR, t + '.psv')
    if not os.path.exists(cache):
        cmd = "curl -s -m 1200 '%s' | awk 'NR==1 || /^1400000US36(005|047|061|081|085)/' > '%s'" % (BASE % t.lower(), cache)
        subprocess.run(cmd, shell=True, check=True)
    rows = list(csv.reader(open(cache), delimiter='|'))
    head = rows[0]
    out = {}
    for r in rows[1:]:
        g = r[0].split('US')[1]
        out[g] = {h.split('_')[1][1:]: float(v) if v not in ('', None) and float(v) > -999999 else 0.0
                  for h, v in zip(head[1:], r[1:]) if h.split('_')[1].startswith('E')}
    assert len(out) == 2327, (t, len(out))
    return out


# ---- geography ----
gaz = {}
for r in csv.DictReader(open(os.path.join(SCR, '2024_gaz_tracts_36.txt')), delimiter='\t'):
    r = {k.strip(): v.strip() for k, v in r.items()}
    if r['GEOID'][2:5] in COUNTY:
        gaz[r['GEOID']] = (float(r['INTPTLONG']), float(r['INTPTLAT']), float(r['ALAND_SQMI']))
cds = [(f['properties']['boro_cd'], shape(f['geometry']).buffer(0)) for f in json.load(open(os.path.join(ROOT, 'data/community-districts.geojson')))['features']]
ntas = [(f['properties'], shape(f['geometry']).buffer(0)) for f in json.load(open(os.path.join(ROOT, 'data/nta-boundaries.geojson')))['features']]
cdt, ntt = STRtree([g for _, g in cds]), STRtree([g for _, g in ntas])


def find(tree, items, pt):
    for i in tree.query(pt):
        if items[i][1].contains(pt):
            return items[i][0]
    # a point on the shoreline: nearest shape
    i = tree.nearest(pt)
    return items[i][0]


tract_cd, tract_nta = {}, {}
for g, (x, y, a) in gaz.items():
    pt = Point(x, y)
    tract_cd[g] = find(cdt, cds, pt)
    tract_nta[g] = find(ntt, ntas, pt)['id']

T = {t: table(t) for t in TABLES}
tracts = sorted(T['B01003'])
assert set(tracts) <= set(gaz), set(tracts) - set(gaz)

# ---- per-geography raw sums ----
def raw(g):
    v = {}
    for t in TABLES:
        for k, x in T[t][g].items():
            v[t + '_' + k] = x
    v['_area'] = gaz[g][2]
    return v


def add(a, b):
    for k, x in b.items():
        a[k] = a.get(k, 0.0) + x


INC = [0, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000, 50000, 60000, 75000, 100000, 125000, 150000, 200000, None]
RENT = [0, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 900, 1000, 1250, 1500, 2000, 2500, 3000, 3500, None]


def median(counts, edges):
    tot = sum(counts)
    if tot <= 0:
        return None
    half, run = tot / 2.0, 0.0
    for i, c in enumerate(counts):
        if run + c >= half and c > 0:
            lo, hi = edges[i], edges[i + 1]
            if hi is None:
                return -float(lo)  # open-ended top bracket: the median is at least its floor (negative marks "or more")
            return lo + (half - run) / c * (hi - lo)
        run += c
    return None


def pct(n, d):
    return None if d <= 0 else round(100.0 * n / d, 1)


def S(v, t, a, b):
    return sum(v.get('%s_%03d' % (t, i), 0.0) for i in range(a, b + 1))


def measures(v):
    m = {}
    pop = v['B01003_001']
    m['pop'] = round(pop)
    m['density'] = round(pop / v['_area']) if v['_area'] else None
    # age (B01001: male 3-25, female 27-49)
    u18 = S(v, 'B01001', 3, 6) + S(v, 'B01001', 27, 30)
    o65 = S(v, 'B01001', 20, 25) + S(v, 'B01001', 44, 49)
    m['age_u18'], m['age_65'] = pct(u18, pop), pct(o65, pop)
    m['age_18_64'] = pct(pop - u18 - o65, pop)
    # race and Hispanic origin
    rt = v['B03002_001']
    m['race_white'], m['race_black'], m['race_asian'] = pct(v['B03002_003'], rt), pct(v['B03002_004'], rt), pct(v['B03002_006'], rt)
    m['race_hisp'] = pct(v['B03002_012'], rt)
    m['race_other'] = pct(v['B03002_005'] + v['B03002_007'] + v['B03002_008'] + v['B03002_009'], rt)
    # education, 25 and over
    e = v['B15003_001']
    m['edu_ba'] = pct(S(v, 'B15003', 22, 25), e)
    m['edu_nohs'] = pct(S(v, 'B15003', 2, 16), e)
    # foreign born, language
    m['foreign'] = pct(v['B05002_013'], v['B05002_001'])
    m['lang_other'] = pct(v['C16001_001'] - v['C16001_002'], v['C16001_001'])
    # income and poverty
    m['inc_median'] = median([v['B19001_%03d' % i] for i in range(2, 18)], INC)
    if m['inc_median'] is not None and m['inc_median'] < 0:
        m['inc_median'], m['inc_median_top'] = -m['inc_median'], 1
    m['inc_median'] = round(m['inc_median']) if m['inc_median'] is not None else None
    m['inc_200k'] = pct(v['B19001_017'], v['B19001_001'])
    m['inc_u25k'] = pct(S(v, 'B19001', 2, 5), v['B19001_001'])
    m['poverty'] = pct(v['C17002_002'] + v['C17002_003'], v['C17002_001'])
    # work
    lf = v['B23025_003']
    m['unemp'] = pct(v['B23025_005'], lf)
    # commuting, workers 16+
    w = v['B08301_001']
    m['com_transit'], m['com_drive'] = pct(v['B08301_010'], w), pct(v['B08301_002'], w)
    m['com_walk'], m['com_bike'], m['com_home'] = pct(v['B08301_019'], w), pct(v['B08301_018'], w), pct(v['B08301_021'], w)
    mids = [2.5, 7, 12, 17, 22, 27, 32, 37, 42, 52, 74.5, 100]
    tw = v['B08303_001']
    m['com_minutes'] = round(sum(v['B08303_%03d' % (i + 2)] * mids[i] for i in range(12)) / tw, 1) if tw else None
    # housing
    occ = v['B25003_001']
    m['hh'] = round(occ)
    m['renters'] = pct(v['B25003_003'], occ)
    m['hh_size'] = round(v['B25008_001'] / occ, 2) if occ else None
    m['vacant'] = pct(v['B25002_003'], v['B25002_001'])
    rent = median([v['B25063_%03d' % i] for i in range(3, 27)], RENT)
    if rent is not None and rent < 0:
        rent, m['rent_median_top'] = -rent, 1
    m['rent_median'] = round(rent) if rent is not None else None
    rb = v['B25070_001'] - v['B25070_011']
    m['rent_burden'] = pct(S(v, 'B25070', 7, 10), rb)
    m['rent_severe'] = pct(v['B25070_010'], rb)
    hu = v['B25034_001']
    m['built_pre1940'] = pct(v['B25034_011'], hu)
    m['built_2000'] = pct(S(v, 'B25034', 2, 4), hu)
    us = v['B25024_001']
    m['units_1_2'] = pct(S(v, 'B25024', 2, 4), us)
    m['units_20'] = pct(S(v, 'B25024', 8, 9), us)
    m['crowded'] = pct(S(v, 'B25014', 5, 7) + S(v, 'B25014', 11, 13), v['B25014_001'])
    m['no_car'] = pct(v['B25044_003'] + v['B25044_010'], v['B25044_001'])
    m['broadband'] = pct(v['B28002_004'], v['B28002_001'])
    m['no_internet'] = pct(v['B28002_013'], v['B28002_001'])
    # health insurance (B27010: no coverage lines 17, 33, 50, 66)
    m['uninsured'] = pct(v['B27010_017'] + v['B27010_033'] + v['B27010_050'] + v['B27010_066'], v['B27010_001'])
    # disability (B18101: with a disability lines, both sexes, every age group)
    dis = sum(v['B18101_%03d' % i] for i in (4, 7, 10, 13, 16, 19, 23, 26, 29, 32, 35, 38))
    m['disability'] = pct(dis, v['B18101_001'])
    m['veterans'] = pct(v['B21001_002'], v['B21001_001'])
    m['hh_kids_alone'] = None
    m['hh_alone'] = pct(v['B11001_008'], v['B11001_001'])
    m.pop('hh_kids_alone')
    return m


units = {}
def acc(key, name, kind, g):
    u = units.setdefault(key, {'name': name, 'kind': kind, 'raw': {}, 'tracts': 0})
    add(u['raw'], raw(g)); u['tracts'] += 1


nta_names = {p['id']: p['name'] for p, _ in ntas}
tract_out = {}
for g in tracts:
    cd, nta, b = tract_cd[g], tract_nta[g], COUNTY[g[2:5]]
    if int(cd[1:]) <= 18:
        acc('cb:' + cd, None, 'board', g)
    else:
        acc('jia:' + cd, None, 'jia', g)
    acc('nta:' + nta, nta_names[nta], 'neighborhood', g)
    acc('boro:' + b, BORON[b], 'borough', g)
    acc('nyc', 'New York City', 'city', g)
    tract_out[g] = dict(measures(raw(g)), cd=cd, nta=nta)

out = {}
for k, u in units.items():
    m = measures(u['raw']); m['tracts'] = u['tracts']
    out[k] = {'name': u['name'], 'kind': u['kind'], 'm': m}
# every tract accounted for, once per level
assert sum(u['tracts'] for k, u in units.items() if u['kind'] in ('board', 'jia')) == len(tracts)
assert units['nyc']['tracts'] == len(tracts)
boards = sorted(k for k in out if k.startswith('cb:'))
print(len(tracts), 'tracts;', len(boards), 'boards;', sum(1 for k in out if k.startswith('nta:')), 'neighborhoods; NYC pop', out['nyc']['m']['pop'])
assert len(boards) == 59, boards
json.dump(tract_out, open(os.path.join(OUT, 'tracts.json'), 'w'), separators=(',', ':'))

# ---- tract shapes, trimmed to the five boroughs ----
z = zipfile.ZipFile(os.path.join(SCR, 'cb_2024_36_tract_500k.zip'))
names = {os.path.splitext(n)[1]: n for n in z.namelist()}
r = shapefile.Reader(shp=io.BytesIO(z.read(names['.shp'])), dbf=io.BytesIO(z.read(names['.dbf'])), shx=io.BytesIO(z.read(names['.shx'])))
fields = [f[0] for f in r.fields[1:]]
feats = []
for sr in r.shapeRecords():
    p = dict(zip(fields, sr.record))
    if p['GEOID'] in tract_out:
        geom = shape(sr.shape.__geo_interface__).simplify(0.00012, preserve_topology=True)
        gi = geom.__geo_interface__
        def rnd(c):
            return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
        feats.append({'type': 'Feature', 'properties': {'g': p['GEOID']}, 'geometry': {'type': gi['type'], 'coordinates': rnd(gi['coordinates'])}})
missing = [g for g in tract_out if g not in {f['properties']['g'] for f in feats}]
assert all(tract_out[g]['pop'] == 0 for g in missing), missing  # water-only tracts have no cartographic shape
print('tracts with no shape (water only, 0 residents):', missing)
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(OUT, 'tracts.geojson'), 'w'), separators=(',', ':'))
print('tract shapes', len(feats))

# ---- the site's own neighborhoods (data/city-neighborhoods.geojson): each tract's counts split by the share of its
# land area that lies in each neighborhood, so a neighborhood smaller than a tract still gets its part ----
from shapely.geometry import shape as _shape
nbs = [(f['properties']['boro'] + '|' + f['properties']['nb'], f['properties'], _shape(f['geometry']).buffer(0))
       for f in json.load(open(os.path.join(ROOT, 'data/city-neighborhoods.geojson')))['features']]
nbt = STRtree([g for _, _, g in nbs])
shapes = {f['properties']['g']: _shape(f['geometry']).buffer(0) for f in feats}
nb_raw, nb_share = {}, {}
for g, geom in shapes.items():
    if geom.area <= 0:
        continue
    rv = raw(g)
    for i in nbt.query(geom):
        k, props, ng = nbs[i]
        a = geom.intersection(ng).area / geom.area
        if a < 0.01:
            continue
        acc_ = nb_raw.setdefault(k, {})
        for kk, x in rv.items():
            acc_[kk] = acc_.get(kk, 0.0) + x * a
        nb_share[k] = nb_share.get(k, 0.0) + a
for k, rv in nb_raw.items():
    boro, name = k.split('|', 1)
    m = measures(rv); m['tracts'] = round(nb_share[k], 2)
    out['nb:' + k] = {'name': name, 'boro': boro, 'kind': 'site-neighborhood', 'm': m}
print(len(nb_raw), 'of', len(nbs), 'site neighborhoods have residents in a tract;',
      'missing:', [k for k, _, _ in nbs if k not in nb_raw][:30])
json.dump({'source': 'U.S. Census Bureau, American Community Survey 2020-2024 5-year estimates, table-based summary files; '
                     'tracts placed by Census internal point in data/community-districts.geojson and data/nta-boundaries.geojson',
           'tables': TABLES, 'units': out}, open(os.path.join(OUT, 'acs.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
