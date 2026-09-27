"""Correct two things in an existing data/bqe/kit build without re-reading every 311 request:
1. the 311 "Truck Route Violation" counts (ts.json s3t, daily.json s3t, areas truck311_m);
2. the crash counts by block, with the truck rule build_bqe_kit.py now uses (pick-ups and SUVs are not trucks).

"Truck Route Violation" is a 311 descriptor (complaint type "Traffic"), not a complaint type. build_bqe_kit.py now
filters on the descriptor; this script fills the same fields in an existing build without re-reading every 311 request.
Each request counts once, on the nearest block within 100 ft, as in build_bqe_kit.py.
"""
import json, os, re, urllib.parse, urllib.request, time, datetime, collections
from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, 'data', 'bqe', 'kit')
NYC = 'https://data.cityofnewyork.us/resource/'
TO = Transformer.from_crs(4326, 2263, always_xy=True)
P = lambda g: transform(lambda x, y, z=None: TO.transform(x, y), g)
def url(ds, q): return NYC + ds + '.json?' + urllib.parse.urlencode(q)
def get(u):
    for i in range(4):
        try: return json.load(urllib.request.urlopen(u, timeout=900))
        except Exception as e: err = e; time.sleep(6)
    raise err
def wkt(poly):
    parts = [q for q in getattr(poly, 'geoms', [poly]) if q.geom_type == 'Polygon']
    return 'MULTIPOLYGON(' + ','.join('((' + ','.join('%.6f %.6f' % c for c in q.exterior.coords) + '))' for q in parts) + ')'
BK = json.load(open(os.path.join(K, 'blocks.json'))); TS = json.load(open(os.path.join(K, 'ts.json'))); DY = json.load(open(os.path.join(K, 'daily.json')))
blocks = BK['blocks']; BP = [P(shape(f['geometry'])) for f in BK['geo']['features']]; tree = STRtree(BP)
def nearest(lon, lat):
    pt = P(Point(lon, lat)); i = int(tree.nearest(pt)); return i if BP[i].distance(pt) <= 100 else None
CB6 = next(shape(f['geometry']).buffer(0) for f in json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features'] if str(f['properties'].get('cd')) == '306')
CB6 = CB6 if CB6.geom_type == 'Polygon' else max(CB6.geoms, key=lambda g: g.area)
BACK = Transformer.from_crs(2263, 4326, always_xy=True); U = lambda g: transform(lambda x, y, z=None: BACK.transform(x, y), g)
AREAQ = wkt(U(P(CB6).buffer(100)).simplify(0.00002, preserve_topology=True))
SM = TS['s311_months']; smi = {m: i for i, m in enumerate(SM)}; END = (datetime.date.fromisoformat(TS['s311_last']) + datetime.timedelta(days=1)).isoformat() + 'T00:00:00'
S3T = [dict() for _ in blocks]; DAY = collections.defaultdict(collections.Counter); HOUR = collections.defaultdict(collections.Counter); us = []; n = 0
for ds, a, b in (('76ig-c548', TS['start'] + 'T00:00:00', '2020-01-01T00:00:00'), ('erm2-nwe9', '2020-01-01T00:00:00', END)):
    u = url(ds, {'$select': 'unique_key,created_date,latitude,longitude', '$where': f"descriptor='Truck Route Violation' AND created_date>='{a}' AND created_date<'{b}' AND within_polygon(location,'{AREAQ}')", '$limit': 200000})
    us.append(u)
    for r in get(u):
        if not r.get('latitude'): continue
        bi = nearest(float(r['longitude']), float(r['latitude']))
        m = smi.get(r['created_date'][:7])
        if bi is None or m is None: continue
        S3T[bi][str(m)] = S3T[bi].get(str(m), 0) + 1; n += 1
        nb = blocks[bi]['nb'] or 'Other'; DAY[nb][r['created_date'][:10]] += 1; HOUR[(nb, m)][int(r['created_date'][11:13])] += 1
TS['s3t'] = S3T; TS['urls']['s311_truck'] = us; TS['counts']['s3t'] = n
D0 = datetime.date.fromisoformat(DY['start']); nd = (datetime.date.fromisoformat(DY['s311_last']) - D0).days + 1
for nb in DY['daily']:
    arr = [0] * nd
    for d, v in DAY.get(nb, {}).items():
        i = (datetime.date.fromisoformat(d) - D0).days
        if 0 <= i < nd: arr[i] = v
    DY['daily'][nb]['s3t'] = arr
    DY['hour'].setdefault(nb, {})['s3t'] = {str(m): [c.get(h, 0) for h in range(24)] for (k, m), c in HOUR.items() if k == nb}
CDA = {str(f['properties'].get('cd')): wkt(shape(f['geometry']).buffer(0).simplify(0.00002, preserve_topology=True)) for f in json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features'] if str(f['properties'].get('cd')) in TS['areas']}
for a in TS['areas']:
    loc = f"within_polygon(location,'{CDA[a]}')" if a in CDA else "borough='BROOKLYN'"; tm = [0] * len(SM); tu = []
    for ds, x, y in (('76ig-c548', TS['start'] + 'T00:00:00', '2020-01-01T00:00:00'), ('erm2-nwe9', '2020-01-01T00:00:00', END)):
        u = url(ds, {'$select': 'date_trunc_ym(created_date) as m,count(*) as n', '$where': f"created_date>='{x}' AND created_date<'{y}' AND descriptor='Truck Route Violation' AND {loc}", '$group': 'm', '$order': 'm', '$limit': 400}); tu.append(u)
        for r in get(u):
            if r['m'][:7] in smi: tm[smi[r['m'][:7]]] += int(r['n'])
    TS['areas'][a]['truck311_m'] = tm; TS['areas'][a]['truck311_urls'] = tu
    print('area', a, sum(tm))

# ---- crashes, re-read by year, with the corrected truck rule (same as build_bqe_kit.py)
TRUCKV = re.compile(r'TRUCK|TRACTOR|TRAILER|DUMP|TANKER|FLAT|BOX|DELV|DELIV|CEMENT|CONCRETE|GARBAGE|REFUSE|SANITATION|\bTOW\b|STAKE|CHASSIS|ARMORED', re.I)
NOTTRUCK = re.compile(r'PICK|^PK$|SPORT UTILITY', re.I)
def istruck(t): return bool(TRUCKV.search(t) and not NOTTRUCK.search(t))
CM = TS['crash_months']; cmi = {m: i for i, m in enumerate(CM)}; CEND = (datetime.date.fromisoformat(TS['crash_last']) + datetime.timedelta(days=1)).isoformat() + 'T00:00:00'
CR = [dict() for _ in blocks]; CDAY = collections.defaultdict(collections.Counter); CHOUR = collections.defaultdict(collections.Counter); cu = []; nc = 0
for y in range(int(TS['start'][:4]), int(TS['crash_last'][:4]) + 1):
    u = url('h9gi-nx95', {'$select': 'collision_id,crash_date,crash_time,latitude,longitude,number_of_persons_injured,number_of_persons_killed,number_of_cyclist_injured,number_of_pedestrians_injured,vehicle_type_code1,vehicle_type_code2,vehicle_type_code_3', '$where': f"crash_date>='{y}-01-01T00:00:00' AND crash_date<'{y + 1}-01-01T00:00:00' AND crash_date<'{CEND}' AND within_polygon(location,'{AREAQ}')", '$limit': 200000})
    cu.append(u)
    for r in get(u):
        if not r.get('latitude'): continue
        bi = nearest(float(r['longitude']), float(r['latitude'])); m = cmi.get(r['crash_date'][:7])
        if bi is None or m is None: continue
        v = CR[bi].setdefault(str(m), [0, 0, 0, 0, 0, 0]); v[0] += 1; v[1] += int(float(r.get('number_of_persons_injured') or 0)); v[2] += int(float(r.get('number_of_cyclist_injured') or 0)); v[3] += int(float(r.get('number_of_pedestrians_injured') or 0)); v[4] += int(float(r.get('number_of_persons_killed') or 0))
        if any(istruck(r.get(k) or '') for k in ('vehicle_type_code1', 'vehicle_type_code2', 'vehicle_type_code_3')): v[5] += 1
        nb = blocks[bi]['nb'] or 'Other'; CDAY[nb][r['crash_date'][:10]] += 1; nc += 1
        try: CHOUR[(nb, m)][int((r.get('crash_time') or '0:0').split(':')[0]) % 24] += 1
        except ValueError: pass
    print('crashes', y, nc)
TS['tk_last'] = get(url('57p3-pdcj', {'$select': 'max(violation_date) as d'}))[0]['d'][:10]
TS['cr'] = CR; TS['urls']['crash'] = cu; TS['counts']['crash'] = nc
nd = (datetime.date.fromisoformat(DY['crash_last']) - datetime.date.fromisoformat(DY['start'])).days + 1
for nb in set(DY['daily']) | set(CDAY):
    arr = [0] * nd
    for d, c in CDAY.get(nb, {}).items():
        i = (datetime.date.fromisoformat(d) - datetime.date.fromisoformat(DY['start'])).days
        if 0 <= i < nd: arr[i] = c
    DY['daily'].setdefault(nb, {})['crash'] = arr
    DY['hour'].setdefault(nb, {})['crash'] = {str(m): [c.get(h, 0) for h in range(24)] for (k, m), c in CHOUR.items() if k == nb}
json.dump(TS, open(os.path.join(K, 'ts.json'), 'w'), separators=(',', ':')); json.dump(DY, open(os.path.join(K, 'daily.json'), 'w'), separators=(',', ':'))
print('truck route violation requests on blocks', n, 'crashes on blocks', nc, 'involving a truck', sum(v[5] for d in CR for v in d.values()))
