"""Every block of Bergen Street and Dean Street (Court St to East New York Ave), with what is on it.
Writes data/bergendean/blocks.json.

A block is the street centerline between two intersections in the NYC Street Centerline (CSCL, inkn-q76z).
CSCL segments that meet at a point where no other street comes in are joined into one block.
Districts: the block's midpoint is checked against the same district files the corridor page uses; a block
whose two ends fall in different districts lists both.
Truck routes, bike lanes, speed limits, bus routes, bus stops, subway stations and Citi Bike come from the
files the corridor map draws (data/bergendean/layers.json, data/truck-routes/*.json).
Crashes come from the corridor's crash points (data/bergendean/points.json, NYPD h9gi-nx95).
311 requests are fetched here for the whole corridor (erm2-nwe9) and counted within 100 ft of each block."""
import json, os, re, urllib.request, urllib.parse, collections, datetime
from zoneinfo import ZoneInfo
from shapely.geometry import shape, mapping, Point, LineString, MultiLineString
from shapely.ops import unary_union, linemerge, transform
from pyproj import Transformer, Geod
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'bergendean')
NYC = 'https://data.cityofnewyork.us/resource/'
TO = Transformer.from_crs(4326, 2263, always_xy=True); BACK = Transformer.from_crs(2263, 4326, always_xy=True)
P = lambda g: transform(lambda x, y, z=None: TO.transform(x, y), g); U = lambda g: transform(lambda x, y, z=None: BACK.transform(x, y), g)
G = Geod(ellps='WGS84')
def url(ds, q): return NYC + ds + '.json?' + urllib.parse.urlencode(q)
def get(u): return json.load(urllib.request.urlopen(u, timeout=600))
S = json.load(open(os.path.join(OUT, 'summary.json'))); LAY = json.load(open(os.path.join(OUT, 'layers.json'))); PTS = json.load(open(os.path.join(OUT, 'points.json')))
END = S.get('end') or (datetime.datetime.now(ZoneInfo('America/New_York')).date().isoformat() + 'T00:00:00')
STREETS = {'BERGEN ST': 'Bergen St', 'DEAN ST': 'Dean St'}
FIELDS = 'physicalid,full_street_name,the_geom,l_low_hn,l_high_hn,r_low_hn,r_high_hn,l_zip,bike_lane,posted_speed,streetwidth,number_travel_lanes,number_park_lanes,trafdir,rw_type,segmentlength'
# ---- corridor segments
segs = []
for nm in STREETS:
    u = url('inkn-q76z', {'$select': FIELDS, '$where': f"full_street_name='{nm}' AND boroughcode='3'", '$limit': 5000})
    for r in get(u):
        g = shape(r['the_geom']); g = linemerge(g) if g.geom_type == 'MultiLineString' else g
        if g.geom_type != 'LineString': g = max(g.geoms, key=lambda x: x.length)
        r['g'] = g; r['street'] = nm; segs.append(r)
CSCL_Q = url('inkn-q76z', {'$select': FIELDS, '$where': "(full_street_name='BERGEN ST' OR full_street_name='DEAN ST') AND boroughcode='3'", '$limit': 5000})
print('segments', len(segs))
# ---- every other street near the corridor, to name the cross streets at each node
allg = unary_union([s['g'] for s in segs]); b = allg.bounds
u = url('inkn-q76z', {'$select': 'physicalid,full_street_name,the_geom,rw_type', '$where': f"boroughcode='3' AND within_box(the_geom,{b[3] + .003},{b[0] - .003},{b[1] - .003},{b[2] + .003})", '$limit': 100000})
others = get(u); print('nearby segments', len(others))
def key(c): return (round(c[0], 5), round(c[1], 5))
node = collections.defaultdict(set)
for r in others:
    if r['full_street_name'] in STREETS or r.get('rw_type') in ('5', '6', '7', '8', '12', '13', '14'): continue
    g = shape(r['the_geom'])
    for ln in getattr(g, 'geoms', [g]):
        cs = list(ln.coords); node[key(cs[0])].add(r['full_street_name']); node[key(cs[-1])].add(r['full_street_name'])
# ---- join segments into blocks
def fmt(n):
    n = n.strip()
    m = re.match(r'^(\d+)\s+(AVE|ST|PL)$', n)
    if m:
        d = int(m.group(1)); suf = 'th' if 10 <= d % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')
        n = f'{d}{suf} {m.group(2)}'
    w = {'AVE': 'Ave', 'ST': 'St', 'PL': 'Pl', 'BLVD': 'Blvd', 'PKWY': 'Pkwy', 'RD': 'Rd', 'DR': 'Dr', 'CT': 'Ct', 'LN': 'Ln', 'TER': 'Ter', 'SQ': 'Sq', 'EXPY': 'Expy', 'HWY': 'Hwy', 'PK': 'Pk', 'E': 'E', 'W': 'W', 'N': 'N', 'S': 'S'}
    return ' '.join(w.get(x, x if x[0].isdigit() else x.title()) for x in n.split())
def cross(k, own): return sorted(n for n in node.get(k, ()) if n != own)
blocks = []
for nm in STREETS:
    ss = [s for s in segs if s['street'] == nm]
    # adjacency by shared endpoint
    byk = collections.defaultdict(list)
    for i, s in enumerate(ss):
        cs = list(s['g'].coords); byk[key(cs[0])].append(i); byk[key(cs[-1])].append(i)
    used = set()
    for i, s in enumerate(ss):
        if i in used: continue
        run = [i]; used.add(i)
        # extend both ways through nodes where no other street comes in
        for side in (0, -1):
            cur = i; k = key(list(ss[cur]['g'].coords)[side])
            while not cross(k, nm):
                nxt = [j for j in byk[k] if j not in used]
                if len(nxt) != 1: break
                j = nxt[0]; used.add(j); run.append(j)
                cj = list(ss[j]['g'].coords); k = key(cj[-1]) if key(cj[0]) == k else key(cj[0]); cur = j
        g = unary_union([ss[j]['g'] for j in run])
        if g.geom_type != 'LineString': g = linemerge(g)
        if g.geom_type != 'LineString': g = max(g.geoms, key=lambda x: x.length)
        cs = list(g.coords); e0, e1 = key(cs[0]), key(cs[-1])
        if cs[0][0] > cs[-1][0]: cs = cs[::-1]; e0, e1 = e1, e0; g = LineString(cs)
        parts = [ss[j] for j in run]
        hn = [int(x) for p in parts for x in (p.get('l_low_hn'), p.get('l_high_hn'), p.get('r_low_hn'), p.get('r_high_hn')) if x and x.isdigit()]
        blocks.append({'street': STREETS[nm], 'sk': 'bergen' if nm == 'BERGEN ST' else 'dean', 'from': [fmt(x) for x in cross(e0, nm)], 'to': [fmt(x) for x in cross(e1, nm)], 'g': g,
                       'ft': round(G.geometry_length(g) * 3.28084), 'hn': [min(hn), max(hn)] if hn else None, 'zip': sorted(set(p.get('l_zip') for p in parts if p.get('l_zip'))),
                       'cscl': {'ids': [p['physicalid'] for p in parts], 'posted_speed': sorted(set(p.get('posted_speed') for p in parts if p.get('posted_speed'))), 'bike_lane': sorted(set(p.get('bike_lane') for p in parts if p.get('bike_lane'))),
                                'width_ft': sorted(set(p.get('streetwidth') for p in parts if p.get('streetwidth'))), 'travel_lanes': sorted(set(p.get('number_travel_lanes') for p in parts if p.get('number_travel_lanes'))),
                                'park_lanes': sorted(set(p.get('number_park_lanes') for p in parts if p.get('number_park_lanes'))), 'trafdir': sorted(set(p.get('trafdir') for p in parts if p.get('trafdir')))}})
blocks.sort(key=lambda b: (b['sk'], b['g'].coords[0][0]))
blocks = [b for b in blocks if b['ft'] > 0 and not (b['from'] == b['to'] and b['ft'] < 100)]  # drop the short pieces inside a divided intersection (4th Ave has two roadbeds)
for n, b in enumerate(blocks): b['id'] = n
print('blocks', collections.Counter(b['sk'] for b in blocks))
# ---- districts
FILES = [('cd', 'data/community-districts.geojson', 'boro_cd'), ('council', 'data/council-districts.geojson', 'cc'), ('assembly', 'data/assembly-districts.geojson', 'ad'), ('senate', 'data/senate-districts.geojson', 'sd'), ('congress', 'data/congress-districts-simple.geojson', 'cong_dist'), ('precinct', 'data/police-precincts-citywide.geojson', 'precinct')]
DPOLY = {k: [(str(int(float(x['properties'][p]))), shape(x['geometry']).buffer(0)) for x in json.load(open(os.path.join(ROOT, f)))['features']] for k, f, p in FILES}
def dist_at(k, pt): return [i for i, g in DPOLY[k] if g.contains(pt)]
for b in blocks:
    g = b['g']; mid = g.interpolate(0.5, normalized=True); b['mid'] = [round(mid.y, 6), round(mid.x, 6)]
    b['d'] = {}
    for k, _, _ in FILES:
        own = dist_at(k, mid); ends = set(dist_at(k, g.interpolate(0.02, normalized=True)) + dist_at(k, g.interpolate(0.98, normalized=True)))
        b['d'][k] = {'main': own[0] if own else None, 'also': sorted(ends - set(own))}
# ---- what is on the block (from the map's own files)
BP = {b['id']: P(b['g']) for b in blocks}
def share(feat_geoms, bp, width=30):
    """fraction of the block's length that lies within `width` ft of the feature"""
    if not feat_geoms: return 0
    u = unary_union(feat_geoms).buffer(width)
    return bp.intersection(u).length / bp.length if bp.length else 0
# truck routes
TR = []
for cd in S['trucks']['cds']:
    fp = os.path.join(ROOT, 'data', 'truck-routes', cd + '.json')
    if os.path.exists(fp):
        for f in json.load(open(fp))['features']:
            if f.get('geometry') and f['properties'].get('street') in ('BERGEN STREET', 'DEAN STREET'): TR.append((f['properties'].get('routetype'), P(shape(f['geometry']))))
BIKE = [(f['properties'], P(shape(f['geometry']))) for f in LAY['bike']['features']]
SPEED = [(f['properties'], P(shape(f['geometry']))) for f in LAY['speed']['features']]
BUSR = [(f['properties']['r'], P(shape(f['geometry']))) for f in LAY['bus_routes']['features']]
STOPS = [(s, P(Point(s[1], s[0]))) for s in LAY['bus_stops']]
SUBS = [(s, P(Point(s[1], s[0]))) for s in LAY['subway_stops']]
CITI = [(s, P(Point(s[1], s[0]))) for s in LAY['citibike']]
CUT = P(shape(LAY['b65_cut']))
CR = [(c, P(Point(c[1], c[0]))) for c in PTS['crashes']]
# 311 for the whole corridor, once
s311 = []; seen = set()
for k in ('bergen', 'dean'):
    u = url('erm2-nwe9', {'$select': 'unique_key,latitude,longitude,complaint_type,created_date', '$where': f"created_date>='2020-01-01T00:00:00' AND created_date<'{END}' AND within_polygon(location,'{S['wkt'][k]}')", '$limit': 200000})
    for r in get(u):
        if r['unique_key'] in seen or not r.get('latitude'): continue
        seen.add(r['unique_key']); s311.append((r['complaint_type'], P(Point(float(r['longitude']), float(r['latitude']))), r['created_date'][:7]))
print('311 points', len(s311))
def wkt(poly):
    parts = [q for q in getattr(poly, 'geoms', [poly]) if q.geom_type == 'Polygon']
    return 'MULTIPOLYGON(' + ','.join('((' + ','.join('%.6f %.6f' % c for c in q.exterior.coords) + '))' for q in parts) + ')'
for b in blocks:
    bp = BP[b['id']]; buf = bp.buffer(100); ubuf = U(buf).simplify(0.00003, preserve_topology=True); b['wkt'] = wkt(ubuf)
    tr = [t for t, g in TR if bp.intersection(g.buffer(30)).length / bp.length > 0.4]
    b['truck'] = sorted(set(tr))
    bk = [(pr, bp.intersection(g.buffer(30)).length / bp.length) for pr, g in BIKE]
    bk = [(pr, s) for pr, s in bk if s > 0.4]
    b['bike'] = sorted(set(f"Class {pr.get('cl')}: {pr.get('ty')}" for pr, s in bk)) if bk else []
    sp = collections.Counter()
    for pr, g in SPEED:
        s = bp.intersection(g.buffer(30)).length / bp.length
        if s > 0.4 and pr.get('sl'): sp[str(pr['sl'])] += s
    b['speed'] = [k for k, _ in sp.most_common()]
    b['bus'] = sorted(set(r for r, g in BUSR if bp.intersection(g.buffer(30)).length / bp.length > 0.5))
    b['stops'] = [[s[2], s[3]] for s, g in STOPS if g.distance(bp) < 60]
    sub = sorted([(round(g.distance(bp)), s[2], s[3]) for s, g in SUBS if g.distance(bp) < 1500])
    b['subway'] = [[d, n, r] for d, n, r in sub[:3]]
    b['citi'] = [[round(g.distance(bp)), s[2], s[3]] for s, g in CITI if g.distance(bp) < 500]
    b['b65cut'] = bp.intersection(CUT.buffer(30)).length / bp.length > 0.5
# each crash and 311 request counts once, on the nearest block (within 100 ft of it)
from shapely.strtree import STRtree
blk_lines = [BP[b['id']] for b in blocks]; tree = STRtree(blk_lines)
def nearest_block(pt):
    i = int(tree.nearest(pt)); return i if blk_lines[i].distance(pt) <= 100 else None
crs = collections.defaultdict(list); t3s = collections.defaultdict(collections.Counter)
for c, g in CR:
    i = nearest_block(g)
    if i is not None: crs[i].append(c)
t3m = collections.defaultdict(collections.Counter); crm = collections.defaultdict(collections.Counter)
for t, g, m in s311:
    i = nearest_block(g)
    if i is not None: t3s[i][t] += 1; t3m[i][m] += 1
for c, g in CR:
    i = nearest_block(g)
    if i is not None: crm[i][c[2][:7]] += 1
CM = sorted(set(m for v in crm.values() for m in v)); SM = sorted(set(m for v in t3m.values() for m in v))
for b in blocks:
    cr = crs[b['id']]
    b['crash'] = {'n': len(cr), 'inj': sum(c[5] for c in cr), 'kil': sum(c[6] for c in cr), 'cyc': sum(c[7] for c in cr), 'ped': sum(c[8] for c in cr)}
    t3 = t3s[b['id']]
    b['s311'] = {'n': sum(t3.values()), 'top': t3.most_common(3), 'types': t3.most_common(12), 'months': [t3m[b['id']].get(m, 0) for m in SM]}
    b['crash']['months'] = [crm[b['id']].get(m, 0) for m in CM]
    cy = collections.Counter(c[2][:4] for c in cr); b['crash']['years'] = dict(cy)
    b['crash']['cyc_years'] = {y: sum(c[7] for c in cr if c[2][:4] == y) for y in cy}
    sy = collections.Counter(m[:4] for m, n in t3m[b['id']].items() for _ in range(n)); b['s311']['years'] = dict(sy)
# ---- totals
tot = {'blocks': len(blocks), 'by_street': dict(collections.Counter(b['sk'] for b in blocks)), 'districts': {}}
for k, _, _ in FILES:
    c = collections.Counter(b['d'][k]['main'] for b in blocks); cb = collections.Counter((b['sk'], b['d'][k]['main']) for b in blocks)
    tot['districts'][k] = {i: {'n': n, 'pct': round(100 * n / len(blocks), 1), 'bergen': cb[('bergen', i)], 'dean': cb[('dean', i)], 'ft': sum(b['ft'] for b in blocks if b['d'][k]['main'] == i)} for i, n in c.most_common()}
tot['truck'] = {'n': sum(1 for b in blocks if b['truck']), 'ft': sum(b['ft'] for b in blocks if b['truck'])}
tot['bike'] = {'n': sum(1 for b in blocks if b['bike']), 'ft': sum(b['ft'] for b in blocks if b['bike']), 'by': dict(collections.Counter(x for b in blocks for x in b['bike']))}
tot['speed'] = dict(collections.Counter(b['speed'][0] if b['speed'] else 'not in the DOT file' for b in blocks))
tot['bus'] = {'n': sum(1 for b in blocks if b['bus']), 'by': dict(collections.Counter(r for b in blocks for r in b['bus']))}
tot['stops'] = sum(len(b['stops']) for b in blocks)
tot['b65cut'] = sum(1 for b in blocks if b['b65cut'])
tot['crash'] = {'n': sum(b['crash']['n'] for b in blocks), 'zero': sum(1 for b in blocks if b['crash']['n'] == 0)}
tot['s311'] = {'n': sum(b['s311']['n'] for b in blocks), 'zero': sum(1 for b in blocks if b['s311']['n'] == 0)}
tot['ft'] = sum(b['ft'] for b in blocks)
out = {'built': END[:10], 'crash_months': CM, 's311_months': SM, 'cscl_query': CSCL_Q, 'crash_last': S['crash_last'], 's311_last': S['s311_last'], 'totals': tot,
       'blocks': [{k: v for k, v in b.items() if k != 'g'} for b in blocks],
       'geo': {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'id': b['id']}, 'geometry': json.loads(json.dumps(mapping(b['g'].simplify(0.00001))), parse_float=lambda s: round(float(s), 6))} for b in blocks]}}
json.dump(out, open(os.path.join(OUT, 'blocks.json'), 'w'), separators=(',', ':'))
print(json.dumps(tot)[:1500])
print(os.path.getsize(os.path.join(OUT, 'blocks.json')))
for b in blocks[:3] + blocks[-2:]: print(b['street'], b['from'], b['to'], b['ft'], b['d']['cd'], b['truck'], b['bike'], b['speed'], b['bus'], b['crash'], b['s311'])
