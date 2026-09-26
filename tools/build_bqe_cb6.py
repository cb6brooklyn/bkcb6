#!/usr/bin/env python3
"""Build data/bqe/cb6-counts.json for bkcb6.app/BQE: every NYC DOT vehicle classification count
(96ay-ea4r) and automated traffic volume count (7ym2-wayt) located inside Brooklyn Community
District 6, assigned to the neighborhood outlines used on bkcb6.app maps, plus 311 Truck Route Violation complaints by
neighborhood."""
import json, os, re, collections, urllib.request, urllib.parse, concurrent.futures as cf
from shapely.geometry import shape, Point
from shapely import wkt
from pyproj import Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'bqe', 'cb6-counts.json')
SOC = 'https://data.cityofnewyork.us/resource/'
GEO = 'b913bdfb9c47466589d0f08c99c75b21'
H = ["_12_00_1_00_am","_1_00_2_00am","_2_00_3_00am","_3_00_4_00am","_4_00_5_00am","_5_00_6_00am","_6_00_7_00am","_7_00_8_00am","_8_00_9_00am","_9_00_10_00am","_10_00_11_00am","_11_00_12_00pm","_12_00_1_00pm","_1_00_2_00pm","_2_00_3_00pm","_3_00_4_00pm","_4_00_5_00pm","_5_00_6_00pm","_6_00_7_00pm","_7_00_8_00pm","_8_00_9_00pm","_9_00_10_00pm","_10_00_11_00pm","_11_00_12_00am"]
NBS = ['Park Slope', 'Carroll Gardens', 'Cobble Hill', 'Red Hook', 'Gowanus', 'Columbia Street Waterfront District']

def get(url, headers=None):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=300))
def soql(ds, **q):
    return get(SOC + ds + '.json?' + urllib.parse.urlencode(q))

CB6 = shape([f for f in json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features'] if str(f['properties']['cd']) == '306'][0]['geometry']).buffer(0)
# neighborhood outlines used on the bkcb6.app maps (data/city-neighborhoods.geojson), clipped to CB6
NBG = []
for f in json.load(open(os.path.join(ROOT, 'data', 'city-neighborhoods.geojson')))['features']:
    g = shape(f['geometry']).buffer(0)
    if g.intersects(CB6):
        gi = g.intersection(CB6)
        if gi.area > 0: NBG.append((f['properties']['nb'], gi))
def nb_of(lat, lon):
    p = Point(lon, lat)
    for n, g in NBG:
        if g.contains(p): return n, 0
    d, n = sorted((g.distance(p), n) for n, g in NBG)[0]
    return n, round(d * 111000)   # on a boundary street: nearest outline, metres away

# ---- classification counts: geocode every location in Brooklyn, keep those inside CB6
cache = {}
def ix(a, b):
    k = (a.upper(), b.upper())
    if k in cache: return cache[k]
    res = None
    for comp in (None, 'E', 'W', 'N', 'S'):
        p = {'crossStreetOne': a, 'crossStreetTwo': b, 'borough': 'Brooklyn', 'subscription-key': GEO}
        if comp: p['compassDirection'] = comp
        try: d = get('https://api.nyc.gov/geoclient/v2/intersection.json?' + urllib.parse.urlencode(p), {'Referer': 'https://bkcb6.app/'}).get('intersection', {})
        except Exception: d = {}
        if d.get('latitude'): res = (float(d['latitude']), float(d['longitude'])); break
        if 'TWICE' not in str(d.get('message', '')): break
    cache[k] = res; return res
def cl(s): return re.sub(r'\b(NB|SB|EB|WB)\b', '', s, flags=re.I).strip()
idx = soql('96ay-ea4r', **{'$select': 'segmentid,roadway_name,`from`,`to`,count(*)', '$group': 'segmentid,roadway_name,`from`,`to`', '$limit': 50000})
locs = sorted(set((r['segmentid'], cl(r['roadway_name']), cl(r.get('from', '')), cl(r.get('to', ''))) for r in idx))
def job(l):
    p1 = ix(l[1], l[2]); p2 = ix(l[1], l[3])
    pt = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2) if p1 and p2 else (p1 or p2)
    return l, pt
inloc = {}
with cf.ThreadPoolExecutor(8) as ex:
    for l, pt in ex.map(job, locs):
        if pt and CB6.contains(Point(pt[1], pt[0])): inloc[(l[0], l[1].lower())] = [round(pt[0], 6), round(pt[1], 6)]
print('classification locations in CB6', len(inloc))
rows = []
for s in sorted(set(k[0] for k in inloc)):
    rows += soql('96ay-ea4r', segmentid=s, **{'$limit': 5000})
G = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(float)))
for r in rows:
    key = (r['segmentid'], cl(r['roadway_name']).lower())
    if key not in inloc: continue
    c = r['veh_class_type'].strip().lower()
    k2 = 'heavy' if 'heavy' in c else 'medium' if 'medium' in c else 'trucks' if c == 'trucks' else 'other'
    G[(r['segmentid'], r['roadway_name'], r['from'], r['to'], r['direction'], r['date'][:4])][r['date'][:10]][k2] += sum(float(r.get(h) or 0) for h in H)
places = collections.OrderedDict()
for k, days in sorted(G.items(), key=lambda z: (z[0][1].lower(), z[0][5])):
    seg, name, frm, to, dr, yr = k
    pt = inloc[(seg, cl(name).lower())]
    n = len(days); dl = sorted(days)
    tot = sum(sum(v.values()) for v in days.values()) / n
    tr = sum(v['heavy'] + v['medium'] + v['trucks'] for v in days.values()) / n
    split = any(v['heavy'] + v['medium'] > 0 for v in days.values())
    hv = sum(v['heavy'] for v in days.values()) / n
    where = "segmentid='%s' AND direction='%s' AND date between '%sT00:00:00' and '%sT23:59:59'" % (seg, dr, dl[0], dl[-1])
    url = SOC + '96ay-ea4r.json?' + urllib.parse.urlencode({'$where': where}, quote_via=urllib.parse.quote)
    pk = ('class', seg, pt[0], pt[1])
    if pk not in places:
        nbn, off = nb_of(*pt)
        places[pk] = {'src': 'class', 'name': '%s, %s to %s' % (cl(name), cl(frm).title() if frm.isupper() else cl(frm), cl(to).title() if to.isupper() else cl(to)), 'pt': pt, 'nb': nbn, 'edge_m': off, 'rows': []}
    places[pk]['rows'].append({'dir': dr, 'yr': yr, 'first': dl[0], 'last': dl[-1], 'days': n, 'all': round(tot), 'trucks': round(tr), 'heavy': round(hv) if split else None, 'url': url})

# ---- automated traffic volume counts inside CB6
T = Transformer.from_crs(2263, 4326, always_xy=True)
geo = soql('7ym2-wayt', **{'$select': 'segmentid,wktgeom,count(*)', '$where': "boro='Brooklyn'", '$group': 'segmentid,wktgeom', '$limit': 50000})
apt = {}
for x in geo:
    g = wkt.loads(x['wktgeom']); c = g.interpolate(0.5, normalized=True) if g.geom_type != 'Point' else g
    lon, lat = T.transform(c.x, c.y)
    if CB6.contains(Point(lon, lat)): apt.setdefault(x['segmentid'], [round(lat, 6), round(lon, 6)])
arows = []
ids = sorted(apt)
for i in range(0, len(ids), 40):
    arows += soql('7ym2-wayt', **{'$select': 'segmentid,street,fromst,tost,direction,yr,m,d,count(*) as n,sum(vol) as v',
                                  '$where': "boro='Brooklyn' AND segmentid in(%s)" % ','.join("'%s'" % s for s in ids[i:i + 40]),
                                  '$group': 'segmentid,street,fromst,tost,direction,yr,m,d', '$limit': 50000})
A = collections.defaultdict(list); nofull = collections.defaultdict(int)
for x in arows:
    k = (x['segmentid'], x['street'], x['fromst'], x['tost'], x['direction'], x['yr'])
    if int(x['n']) == 96: A[k].append((int(x['m']), int(x['d']), int(x['v'])))
    else: nofull[k] += 1
partial = []
for k in sorted(set(nofull) | set(A)):
    if k in A: continue
    partial.append({'seg': k[0], 'nb': nb_of(*apt[k[0]])[0], 'n15': nofull[k], 'name': k[1], 'from': k[2], 'to': k[3], 'dir': k[4], 'yr': k[5],
                    'url': SOC + '7ym2-wayt.json?' + urllib.parse.urlencode({'$where': "boro='Brooklyn' AND segmentid='%s' AND street='%s' AND fromst='%s' AND tost='%s' AND direction='%s' AND yr='%s'" % (k[0], k[1].replace("'", "''"), k[2].replace("'", "''"), k[3].replace("'", "''"), k[4], k[5]), '$limit': 5000}, quote_via=urllib.parse.quote)})
for k, v in sorted(A.items(), key=lambda z: (z[0][1].lower(), z[0][5])):
    seg, name, frm, to, dr, yr = k
    pt = apt[seg]; v.sort()
    esc = lambda s: s.replace("'", "''")
    url = SOC + '7ym2-wayt.json?' + urllib.parse.urlencode({'$where': "boro='Brooklyn' AND segmentid='%s' AND street='%s' AND fromst='%s' AND tost='%s' AND direction='%s' AND yr='%s'" % (seg, esc(name), esc(frm), esc(to), dr, yr), '$limit': 5000}, quote_via=urllib.parse.quote)
    pk = ('atr', seg, name, frm, to)
    if pk not in places:
        nbn, off = nb_of(*pt)
        places[pk] = {'src': 'atr', 'name': '%s, %s to %s' % (name.title() if name.isupper() else name, frm.title() if frm.isupper() else frm, to.title() if to.isupper() else to), 'pt': pt, 'nb': nbn, 'edge_m': off, 'rows': []}
    places[pk]['rows'].append({'dir': dr, 'yr': yr, 'first': '%s-%02d-%02d' % (yr, v[0][0], v[0][1]), 'last': '%s-%02d-%02d' % (yr, v[-1][0], v[-1][1]), 'days': len(v), 'all': round(sum(z[2] for z in v) / len(v)), 'trucks': None, 'heavy': None, 'url': url})

# ---- 311 Truck Route Violation complaints in CB6 by neighborhood
cm = json.load(open(os.path.join(ROOT, 'data', 'bqe', 'truck-complaints.json')))
cnb = collections.Counter(); cedge = 0
for p in cm['p']:
    if p[4] != '06 BROOKLYN': continue
    n, off = nb_of(p[0], p[1]); cnb[n] += 1; cedge += 1 if off else 0
found = [n for n in NBS] + sorted(set(p['nb'] for p in places.values()) | set(cnb) - set(NBS))
out = {'places': list(places.values()), 'partial': partial, 'nbs': found, 'complaints_by_nb': {n: cnb.get(n, 0) for n in found},
       'complaints_edge': cedge, 'complaints_cb6_total': sum(cnb.values()), 'max_edge_m': max([p['edge_m'] for p in places.values()] + [0])}
json.dump(out, open(OUT, 'w'), indent=1)
print('places', len(places), collections.Counter(p['src'] for p in places.values()), 'partial', len(partial))
print('by nb', collections.Counter((p['nb'], p['src']) for p in places.values()))
print('complaints', out['complaints_by_nb'], 'edge', cedge, 'max edge m', out['max_edge_m'])
