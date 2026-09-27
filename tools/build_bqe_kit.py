#!/usr/bin/env python3
"""Block-level data for the BQE pages (bkcb6.app/BQE/ and /BQE/carrollgardens-gowanus/).

Every street block inside Community District 6 (NYC Street Centerline, inkn-q76z, roadway type 1), split at cross
streets, with: neighborhood (bkcb6.app city-neighborhoods outlines), districts at its midpoint, truck route status
(NYC DOT truck routes, repo per-district files), speed limit, bike lanes, bus routes and stops, nearby subway and
Citi Bike; and, by month since January 2013, everything within 100 ft of it, each record counted once on its nearest
block: NYPD crashes (all, and those involving a truck), 311 requests (all, and "Truck Route Violation"), and NYPD
truck route (VTL 413) and size or weight (VTL 385) summonses.

Writes data/bqe/kit/layers.json, blocks.json and ts.json."""
import json, os, re, csv, urllib.request, urllib.parse, collections, datetime, time
from shapely.geometry import shape, mapping, Point, LineString, box
from shapely.ops import unary_union, linemerge, transform
from shapely.strtree import STRtree
from shapely import wkt as shwkt
import shapely
from pyproj import Transformer, Geod
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'bqe', 'kit'); os.makedirs(OUT, exist_ok=True)
NYC = 'https://data.cityofnewyork.us/resource/'; NYS = 'https://data.ny.gov/resource/'
TO = Transformer.from_crs(4326, 2263, always_xy=True); BACK = Transformer.from_crs(2263, 4326, always_xy=True)
P = lambda g: transform(lambda x, y, z=None: TO.transform(x, y), g); U = lambda g: transform(lambda x, y, z=None: BACK.transform(x, y), g)
G = Geod(ellps='WGS84')
def url(base, ds, q): return base + ds + '.json?' + urllib.parse.urlencode(q)
def get(u):
    for i in range(4):
        try: return json.load(urllib.request.urlopen(u, timeout=900))
        except Exception as e: err = e; time.sleep(6)
    raise err
def rnd(g, n=5): return json.loads(json.dumps(mapping(shapely.set_precision(g, 10 ** -n))))
def wkt(poly):
    parts = [q for q in getattr(poly, 'geoms', [poly]) if q.geom_type == 'Polygon']
    return 'MULTIPOLYGON(' + ','.join('((' + ','.join('%.6f %.6f' % c for c in q.exterior.coords) + '))' for q in parts) + ')'
END = datetime.datetime.now(datetime.timezone.utc).date().isoformat() + 'T00:00:00'
START = '2013-01-01T00:00:00'
# ---- the area: CD 6
CB6 = [shape(f['geometry']).buffer(0) for f in json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features'] if str(f['properties']['cd']) == '306'][0]
CB6 = CB6 if CB6.geom_type == 'Polygon' else max(CB6.geoms, key=lambda g: g.area)
AREA = CB6.buffer(0.004); bx = AREA.bounds
NBS = [(f['properties']['nb'], shape(f['geometry']).buffer(0)) for f in json.load(open(os.path.join(ROOT, 'data', 'city-neighborhoods.geojson')))['features'] if f['properties'].get('boro') == 'Brooklyn' and shape(f['geometry']).buffer(0).intersects(CB6)]
print('neighborhoods', [n for n, _ in NBS])
# ================================================================== layers
layers = {}
stops = get(url(NYS, '2ucp-7wg5', {'$select': 'stop_id,stop_name,route_short_name,latitude,longitude', '$where': f"in_effect='true' AND revenue_stop='1' AND latitude between {bx[1]} and {bx[3]} AND longitude between {bx[0]} and {bx[2]}", '$limit': 50000}))
S = {}
for r in stops:
    p = Point(float(r['longitude']), float(r['latitude']))
    if not AREA.contains(p): continue
    s = S.setdefault(r['stop_id'], {'n': r['stop_name'], 'll': [round(float(r['latitude']), 6), round(float(r['longitude']), 6)], 'r': set()}); s['r'].add(r['route_short_name'])
layers['bus_stops'] = [[v['ll'][0], v['ll'][1], v['n'], sorted(v['r'])] for v in S.values()]
routes_here = sorted(set(r for v in S.values() for r in v['r']))
rs = get(url(NYS, 'bzwk-3hb4', {'$select': 'route_short_name,route_color,direction_id,shape_id,vertices,geometry', '$where': "in_effect='true' AND route_short_name in(" + ','.join("'%s'" % r for r in routes_here) + ")", '$limit': 5000}))
best = {}
for r in rs:
    k = (r['route_short_name'], r['direction_id'])
    if k not in best or int(float(r['vertices'])) > int(float(best[k]['vertices'])): best[k] = r
byroute = {}
for (rt, d), r in sorted(best.items()): byroute.setdefault(rt, []).append(r)
layers['bus_routes'] = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'r': rt, 'c': '#' + (rr[0].get('route_color') or '0d1b4b')}, 'geometry': rnd(g)} for rt, rr in sorted(byroute.items()) for g in [unary_union([shape(r['geometry']) for r in rr]).intersection(AREA)] if not g.is_empty]}
sub = json.load(open(os.path.join(ROOT, 'data', 'nyc-subway-routes.geojson')))
layers['subway_lines'] = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'n': f['properties'].get('name'), 'c': f['properties'].get('color')}, 'geometry': rnd(shape(f['geometry']).intersection(AREA))} for f in sub['features'] if f.get('geometry') and shape(f['geometry']).intersects(AREA)]}
st = json.load(open(os.path.join(ROOT, 'data', 'nyc-subway-stations.geojson')))
layers['subway_stops'] = [[round(f['geometry']['coordinates'][1], 6), round(f['geometry']['coordinates'][0], 6), f['properties'].get('display_name') or f['properties'].get('stop_name'), f['properties'].get('daytime_routes') or f['properties'].get('routes'), f['properties'].get('ada')] for f in st['features'] if AREA.contains(Point(f['geometry']['coordinates'][:2]))]
BIKECSV = os.path.join(ROOT, 'data', 'bergendean', 'bike_routes_2026-09-27.csv')
bf = []
with open(BIKECSV) as f:
    for r in csv.DictReader(f):
        if r['status'] != 'Current' or r['boro'] != '3' or not r['the_geom']: continue
        g = shwkt.loads(r['the_geom'])
        if not g.intersects(AREA): continue
        types = sorted(set(t for t in (r['ft_facilit'], r['tf_facilit']) if t))
        bf.append({'type': 'Feature', 'properties': {'s': r['street'], 'f': r['fromstreet'], 't': r['tostreet'], 'cl': r['facilitycl'], 'ty': ' / '.join(types), 'd': r['instdate']}, 'geometry': rnd(g.intersection(AREA))})
layers['bike'] = {'type': 'FeatureCollection', 'features': bf}
layers['bike_query'] = 'https://data.cityofnewyork.us/Transportation/New-York-City-Bike-Routes/mzxg-pwib'
sf = []
for cd in ('302', '306', '307', '308', '355'):
    fp = os.path.join(ROOT, 'data', 'speed-limits', cd + '.json')
    if not os.path.exists(fp): continue
    for f in json.load(open(fp))['features']:
        g = shape(f['geometry'])
        if g.intersects(AREA): sf.append({'type': 'Feature', 'properties': {'s': f['properties'].get('street'), 'sl': f['properties'].get('sl'), 'sz': f['properties'].get('sz')}, 'geometry': rnd(g.intersection(AREA))})
layers['speed'] = {'type': 'FeatureCollection', 'features': sf}
cb = json.load(open(os.path.join(ROOT, 'data', 'citibike_station_information.json')))
layers['citibike'] = [[round(s['lat'], 6), round(s['lon'], 6), s['name'], s.get('capacity')] for s in cb['data']['stations'] if AREA.contains(Point(s['lon'], s['lat']))]
layers['citibike_updated'] = cb.get('last_updated')
DF = [('cd', 'data/community-districts.geojson', 'boro_cd'), ('council', 'data/council-districts.geojson', 'cc'), ('assembly', 'data/assembly-districts.geojson', 'ad'), ('senate', 'data/senate-districts.geojson', 'sd'), ('congress', 'data/congress-districts-simple.geojson', 'cong_dist'), ('precinct', 'data/police-precincts-citywide.geojson', 'precinct')]
DPOLY = {}
dfe = []
for k, f, pk in DF:
    DPOLY[k] = []
    for x in json.load(open(os.path.join(ROOT, f)))['features']:
        g = shape(x['geometry']).buffer(0); i = str(int(float(x['properties'][pk])))
        DPOLY[k].append((i, g))
        gi = g.intersection(AREA.buffer(0.004))
        if not gi.is_empty: dfe.append({'type': 'Feature', 'properties': {'k': k, 'id': i}, 'geometry': rnd(gi.simplify(0.00005))})
layers['districts'] = {'type': 'FeatureCollection', 'features': dfe}
layers['neighborhoods'] = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'nb': n}, 'geometry': rnd(g.simplify(0.00003))} for n, g in NBS]}
json.dump(layers, open(os.path.join(OUT, 'layers.json'), 'w'), separators=(',', ':'))
print('layers', {k: (len(v['features']) if isinstance(v, dict) and 'features' in v else len(v) if isinstance(v, list) else v) for k, v in layers.items() if k != 'bike_query'}, os.path.getsize(os.path.join(OUT, 'layers.json')) // 1024, 'KB')
# ================================================================== blocks
FIELDS = 'physicalid,full_street_name,the_geom,l_low_hn,l_high_hn,r_low_hn,r_high_hn,l_zip,posted_speed,streetwidth,number_travel_lanes,number_park_lanes,trafdir,rw_type'
W6 = wkt(CB6.simplify(0.00002, preserve_topology=True))
CSCL_Q = url(NYC, 'inkn-q76z', {'$select': FIELDS, '$where': f"rw_type='1' AND within_polygon(the_geom,'{W6}')", '$limit': 50000})
segs = get(CSCL_Q)
others = get(url(NYC, 'inkn-q76z', {'$select': 'full_street_name,the_geom,rw_type', '$where': f"within_box(the_geom,{bx[3]},{bx[0]},{bx[1]},{bx[2]})", '$limit': 100000}))
print('segments', len(segs), 'nearby', len(others))
def key(c): return (round(c[0], 5), round(c[1], 5))
node = collections.defaultdict(set)
for r in others:
    if r.get('rw_type') in ('5', '6', '7', '8', '12', '13', '14'): continue
    g = shape(r['the_geom'])
    for ln in getattr(g, 'geoms', [g]):
        cs = list(ln.coords); node[key(cs[0])].add(r['full_street_name']); node[key(cs[-1])].add(r['full_street_name'])
def fmtn(n):
    n = re.sub(r'\s+', ' ', n.strip())
    m = re.match(r'^(N |S |E |W )?(\d+)\s+(AVE|ST|PL)$', n)
    if m:
        d = int(m.group(2)); suf = 'th' if 10 <= d % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')
        n = (m.group(1) or '') + f'{d}{suf} {m.group(3)}'
    w = {'AVE': 'Ave', 'ST': 'St', 'PL': 'Pl', 'BLVD': 'Blvd', 'PKWY': 'Pkwy', 'RD': 'Rd', 'DR': 'Dr', 'CT': 'Ct', 'LN': 'Ln', 'TER': 'Ter', 'SQ': 'Sq', 'EXPY': 'Expy', 'HWY': 'Hwy', 'PK': 'Pk', 'N': 'N', 'S': 'S', 'E': 'E', 'W': 'W', 'SVC': 'Svc', 'ROAD': 'Rd'}
    return ' '.join(w.get(x, x if x[0].isdigit() else x.title()) for x in n.split())
for r in segs:
    g = shape(r['the_geom']); g = linemerge(g) if g.geom_type == 'MultiLineString' else g
    if g.geom_type != 'LineString': g = max(g.geoms, key=lambda x: x.length)
    r['g'] = g
bystreet = collections.defaultdict(list)
for r in segs: bystreet[r['full_street_name']].append(r)
blocks = []
for nm, ss in bystreet.items():
    byk = collections.defaultdict(list)
    for i, s in enumerate(ss):
        cs = list(s['g'].coords); byk[key(cs[0])].append(i); byk[key(cs[-1])].append(i)
    def cross(k): return sorted(n for n in node.get(k, ()) if n != nm)
    used = set()
    for i, s in enumerate(ss):
        if i in used: continue
        run = [i]; used.add(i)
        for side in (0, -1):
            k = key(list(ss[i]['g'].coords)[side])
            while not cross(k):
                nxt = [j for j in byk[k] if j not in used]
                if len(nxt) != 1: break
                j = nxt[0]; used.add(j); run.append(j)
                cj = list(ss[j]['g'].coords); k = key(cj[-1]) if key(cj[0]) == k else key(cj[0])
        g = unary_union([ss[j]['g'] for j in run])
        if g.geom_type != 'LineString': g = linemerge(g)
        if g.geom_type != 'LineString': g = max(g.geoms, key=lambda x: x.length)
        cs = list(g.coords); e0, e1 = key(cs[0]), key(cs[-1])
        parts = [ss[j] for j in run]
        hn = [int(x) for p in parts for x in (p.get('l_low_hn'), p.get('l_high_hn'), p.get('r_low_hn'), p.get('r_high_hn')) if x and x.isdigit()]
        ft = round(G.geometry_length(g) * 3.28084)
        fr, to = [fmtn(x) for x in cross(e0)], [fmtn(x) for x in cross(e1)]
        if ft < 60 and fr == to: continue
        blocks.append({'street': fmtn(nm), 'sn': nm, 'from': fr, 'to': to, 'g': g, 'ft': ft, 'hn': [min(hn), max(hn)] if hn else None,
                       'cscl': {'speed': sorted(set(p.get('posted_speed') for p in parts if p.get('posted_speed'))), 'width': sorted(set(p.get('streetwidth') for p in parts if p.get('streetwidth'))),
                                'lanes': sorted(set(p.get('number_travel_lanes') for p in parts if p.get('number_travel_lanes'))), 'park': sorted(set(p.get('number_park_lanes') for p in parts if p.get('number_park_lanes'))),
                                'dir': sorted(set(p.get('trafdir') for p in parts if p.get('trafdir')))}})
# order: by street name, then west to east / south to north
blocks.sort(key=lambda b: (b['street'], round(b['g'].coords[0][0], 4) if abs(b['g'].coords[-1][0] - b['g'].coords[0][0]) > abs(b['g'].coords[-1][1] - b['g'].coords[0][1]) else round(b['g'].coords[0][1], 4)))
for n, b in enumerate(blocks): b['id'] = n
print('blocks', len(blocks), 'streets', len(set(b['street'] for b in blocks)))
BP = [P(b['g']) for b in blocks]; tree = STRtree(BP)
def nearest(lon, lat, maxft=100):
    pt = P(Point(lon, lat)); i = int(tree.nearest(pt)); return i if BP[i].distance(pt) <= maxft else None
# attributes
TR = []
for cd in ('302', '306', '307', '308', '355'):
    fp = os.path.join(ROOT, 'data', 'truck-routes', cd + '.json')
    if os.path.exists(fp):
        for f in json.load(open(fp))['features']:
            if f.get('geometry'): TR.append((f['properties'].get('routetype'), f['properties'].get('street'), P(shape(f['geometry']))))
def share(g, bp, w=30): return bp.intersection(g.buffer(w)).length / bp.length if bp.length else 0
BIKE = [(f['properties'], P(shape(f['geometry']))) for f in layers['bike']['features']]
SPEED = [(f['properties'], P(shape(f['geometry']))) for f in layers['speed']['features']]
BUSR = [(f['properties']['r'], P(shape(f['geometry']))) for f in layers['bus_routes']['features']]
STOPS = [(s, P(Point(s[1], s[0]))) for s in layers['bus_stops']]
SUBS = [(s, P(Point(s[1], s[0]))) for s in layers['subway_stops']]
CITI = [(s, P(Point(s[1], s[0]))) for s in layers['citibike']]
trtree = STRtree([g for _, _, g in TR]); bktree = STRtree([g for _, g in BIKE]) if BIKE else None; sptree = STRtree([g for _, g in SPEED]) if SPEED else None; bstree = STRtree([g for _, g in BUSR]) if BUSR else None
for b in blocks:
    bp = BP[b['id']]; g = b['g']; mid = g.interpolate(0.5, normalized=True); b['mid'] = [round(mid.y, 6), round(mid.x, 6)]
    b['nb'] = next((n for n, pg in NBS if pg.contains(mid)), None)
    b['d'] = {}
    for k, _, _ in DF:
        own = [i for i, pg in DPOLY[k] if pg.contains(mid)]; ends = set(i for t in (0.02, 0.98) for i, pg in DPOLY[k] if pg.contains(g.interpolate(t, normalized=True)))
        b['d'][k] = [own[0] if own else None, sorted(ends - set(own))]
    cand = lambda tr, items: [items[int(i)] for i in tr.query(bp.buffer(30))] if tr is not None else []
    b['truck'] = sorted(set(t for t, s, tg in cand(trtree, TR) if share(tg, bp) > 0.4))
    b['bike'] = sorted(set('Class %s: %s' % (pr.get('cl'), pr.get('ty')) for pr, bg in cand(bktree, BIKE) if share(bg, bp) > 0.4))
    spd = collections.Counter()
    for pr, sg in cand(sptree, SPEED):
        s = share(sg, bp)
        if s > 0.4 and pr.get('sl'): spd[str(pr['sl'])] += s
    b['speed'] = [k for k, _ in spd.most_common()]
    b['bus'] = sorted(set(r for r, rg in cand(bstree, BUSR) if share(rg, bp) > 0.5))
    b['stops'] = [[s[2], s[3]] for s, sg in STOPS if sg.distance(bp) < 60]
    b['subway'] = [[round(sg.distance(bp)), s[2], s[3]] for s, sg in sorted(SUBS, key=lambda x: x[1].distance(bp))[:3] if sg.distance(bp) < 1500]
    b['citi'] = [[round(sg.distance(bp)), s[2]] for s, sg in CITI if sg.distance(bp) < 500]
# ================================================================== time series by block and month
def months_between(a, b):
    y, m = int(a[:4]), int(a[5:7]); out = []
    while (y, m) <= (int(b[:4]), int(b[5:7])): out.append('%d-%02d' % (y, m)); m += 1; (y, m) = (y + 1, 1) if m == 13 else (y, m)
    return out
WB = wkt(unary_union(BP).buffer(100).simplify(20)) if False else None
BAND = U(unary_union([bp.buffer(100) for bp in BP])).simplify(0.00003, preserve_topology=True)
WBAND = wkt(BAND if BAND.geom_type in ('Polygon', 'MultiPolygon') else BAND.convex_hull)
# Socrata rejects very long polygons; query by the CD 6 outline grown by 100 ft, then keep only points within 100 ft of a block
AREAQ = wkt(U(P(CB6).buffer(100)).simplify(0.00002, preserve_topology=True))
crash_last = get(url(NYC, 'h9gi-nx95', {'$select': 'max(crash_date) as d', '$where': f"crash_date<'{END}'"}))[0]['d'][:10]
s311_last = get(url(NYC, 'erm2-nwe9', {'$select': 'max(created_date) as d', '$where': f"created_date<'{END}'"}))[0]['d'][:10]
CM = months_between(START, crash_last); SM = months_between(START, s311_last); cmi = {m: i for i, m in enumerate(CM)}; smi = {m: i for i, m in enumerate(SM)}
NB_ = len(blocks)
def sparse(): return [dict() for _ in range(NB_)]
CR = sparse()    # block -> {month_index: [n, inj, cyc, ped, kil, truck]}
S3 = sparse(); S3T = sparse(); TK4 = sparse(); TK3 = sparse()
S3TYPE = [collections.Counter() for _ in range(NB_)]    # block -> type|year -> n
DAY = collections.defaultdict(collections.Counter)   # (kind, nb) -> date -> n
HOUR = collections.defaultdict(collections.Counter)  # (kind, nb, month_index) -> hour -> n
def tick(kind, b, date, hour, mi):
    nb = blocks[b]['nb'] or 'Other'
    DAY[(kind, nb)][date] += 1
    if hour is not None: HOUR[(kind, nb, mi)][hour] += 1
urls = {}
TRUCKV = re.compile(r'TRUCK|TRACTOR|TRAILER|DUMP|TANKER|FLAT|BOX|DELV|DELIV|CEMENT|CONCRETE|GARBAGE|REFUSE|SANITATION|\bTOW\b|STAKE|CHASSIS|ARMORED', re.I)
NOTTRUCK = re.compile(r'PICK|^PK$|SPORT UTILITY', re.I)   # pick-ups and SUVs are not counted as trucks
def istruck(t): return bool(TRUCKV.search(t) and not NOTTRUCK.search(t))
# crashes, by year (to keep each response modest)
cnt = collections.Counter()
for y in range(2013, int(crash_last[:4]) + 1):
    u = url(NYC, 'h9gi-nx95', {'$select': 'collision_id,crash_date,crash_time,latitude,longitude,number_of_persons_injured,number_of_persons_killed,number_of_cyclist_injured,number_of_pedestrians_injured,vehicle_type_code1,vehicle_type_code2,vehicle_type_code_3', '$where': f"crash_date>='{y}-01-01T00:00:00' AND crash_date<'{y + 1}-01-01T00:00:00' AND crash_date<'{END}' AND within_polygon(location,'{AREAQ}')", '$limit': 200000})
    urls.setdefault('crash', []).append(u)
    for r in get(u):
        if not r.get('latitude'): continue
        b = nearest(float(r['longitude']), float(r['latitude']))
        if b is None: cnt['crash_off'] += 1; continue
        m = cmi.get(r['crash_date'][:7])
        if m is None: continue
        v = CR[b].setdefault(m, [0, 0, 0, 0, 0, 0]); v[0] += 1; v[1] += int(float(r.get('number_of_persons_injured') or 0)); v[2] += int(float(r.get('number_of_cyclist_injured') or 0)); v[3] += int(float(r.get('number_of_pedestrians_injured') or 0)); v[4] += int(float(r.get('number_of_persons_killed') or 0))
        if any(istruck(r.get(k) or '') for k in ('vehicle_type_code1', 'vehicle_type_code2', 'vehicle_type_code_3')): v[5] += 1
        try: hh = int((r.get('crash_time') or '0:0').split(':')[0]) % 24
        except ValueError: hh = None
        tick('crash', b, r['crash_date'][:10], hh, m)
        cnt['crash'] += 1
    print('crashes', y, cnt['crash'])
# 311, both files, by year
S311 = [('76ig-c548', y) for y in range(2013, 2020)] + [('erm2-nwe9', y) for y in range(2020, int(s311_last[:4]) + 1)]
for ds, y in S311:
    off = 0
    while True:
        u = url(NYC, ds, {'$select': 'unique_key,created_date,complaint_type,descriptor,latitude,longitude', '$where': f"created_date>='{y}-01-01T00:00:00' AND created_date<'{y + 1}-01-01T00:00:00' AND created_date<'{END}' AND within_polygon(location,'{AREAQ}')", '$order': 'unique_key', '$limit': 200000, '$offset': off})
        rows = get(u)
        if off == 0: urls.setdefault('s311', []).append(u)
        for r in rows:
            if not r.get('latitude'): continue
            b = nearest(float(r['longitude']), float(r['latitude']))
            if b is None: cnt['s311_off'] += 1; continue
            m = smi.get(r['created_date'][:7])
            if m is None: continue
            S3[b][m] = S3[b].get(m, 0) + 1; ct = r.get('complaint_type') or ''
            S3TYPE[b][ct + '|' + r['created_date'][:4]] += 1
            tick('s311', b, r['created_date'][:10], int(r['created_date'][11:13]), m)
            if r.get('descriptor') == 'Truck Route Violation': S3T[b][m] = S3T[b].get(m, 0) + 1; tick('s3t', b, r['created_date'][:10], int(r['created_date'][11:13]), m)
            cnt['s311'] += 1
        if len(rows) < 200000: break
        off += 200000
    print('311', ds, y, cnt['s311'])
# NYPD truck route (413) and size or weight (385) summonses, both files
TKQ = []
for ds, a, bnd in (('bme5-7ty4', START, '2026-01-01T00:00:00'), ('57p3-pdcj', '2026-01-01T00:00:00', END)):
    u = url(NYC, ds, {'$select': 'evnt_key,violation_date,violation_code,latitude,longitude', '$where': f"(violation_code like '413%' OR violation_code like '385%') AND violation_date>='{a}' AND violation_date<'{bnd}' AND latitude between {bx[1]} and {bx[3]} AND longitude between {bx[0]} and {bx[2]}", '$limit': 200000})
    TKQ.append(u)
    for r in get(u):
        try: lat, lon = float(r['latitude']), float(r['longitude'])
        except (KeyError, ValueError, TypeError): continue
        b = nearest(lon, lat)
        if b is None: continue
        m = smi.get(r['violation_date'][:7])
        if m is None: continue
        dst = TK4 if r['violation_code'].startswith('413') else TK3
        dst[b][m] = dst[b].get(m, 0) + 1; cnt['tk413' if dst is TK4 else 'tk385'] += 1; tick('tk413' if dst is TK4 else 'tk385', b, r['violation_date'][:10], None, m)
urls['tickets'] = TKQ
tk_last = get(url(NYC, '57p3-pdcj', {'$select': 'max(violation_date) as d'}))[0]['d'][:10]
print('counts', dict(cnt))
# comparison areas by month: CD 6, the neighbouring CDs, Brooklyn
CDA = {}
for f in json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features']:
    cd = str(f['properties'].get('cd'))
    if cd in ('302', '306', '307', '308', '355'): CDA[cd] = wkt(shape(f['geometry']).buffer(0).simplify(0.00002, preserve_topology=True))
AR = {}
def mq(ds, dt, where):
    return url(NYC, ds, {'$select': f'date_trunc_ym({dt}) as m,count(*) as n', '$where': where, '$group': 'm', '$order': 'm', '$limit': 400})
for a, wk in list(CDA.items()) + [('brooklyn', None)]:
    loc = f"within_polygon(location,'{wk}')" if wk else "borough='BROOKLYN'"
    cu = mq('h9gi-nx95', 'crash_date', f"crash_date>='{START}' AND crash_date<'{END}' AND {loc}"); cm = [0] * len(CM)
    for r in get(cu):
        if r['m'][:7] in cmi: cm[cmi[r['m'][:7]]] = int(r['n'])
    sm = [0] * len(SM); su = []; tm = [0] * len(SM)
    for ds, a1, b1 in (('76ig-c548', START, '2020-01-01T00:00:00'), ('erm2-nwe9', '2020-01-01T00:00:00', END)):
        u = mq(ds, 'created_date', f"created_date>='{a1}' AND created_date<'{b1}' AND {loc}"); su.append(u)
        for r in get(u):
            if r['m'][:7] in smi: sm[smi[r['m'][:7]]] += int(r['n'])
        u2 = mq(ds, 'created_date', f"created_date>='{a1}' AND created_date<'{b1}' AND descriptor='Truck Route Violation' AND {loc}")
        for r in get(u2):
            if r['m'][:7] in smi: tm[smi[r['m'][:7]]] += int(r['n'])
    mi = None
    if wk:
        r = get(url(NYC, 'inkn-q76z', {'$select': 'sum(segmentlength) as ft', '$where': f"rw_type='1' AND within_polygon(the_geom,'{wk}')"}))[0]; mi = round(float(r['ft']) / 5280, 1)
    else:
        r = get(url(NYC, 'inkn-q76z', {'$select': 'sum(segmentlength) as ft', '$where': "boroughcode='3' AND rw_type='1'"}))[0]; mi = round(float(r['ft']) / 5280, 1)
    AR[a] = {'mi': mi, 'crash_url': cu, 'crash_m': cm, 's311_urls': su, 's311_m': sm, 'truck311_m': tm}
    print('area', a, mi, sum(cm), sum(sm), sum(tm))
# ================================================================== write
TYPES = collections.Counter()
for c in S3TYPE:
    for k, v in c.items(): TYPES[k.split('|')[0]] += v
TOPT = [t for t, _ in TYPES.most_common(40)]; ti = {t: i for i, t in enumerate(TOPT)}
YRS = [str(y) for y in range(2013, int(s311_last[:4]) + 1)]
def st_row(c):   # per block: {type_index: {year: n}} with 'other' as index len(TOPT)
    o = {}
    for k, v in c.items():
        t, y = k.split('|'); i = ti.get(t, len(TOPT)); o.setdefault(str(i), {}); o[str(i)][y] = o[str(i)].get(y, 0) + v
    return o
blk_out = []
for b in blocks:
    blk_out.append({k: v for k, v in b.items() if k not in ('g', 'sn')})
json.dump({'built': END[:10], 'cscl_query': CSCL_Q, 'blocks': blk_out,
           'geo': {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'id': b['id']}, 'geometry': rnd(b['g'].simplify(0.00001))} for b in blocks]}},
          open(os.path.join(OUT, 'blocks.json'), 'w'), separators=(',', ':'))
def enc(d): return {str(k): v for k, v in d.items()}
json.dump({'built': END[:10], 'start': START[:10], 'crash_last': crash_last, 's311_last': s311_last, 'tk_last': tk_last, 'crash_months': CM, 's311_months': SM, 'types': TOPT, 'years': YRS, 'urls': urls,
           'cr': [enc(x) for x in CR], 's3': [enc(x) for x in S3], 's3t': [enc(x) for x in S3T], 'tk413': [enc(x) for x in TK4], 'tk385': [enc(x) for x in TK3], 'st': [st_row(c) for c in S3TYPE],
           'areas': AR, 'counts': dict(cnt)}, open(os.path.join(OUT, 'ts.json'), 'w'), separators=(',', ':'))
D0 = datetime.date.fromisoformat(START[:10])
def daily(c, last):
    n = (datetime.date.fromisoformat(last) - D0).days + 1; arr = [0] * n
    for d, v in c.items():
        i = (datetime.date.fromisoformat(d) - D0).days
        if 0 <= i < n: arr[i] = v
    return arr
dd = {}
for (kind, nb), c in DAY.items(): dd.setdefault(nb, {})[kind] = daily(c, crash_last if kind == 'crash' else s311_last)
hh = {}
for (kind, nb, mi), c in HOUR.items(): hh.setdefault(nb, {}).setdefault(kind, {})[str(mi)] = [c.get(h, 0) for h in range(24)]
json.dump({'start': START[:10], 'crash_last': crash_last, 's311_last': s311_last, 'daily': dd, 'hour': hh}, open(os.path.join(OUT, 'daily.json'), 'w'), separators=(',', ':'))
for f in ('layers.json', 'blocks.json', 'ts.json', 'daily.json'): print(f, os.path.getsize(os.path.join(OUT, f)) // 1024, 'KB')
