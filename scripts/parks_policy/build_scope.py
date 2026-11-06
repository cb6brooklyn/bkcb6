import json, re, pickle, collections as C, warnings, sys
warnings.filterwarnings('ignore')
from shapely.geometry import shape, Point, mapping
from shapely import make_valid
L = lambda n: json.load(open('raw/%s.json' % n))
A = json.load(open('out/all.json')); m = pickle.load(open('out/mid.pkl', 'rb'))
D, BO, RK = A['D'], A['BO'], A['RK']
BL = {'M': 'Manhattan', 'X': 'Bronx', 'B': 'Brooklyn', 'Q': 'Queens', 'R': 'Staten Island'}
AB = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
code = lambda cd: AB[cd[0]] + cd[1:].zfill(2)
scope = sys.argv[1]  # brooklyn | nyc
boro = 'Brooklyn' if scope == 'brooklyn' else None

def rnd(g, n=5):
    def r(c):
        if isinstance(c[0], (int, float)): return [round(c[0], n), round(c[1], n)]
        return [r(x) for x in c]
    d = mapping(g); return {'type': d['type'], 'coordinates': r(d['coordinates'])}

# districts with metrics
SD = json.load(open('/root/bkcb6/sanitation-policy/%s/districts.geojson' % ('brooklyn' if boro else 'nyc')))
KEEP = ['acres', 'acresPer1k', 'parks', 'pipN', 'pipOverall', 'pipClean', 'trees', 'treesPer1k', 'planted', 'emptySpaces', 'fsr', 'fsrPer1k', 'c311', 'c311Per1k',
        'fountains', 'spray', 'play', 'playPer10k', 'dogs', 'pools', 'skate', 'athletic', 'gardens', 'monuments', 'restrooms', 'capital']
feats = []
for f in SD['features']:
    p = f['properties']; b = p['b']
    np = dict(b=b, num=p['num'], boro=p.get('boro') or 'Brooklyn', names=p.get('names'), st=p.get('st'), c=p['c'], pop=p['pop'])
    np.update({k: D[b][k] for k in KEEP})
    np['rk'] = {k: [RK[k]['bk' if False else 'nyc'].get(b)] for k in []}
    np['rkB'] = {k: None for k in []}
    # rank within borough and citywide, computed fresh so every borough is right
    feats.append(dict(type='Feature', properties=np, geometry=f['geometry']))
def rank(key, hi, within=None):
    items = [(k, v[key]) for k, v in D.items() if v[key] is not None and (within is None or k[:2] == within)]
    items.sort(key=lambda x: -x[1] if hi else x[1])
    out = {}; r = 0; prev = object()
    for i, (k, v) in enumerate(items):
        if v != prev: r = i + 1; prev = v
        out[k] = [r, len(items)]
    return out
HI = {k: True for k in KEEP}; HI.update(c311Per1k=False, fsrPer1k=False, c311=False, fsr=False, emptySpaces=False, pipN=True)
for f in feats:
    p = f['properties']; b = p['b']
    p['rB'] = {k: rank(k, HI[k], b[:2]).get(b) for k in KEEP}
    p['rN'] = {k: rank(k, HI[k]).get(b) for k in KEEP}
json.dump(dict(type='FeatureCollection', features=feats), open('out/%s-districts.geojson' % scope, 'w'), separators=(',', ':'))

# boroughs ranked against each other
BOROS = ['Manhattan', 'Bronx', 'Brooklyn', 'Queens', 'Staten Island']
def brank(key, hi):
    s = sorted([b for b in BOROS if BO[b][key] is not None], key=lambda b: -BO[b][key] if hi else BO[b][key])
    return {b: [s.index(b) + 1, len(s)] for b in s}
BR = {k: brank(k, HI[k]) for k in KEEP}

# parks in scope, with inspections
P = L('props')
insp = {}
for pid, rows in m['pip_prop'].items():
    n = len(rows); o = sum(r['overall_condition'] == 'A' for r in rows); c = sum(r['cleanliness'] == 'A' for r in rows)
    last = max(rows, key=lambda r: r['date'])
    insp[pid] = [n, round(100 * o / n, 1), round(100 * c / n, 1), last['date'][:10], last['overall_condition']]
cdof = {}
for k, ids in m['parks_cd'].items():
    for i in ids: cdof.setdefault(i, []).append(k)
parks = []
tol = 0.00004 if boro else 0.00008
for p in P:
    b = BL.get(p.get('borough'))
    if boro and b != boro: continue
    if not p.get('multipolygon'): continue
    g = make_valid(shape(p['multipolygon'])).simplify(tol, preserve_topology=True)
    if g.is_empty: continue
    c = g.representative_point()
    i = p['gispropnum']
    ds = [code(x) for x in cdof.get(i, []) if int(x[1:]) <= 18]
    parks.append(dict(id=i, n=p.get('signname'), t=p.get('typecategory'), a=round(float(p.get('acres') or 0), 2), b=b, d=ds, loc=p.get('location'),
        i=insp.get(i), lat=round(c.y, 5), lon=round(c.x, 5), g=rnd(g)))
# capital projects underway in scope
cap = []
for r in L('cap'):
    if r.get('currentphase') == 'completed': continue
    if boro and r.get('borough') != boro: continue
    if not r.get('latitude'): continue
    cap.append(dict(lat=round(float(r['latitude']), 5), lon=round(float(r['longitude']), 5), id=r.get('trackerid'), t=r.get('title'), ph=r.get('currentphase'),
        fund=r.get('totalfunding'), park=r.get('name'), pid=r.get('parkid'), b=r.get('borough'),
        dp=r.get('designpercentcomplete'), pp=r.get('procurementpercentcomplete'), cp=r.get('constructionpercentcomplete')))
out = dict(scope=scope, name=boro or 'New York City', win=A['win'], BO={b: BO[b] for b in BOROS + ['NYC']}, BR=BR, parks=parks, cap=cap)
json.dump(out, open('out/%s.json' % scope, 'w'), separators=(',', ':'))
import os
print(scope, len(feats), len(parks), len(cap), os.path.getsize('out/%s.json' % scope) // 1024, 'KB')
