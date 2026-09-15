#!/usr/bin/env python3
"""Build data/vzr/*.json for /visionzero/ (Vision Zero Reimagined by CB & CD).

Inputs (already downloaded):
  /home/claude/crash/p*.csv      NYPD Motor Vehicle Collisions - Crashes (h9gi-nx95), injury or fatal, 2014-01-01 on, with coordinates
  /home/claude/crash/nolat*.csv  same, rows without usable coordinates (counted, not mapped)
  /home/claude/vzv/*.geojson     DOT Vision Zero View layers
  data/community-districts.geojson (71 polygons incl. joint interest areas), data/council-districts.geojson (51)
  data/speed-limits/{borocd}.json  DOT VZV Speed Limits segments with street names, already split by CD
"""
import csv, glob, json, math, os, re, collections, datetime
from shapely.geometry import shape, Point, LineString, MultiLineString
from shapely.strtree import STRtree
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'vzr'); os.makedirs(OUT, exist_ok=True)
BORO = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
BORONAME = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
LAST_CRASH = None

MAXCB = {'1': 12, '2': 12, '3': 18, '4': 14, '5': 3}
def is_cb(borocd): return int(borocd[1:]) <= MAXCB[borocd[0]]
def cd_label(borocd):
    b, n = borocd[0], int(borocd[1:])
    return (BORO[b] + 'CB' + str(n)) if is_cb(borocd) else (BORO[b] + ' JIA ' + str(n))

# ---------- polygons ----------
cdg = json.load(open(os.path.join(ROOT, 'data', 'community-districts.geojson')))
cd_polys, cd_keys = [], []
for f in cdg['features']:
    cd_polys.append(shape(f['geometry']).buffer(0)); cd_keys.append(f['properties']['boro_cd'])
cd_tree = STRtree(cd_polys)
ccg = json.load(open(os.path.join(ROOT, 'data', 'council-districts.geojson')))
cc_polys, cc_keys = [], []
for f in ccg['features']:
    cc_polys.append(shape(f['geometry']).buffer(0)); cc_keys.append(str(f['properties']['cc']))
cc_tree = STRtree(cc_polys)

def locate(tree, polys, keys, pt):
    for i in tree.query(pt):
        if polys[i].contains(pt) or polys[i].touches(pt):
            return keys[i]
    # nearest within ~15 m for points on boundaries
    i = tree.nearest(pt)
    if polys[i].distance(pt) < 0.00015:
        return keys[i]
    return None

# ---------- crashes ----------
YEARS = [str(y) for y in range(2014, 2027)]
def blank():
    return {'crashes': 0, 'inj': 0, 'k': 0, 'pi': 0, 'pk': 0, 'ci': 0, 'ck': 0, 'mi': 0, 'mk': 0}
def blank_years():
    return {y: blank() for y in YEARS}
by_cd = collections.defaultdict(blank_years)
by_cc = collections.defaultdict(blank_years)
city = blank_years()
unmapped = blank_years()
cb6_int = collections.defaultdict(lambda: {'crashes': 0, 'inj': 0, 'k': 0, 'pi': 0, 'pk': 0, 'ci': 0, 'ck': 0, 'mi': 0, 'mk': 0, 'lat': 0.0, 'lng': 0.0, 'n': 0})
cb6_fatal = []
cd_locate_miss = 0
cc_locate_miss = 0
n_rows = 0
def I(v):
    try: return int(float(v or 0))
    except: return 0
ABBR = {'AVE': 'AVENUE', 'AV': 'AVENUE', 'ST': 'STREET', 'STR': 'STREET', 'PL': 'PLACE', 'BLVD': 'BOULEVARD', 'PKWY': 'PARKWAY', 'PKY': 'PARKWAY',
        'EXPY': 'EXPRESSWAY', 'EXPWY': 'EXPRESSWAY', 'RD': 'ROAD', 'DR': 'DRIVE', 'CT': 'COURT', 'TER': 'TERRACE', 'LN': 'LANE', 'SQ': 'SQUARE', 'HWY': 'HIGHWAY',
        'E': 'EAST', 'W': 'WEST', 'N': 'NORTH', 'S': 'SOUTH', 'BQE': 'BROOKLYN QUEENS EXPRESSWAY'}
def norm_street(s):
    s = (s or '').strip().upper()
    s = re.sub(r'[.,]', '', s)
    s = re.sub(r'\s+', ' ', s)
    if not s: return s
    words = [ABBR.get(w, w) for w in s.split(' ')]
    s = ' '.join(words)
    s = re.sub(r'\b(\d+)(ST|ND|RD|TH)\b', r'\1', s)
    s = s.replace('BROOKLYN-QUEENS EXPRESSWAY', 'BROOKLYN QUEENS EXPRESSWAY')
    return s
for fn in sorted(glob.glob('/home/claude/crash/p*.csv')):
    for r in csv.DictReader(open(fn)):
        n_rows += 1
        y = r['crash_date'][:4]
        d = r['crash_date'][:10]
        if LAST_CRASH is None or d > LAST_CRASH: LAST_CRASH = d
        rec = {'crashes': 1, 'inj': I(r['number_of_persons_injured']), 'k': I(r['number_of_persons_killed']),
               'pi': I(r['number_of_pedestrians_injured']), 'pk': I(r['number_of_pedestrians_killed']),
               'ci': I(r['number_of_cyclist_injured']), 'ck': I(r['number_of_cyclist_killed']),
               'mi': I(r['number_of_motorist_injured']), 'mk': I(r['number_of_motorist_killed'])}
        pt = Point(float(r['longitude']), float(r['latitude']))
        for k2, v in rec.items(): city[y][k2] += v
        cd = locate(cd_tree, cd_polys, cd_keys, pt)
        cc = locate(cc_tree, cc_polys, cc_keys, pt)
        if cd is None: cd_locate_miss += 1
        else:
            for k2, v in rec.items(): by_cd[cd][y][k2] += v
        if cc is None: cc_locate_miss += 1
        else:
            for k2, v in rec.items(): by_cc[cc][y][k2] += v
        if cd == '306':
            a, b = norm_street(r['on_street_name']), norm_street(r['off_street_name'] or r['cross_street_name'])
            if a and b:
                key = ' & '.join(sorted([a, b]))
                e = cb6_int[key]
                for k2, v in rec.items(): e[k2] += v
                e['lat'] += pt.y; e['lng'] += pt.x; e['n'] += 1
            if rec['k'] > 0:
                mode = 'pedestrian' if rec['pk'] else ('cyclist' if rec['ck'] else 'motor vehicle occupant')
                cb6_fatal.append({'date': d, 'on': a, 'cross': b, 'k': rec['k'], 'mode': mode,
                                  'lat': round(pt.y, 6), 'lng': round(pt.x, 6)})
for fn in sorted(glob.glob('/home/claude/crash/nolat*.csv')):
    for r in csv.DictReader(open(fn)):
        y = r['crash_date'][:4]
        unmapped[y]['crashes'] += 1; unmapped[y]['inj'] += I(r['number_of_persons_injured']); unmapped[y]['k'] += I(r['number_of_persons_killed'])
print('mapped rows', n_rows, 'cd miss', cd_locate_miss, 'cc miss', cc_locate_miss, 'last crash', LAST_CRASH)

# ---------- speed limits by segment (miles by limit, Sammy's Law school zone segments) ----------
def seg_len_m(coords):
    t = 0.0
    for i in range(1, len(coords)):
        (x1, y1), (x2, y2) = coords[i-1], coords[i]
        dx = (x2 - x1) * 111320 * math.cos(math.radians((y1 + y2) / 2)); dy = (y2 - y1) * 110540
        t += math.hypot(dx, dy)
    return t
def geom_len_m(g):
    if g['type'] == 'LineString': return seg_len_m(g['coordinates'])
    return sum(seg_len_m(c) for c in g['coordinates'])
def bucket(sl):
    try: sl = int(sl)
    except: return 'other'
    if sl <= 15: return '15'
    if sl == 20: return '20'
    if sl == 25: return '25'
    if sl == 30: return '30'
    return '35plus'
sp_cd = collections.defaultdict(lambda: {'mi': collections.Counter(), 'sz': 0, 'segs': 0})
sp_cc = collections.defaultdict(lambda: {'mi': collections.Counter(), 'sz': 0, 'segs': 0})
seg_geoms, seg_names = [], []
for fn in sorted(glob.glob(os.path.join(ROOT, 'data', 'speed-limits', '*.json'))):
    if os.path.basename(fn) in ('schools.json', 'index.json'): continue
    g = json.load(open(fn))
    for f in g['features']:
        p = f['properties']; geom = f['geometry']
        L = geom_len_m(geom) / 1609.344
        b = bucket(p.get('sl'))
        e = sp_cd[p['borocd']]; e['mi'][b] += L; e['segs'] += 1; e['sz'] += 1 if p.get('sz') else 0
        sh = shape(geom); seg_geoms.append(sh); seg_names.append(p.get('street') or '')
        mid = sh.interpolate(0.5, normalized=True) if sh.geom_type == 'LineString' else sh.geoms[0].interpolate(0.5, normalized=True)
        cc = locate(cc_tree, cc_polys, cc_keys, mid)
        if cc:
            e = sp_cc[cc]; e['mi'][b] += L; e['segs'] += 1; e['sz'] += 1 if p.get('sz') else 0
seg_tree = STRtree(seg_geoms)
print('speed segments', len(seg_geoms))

def nearest_street(pt, exclude=None, maxd=0.0004):
    idx = seg_tree.query(pt.buffer(maxd))
    best, bd = None, 9
    for i in idx:
        nm = seg_names[i]
        if not nm or nm == exclude: continue
        d = seg_geoms[i].distance(pt)
        if d < bd: bd, best = d, nm
    return best

# ---------- VZV layers ----------
def load(id_): return json.load(open('/home/claude/vzv/%s.geojson' % id_))
def titlecase(s):
    s = (s or '').strip()
    small = {'and', 'of', 'the', 'at'}
    out = []
    for w in s.lower().split():
        out.append(w if w in small else w.capitalize())
    t = ' '.join(out)
    t = re.sub(r'\b(\d+)(St|Nd|Rd|Th)\b', lambda m: m.group(1) + m.group(2).lower(), t)
    return t

# priority corridors: clip to CDs and CCs, name by nearest segments
cor = load('36nr-7fbp')
corridors = []
cor_cd = collections.defaultdict(list); cor_cc = collections.defaultdict(list)
for i, f in enumerate(cor['features']):
    sh = shape(f['geometry'])
    lines = list(sh.geoms) if sh.geom_type == 'MultiLineString' else [sh]
    total_m = sum(seg_len_m(list(l.coords)) for l in lines)
    # name: sample along
    names = collections.Counter()
    merged = unary_union(lines)
    ml = list(merged.geoms) if merged.geom_type == 'MultiLineString' else [merged]
    samples = []
    for l in ml:
        n = max(2, int(l.length / 0.0015))
        for k in range(n + 1):
            samples.append(l.interpolate(k / n, normalized=True))
    for p in samples:
        nm = nearest_street(p, maxd=0.00015)
        if nm: names[nm] += 1
    street = names.most_common(1)[0][0] if names else 'Priority corridor'
    # extent: ends of the longest line
    longest = max(ml, key=lambda l: l.length)
    a = Point(longest.coords[0]); b = Point(longest.coords[-1])
    fa = nearest_street(a, exclude=street) or ''; fb = nearest_street(b, exclude=street) or ''
    rec = {'i': i, 'name': titlecase(street), 'from': titlecase(fa), 'to': titlecase(fb), 'mi': round(total_m / 1609.344, 2), 'cd': [], 'cc': []}
    for keys, polys, store, out in ((cd_keys, cd_polys, cor_cd, 'cd'), (cc_keys, cc_polys, cor_cc, 'cc')):
        tree = cd_tree if out == 'cd' else cc_tree
        for j in tree.query(sh):
            inter = polys[j].intersection(sh)
            if inter.is_empty: continue
            L = 0.0
            geoms = list(inter.geoms) if hasattr(inter, 'geoms') else [inter]
            for gg in geoms:
                if gg.geom_type == 'LineString': L += seg_len_m(list(gg.coords))
            mi = L / 1609.344
            if mi >= 0.05:
                rec[out].append({'k': keys[j], 'mi': round(mi, 2)})
                store[keys[j]].append(i)
    corridors.append(rec)
print('corridors', len(corridors))

def point_layer(id_, name_fn):
    g = load(id_)
    per_cd = collections.defaultdict(list); per_cc = collections.defaultdict(list)
    n = 0
    for f in g['features']:
        geom = f['geometry']
        if geom is None: continue
        if geom['type'] == 'Point': pts = [geom['coordinates']]
        else: pts = geom['coordinates']
        for c in pts:
            n += 1
            pt = Point(c[0], c[1])
            item = name_fn(f['properties'], pt)
            cd = locate(cd_tree, cd_polys, cd_keys, pt); cc = locate(cc_tree, cc_polys, cc_keys, pt)
            if cd: per_cd[cd].append(item)
            if cc: per_cc[cc].append(item)
    return n, per_cd, per_cc

def name_int(p, pt): return {'n': titlecase(p.get('street_1', '')) + ' & ' + titlecase(p.get('street_2', '')), 'lat': round(pt.y, 6), 'lng': round(pt.x, 6)}
n_int, int_cd, int_cc = point_layer('tmt9-43em', name_int)
def name_lpi(p, pt): return {'n': titlecase(p.get('main_street', '')) + ' & ' + titlecase(p.get('cross_stree', '')), 'y': (p.get('install_da') or '')[:4]}
n_lpi, lpi_cd, lpi_cc = point_layer('xc4v-ntf4', name_lpi)
def name_turn(p, pt): return {'t': p.get('treatment_', ''), 'y': (p.get('completion') or '')[:4]}
n_turn, turn_cd, turn_cc = point_layer('sm2x-35i7', name_turn)
def name_sip(p, pt): return {'n': p.get('pjct_name', ''), 'y': p.get('sip_year', '')}
n_sipi, sipi_cd, sipi_cc = point_layer('shr7-eqdc', name_sip)
def name_ec(p, pt): return {'y': (p.get('date_imple') or '')[:4]}
n_ec, ec_cd, ec_cc = point_layer('6ax4-q5k4', name_ec)
print('intersections', n_int, 'lpi', n_lpi, 'turn', n_turn, 'sip int', n_sipi, 'enhanced crossings', n_ec)

# speed humps: segments with hump counts; assign by midpoint
hump = load('jknp-skuy')
hump_cd = collections.Counter(); hump_cc = collections.Counter(); hump_total = 0
for f in hump['features']:
    if not f['geometry']: continue
    sh = shape(f['geometry'])
    line = sh if sh.geom_type == 'LineString' else max(sh.geoms, key=lambda l: l.length)
    mid = line.interpolate(0.5, normalized=True)
    h = int(float(f['properties'].get('humps') or 0)); hump_total += h
    cd = locate(cd_tree, cd_polys, cd_keys, mid); cc = locate(cc_tree, cc_polys, cc_keys, mid)
    if cd: hump_cd[cd] += h
    if cc: hump_cc[cc] += h
print('humps', hump_total)

# neighborhood slow zones: polygons, which CD/CC they overlap (share of zone area)
sz = load('bqye-aqft')
sz_cd = collections.defaultdict(list); sz_cc = collections.defaultdict(list)
for f in sz['features']:
    sh = shape(f['geometry']).buffer(0)
    nm = f['properties'].get('name', ''); yr = f['properties'].get('year', '')
    for keys, polys, tree, store in ((cd_keys, cd_polys, cd_tree, sz_cd), (cc_keys, cc_polys, cc_tree, sz_cc)):
        for j in tree.query(sh):
            inter = polys[j].intersection(sh)
            if inter.is_empty or inter.area / sh.area < 0.05: continue
            store[keys[j]].append({'n': nm, 'y': yr, 'share': round(inter.area / sh.area, 2)})
print('slow zones', len(sz['features']))

# SIP corridors: miles within CD/CC
sipc = load('if4c-w48d')
sipc_cd = collections.defaultdict(float); sipc_cc = collections.defaultdict(float); sipc_n_cd = collections.Counter(); sipc_n_cc = collections.Counter(); sipc_total_mi = 0.0
for f in sipc['features']:
    if not f['geometry']: continue
    sh = shape(f['geometry'])
    sipc_total_mi += geom_len_m(f['geometry']) / 1609.344
    for keys, polys, tree, store, cnt in ((cd_keys, cd_polys, cd_tree, sipc_cd, sipc_n_cd), (cc_keys, cc_polys, cc_tree, sipc_cc, sipc_n_cc)):
        for j in tree.query(sh):
            inter = polys[j].intersection(sh)
            if inter.is_empty: continue
            L = 0.0
            geoms = list(inter.geoms) if hasattr(inter, 'geoms') else [inter]
            for gg in geoms:
                if gg.geom_type == 'LineString': L += seg_len_m(list(gg.coords))
            if L > 30:
                store[keys[j]] += L / 1609.344; cnt[keys[j]] += 1
print('sip corridors', len(sipc['features']), round(sipc_total_mi, 1), 'mi')

# ---------- assemble ----------
cdlook = json.load(open(os.path.join(ROOT, 'data', 'cd-lookup.json')))
ccx = json.load(open(os.path.join(ROOT, 'data', 'cc-neighborhood-crosswalk.json')))
ccm = json.load(open(os.path.join(ROOT, 'data', 'council-members.json')))['members']

def sums(years, y0='2014', y1='2025'):
    t = blank()
    for y, v in years.items():
        if y0 <= y <= y1:
            for k in t: t[k] += v[k]
    return t

def pack_years(years):
    return {y: [v['crashes'], v['inj'], v['k'], v['pi'], v['pk'], v['ci'], v['ck'], v['mi'], v['mk']] for y, v in years.items()}

def district(kind, key):
    years = (by_cd if kind == 'cd' else by_cc).get(key, blank_years())
    spd = (sp_cd if kind == 'cd' else sp_cc).get(key, {'mi': collections.Counter(), 'sz': 0, 'segs': 0})
    ints = (int_cd if kind == 'cd' else int_cc).get(key, [])
    cors = [(corridors[i], next(x['mi'] for x in corridors[i][kind] if x['k'] == key)) for i in (cor_cd if kind == 'cd' else cor_cc).get(key, [])]
    lp = (lpi_cd if kind == 'cd' else lpi_cc).get(key, [])
    tc = (turn_cd if kind == 'cd' else turn_cc).get(key, [])
    si = (sipi_cd if kind == 'cd' else sipi_cc).get(key, [])
    ec = (ec_cd if kind == 'cd' else ec_cc).get(key, [])
    szs = (sz_cd if kind == 'cd' else sz_cc).get(key, [])
    total = sums(years)
    return {
        'years': pack_years(years),
        'tot': total,
        'assets': {
            'corridors': [{'name': c['name'], 'from': c['from'], 'to': c['to'], 'mi': mi, 'mi_total': c['mi']} for c, mi in sorted(cors, key=lambda x: -x[1])],
            'corridor_mi': round(sum(mi for _, mi in cors), 2),
            'intersections': sorted(ints, key=lambda x: x['n']),
            'lpi': len(lp),
            'lpi_by_year': dict(collections.Counter(x['y'] for x in lp)),
            'turn_calming': len(tc),
            'sip_intersections': len(si),
            'sip_corridor_mi': round((sipc_cd if kind == 'cd' else sipc_cc).get(key, 0.0), 2),
            'sip_corridors': (sipc_n_cd if kind == 'cd' else sipc_n_cc).get(key, 0),
            'enhanced_crossings': len(ec),
            'speed_humps': (hump_cd if kind == 'cd' else hump_cc).get(key, 0),
            'slow_zones': szs,
            'speed_mi': {k: round(v, 2) for k, v in spd['mi'].items()},
            'street_mi': round(sum(spd['mi'].values()), 2),
            'school_zone_segments': spd['sz'],
        }
    }

out = {'generated': datetime.date.today().isoformat(), 'last_crash': LAST_CRASH,
       'years': YEARS, 'cols': ['crashes', 'injured', 'killed', 'pedestrians injured', 'pedestrians killed', 'cyclists injured', 'cyclists killed', 'motorists injured', 'motorists killed'],
       'city': {'years': pack_years(city), 'tot': sums(city), 'unmapped': pack_years(unmapped), 'unmapped_tot': sums(unmapped),
                'assets': {'corridors': len(corridors), 'corridor_mi': round(sum(c['mi'] for c in corridors), 1), 'intersections': n_int, 'lpi': n_lpi, 'turn_calming': n_turn,
                           'sip_intersections': n_sipi, 'sip_corridors': len(sipc['features']), 'sip_corridor_mi': round(sipc_total_mi, 1), 'enhanced_crossings': n_ec,
                           'speed_humps': hump_total, 'slow_zones': len(sz['features']), 'speed_segments': len(seg_geoms),
                           'school_zone_segments': sum(v['sz'] for v in sp_cd.values())}},
       'cd': {}, 'cc': {}, 'jia': {}}
for k in cd_keys:
    lab = cd_label(k)
    d = district('cd', k)
    if is_cb(k):
        lk = cdlook.get(lab, {})
        d['label'] = lab; d['boro'] = BORONAME[k[0]]; d['num'] = int(k[1:]); d['borocd'] = k
        d['neighborhoods'] = ', '.join(lk.get('cn') or lk.get('se') or [])
        d['cc'] = [{'d': x['d'], 'share': x['share']} for x in lk.get('cc', [])]
        out['cd'][lab] = d
    else:
        d['label'] = lab; d['boro'] = BORONAME[k[0]]; d['borocd'] = k
        out['jia'][lab] = d
for k in cc_keys:
    d = district('cc', k)
    d['label'] = 'District ' + k; d['num'] = int(k); d['member'] = (ccm.get(k) or {}).get('name', '')
    d['neighborhoods'] = ', '.join(ccx.get(k, []))
    out['cc']['District ' + k] = d
json.dump(out, open(os.path.join(OUT, 'districts.json'), 'w'), separators=(',', ':'))

# CB6 places
ints = []
for k, e in cb6_int.items():
    ints.append({'n': k, 'crashes': e['crashes'], 'inj': e['inj'], 'k': e['k'], 'pi': e['pi'], 'pk': e['pk'], 'ci': e['ci'], 'ck': e['ck'], 'mi': e['mi'], 'mk': e['mk'],
                 'lat': round(e['lat'] / e['n'], 6), 'lng': round(e['lng'] / e['n'], 6)})
ints.sort(key=lambda x: (-(x['inj'] + 10 * x['k']), x['n']))
cb6_fatal.sort(key=lambda x: x['date'])
json.dump({'generated': out['generated'], 'last_crash': LAST_CRASH, 'intersections': ints, 'fatal': cb6_fatal,
           'note': 'NYPD Motor Vehicle Collisions - Crashes (h9gi-nx95), crashes with at least one person injured or killed, inside Brooklyn Community District 6 by crash coordinates, 2014-01-01 to ' + LAST_CRASH + '. Intersections are the on-street and cross-street NYPD recorded; crashes recorded with only an on-street or an off-street address are counted in the district totals but not in the intersection list.'},
          open(os.path.join(OUT, 'cb6-places.json'), 'w'), separators=(',', ':'))
# corridors geojson for the map (named)
fc = {'type': 'FeatureCollection', 'features': []}
for i, f in enumerate(cor['features']):
    c = corridors[i]
    fc['features'].append({'type': 'Feature', 'properties': {'i': i, 'name': c['name'], 'from': c['from'], 'to': c['to'], 'mi': c['mi'], 'cd': [x['k'] for x in c['cd']], 'cc': [x['k'] for x in c['cc']]}, 'geometry': f['geometry']})
json.dump(fc, open(os.path.join(OUT, 'priority-corridors.geojson'), 'w'), separators=(',', ':'))
ifc = {'type': 'FeatureCollection', 'features': []}
for f in load('tmt9-43em')['features']:
    p = f['properties']
    ifc['features'].append({'type': 'Feature', 'properties': {'n': titlecase(p.get('street_1', '')) + ' & ' + titlecase(p.get('street_2', ''))}, 'geometry': f['geometry']})
json.dump(ifc, open(os.path.join(OUT, 'priority-intersections.geojson'), 'w'), separators=(',', ':'))

# sanity
tot_cd = sum(sum(v['crashes'] for v in d.values()) for d in by_cd.values())
print('city mapped crashes', sum(v['crashes'] for v in city.values()), 'assigned to a CD or JIA', tot_cd, 'cd miss', cd_locate_miss)
print('CB6 2014-2025', out['cd']['BKCB6']['tot'])
print('CB6 assets', json.dumps({k: v for k, v in out['cd']['BKCB6']['assets'].items() if k not in ('intersections', 'corridors')}))
print('CB6 corridors', json.dumps(out['cd']['BKCB6']['assets']['corridors']))
print('CB6 intersections', json.dumps(out['cd']['BKCB6']['assets']['intersections']))
print('CB6 slow zones', out['cd']['BKCB6']['assets']['slow_zones'])
print('CC39', out['cc']['District 39']['tot'], out['cc']['District 39']['assets']['corridor_mi'])
