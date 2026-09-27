#!/usr/bin/env python3
"""Build data/bqe/cb6-enforcement.json for bkcb6.app/BQE: NYPD truck route and size/weight tickets,
NYPD crashes involving trucks and 311 commercial overnight parking complaints, counted for Community
District 6 and every CB6 neighborhood outline (city-neighborhoods.geojson clipped to CB6), each split into
on or beside the BQE (on the BQE, an expressway or a ramp by name, or within about 40 m of the BQE lines)
versus local streets. Reads data/bqe/enforcement.json (from build_bqe_enforcement.py) for tickets."""
import json, os, collections, urllib.request, urllib.parse
from shapely.geometry import shape, Point
from shapely.ops import unary_union
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOC = 'https://data.cityofnewyork.us/resource/'
def get(ds, q): return json.load(urllib.request.urlopen(SOC + ds + '.json?' + urllib.parse.urlencode(q), timeout=600))
def pages(ds, q):
    out, off = [], 0
    while True:
        r = get(ds, dict(q, **{'$limit': 50000, '$offset': off})); out += r
        if len(r) < 50000: return out
        off += 50000
CB6 = [shape(f['geometry']).buffer(0) for f in json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features'] if str(f['properties']['cd']) == '306'][0]
NB = {}
for f in json.load(open(os.path.join(ROOT, 'data', 'city-neighborhoods.geojson')))['features']:
    g = shape(f['geometry']).buffer(0).intersection(CB6)
    if g.area > 1e-6:
        # round to the 6-decimal outline used in the page's linked NYC Open Data queries, so counts match them exactly
        from shapely.geometry import Polygon, MultiPolygon
        parts = [q for q in getattr(g, 'geoms', [g]) if q.geom_type == 'Polygon' and q.area > 1e-8]
        NB[f['properties']['nb']] = MultiPolygon([Polygon([(round(x, 6), round(y, 6)) for x, y in q.exterior.coords]) for q in parts])
HWY = unary_union([shape(f['geometry']) for f in json.load(open(os.path.join(ROOT, 'data', 'bqe', 'bqe-lines.geojson')))['features']]).buffer(0.0004)
def where(lat, lon):
    # returns the places a point counts toward: '306' if inside CB6, each neighborhood outline it falls in,
    # or 'none' if inside CB6 but in no outline; None if it counts toward nothing
    p = Point(lon, lat); nbs = [n for n, g in NB.items() if g.contains(p)]; in6 = CB6.contains(p)
    if not in6 and not nbs: return None
    return (['306'] if in6 else []) + (nbs or (['none'] if in6 else []))
def near_hwy(lat, lon, names=''):
    n = names.upper()
    return 'EXPRESSWAY' in n or 'EXPWY' in n or 'RAMP' in n or HWY.contains(Point(lon, lat))
PLACES = ['306'] + sorted(NB)
out = {'nbs': sorted(NB)}
# tickets
E = json.load(open(os.path.join(ROOT, 'data', 'bqe', 'enforcement.json')))
for key in ('truckroute', 'sizeweight'):
    agg = {p: {'total': 0, 'hwy': 0, 'streets': 0, 'by_year': collections.Counter()} for p in PLACES + ['none']}
    pts = []
    for la, lo, dt, code, cat, ds, ek in E[key]['pts']:
        w = where(la, lo)
        if w is None: continue
        h = near_hwy(la, lo)
        for p in w:
            a = agg[p]; a['total'] += 1; a['hwy' if h else 'streets'] += 1; a['by_year'][dt[:4]] += 1
        pts.append([la, lo, dt, code, cat, ds, ek, 1 if h else 0])
    out[key] = {k: dict(v, by_year=dict(sorted(v['by_year'].items()))) for k, v in agg.items()}
    out[key + '_pts'] = pts
    print(key, {k: (v['total'], v['hwy']) for k, v in agg.items()})
# crashes
TRK = E['crash_types']
VT = ['vehicle_type_code1', 'vehicle_type_code2', 'vehicle_type_code_3', 'vehicle_type_code_4', 'vehicle_type_code_5']
w = ' OR '.join("upper(%s) in (%s)" % (f, ','.join("'%s'" % t for t in TRK)) for f in VT)
minx, miny, maxx, maxy = CB6.bounds
cr = pages('h9gi-nx95', {'$select': 'collision_id,crash_date,on_street_name,cross_street_name,latitude,longitude,number_of_persons_injured,number_of_persons_killed',
                         '$where': f"({w}) AND latitude between {miny} and {maxy} AND longitude between {minx} and {maxx}", '$order': 'collision_id'})
agg = {p: {'crashes': 0, 'hwy': 0, 'streets': 0, 'injured': 0, 'killed': 0, 'streets_injured': 0, 'streets_killed': 0, 'by_year': collections.Counter()} for p in PLACES + ['none']}
cpts = []
for c in cr:
    try: la, lo = float(c['latitude']), float(c['longitude'])
    except (KeyError, ValueError): continue
    if not la or not lo: continue
    wh = where(la, lo)
    if wh is None: continue
    h = near_hwy(la, lo, (c.get('on_street_name') or '') + ' ' + (c.get('cross_street_name') or ''))
    inj, kil = int(c.get('number_of_persons_injured') or 0), int(c.get('number_of_persons_killed') or 0)
    for p in wh:
        a = agg[p]; a['crashes'] += 1; a['injured'] += inj; a['killed'] += kil; a['by_year'][c['crash_date'][:4]] += 1
        if h: a['hwy'] += 1
        else: a['streets'] += 1; a['streets_injured'] += inj; a['streets_killed'] += kil
    cpts.append([round(la, 6), round(lo, 6), c['crash_date'][:10], (c.get('on_street_name') or '').strip(), (c.get('cross_street_name') or '').strip(), inj, kil, c['collision_id'], 1 if h else 0])
out['crashes'] = {k: dict(v, by_year=dict(sorted(v['by_year'].items()))) for k, v in agg.items()}
out['crash_pts'] = cpts
out['crash_first'] = min(c['crash_date'][:10] for c in cr); out['crash_last'] = max(c['crash_date'][:10] for c in cr)
print('crashes', {k: (v['crashes'], v['hwy'], v['streets_killed']) for k, v in agg.items()})
# 311 commercial overnight parking
cp = pages('erm2-nwe9', {'$select': 'unique_key,created_date,descriptor,incident_address,street_name,latitude,longitude', '$where': "community_board='06 BROOKLYN' AND descriptor in('Commercial Overnight Parking','Overnight Commercial Storage')", '$order': 'unique_key'})
agg = {p: {'total': 0, 'by_desc': collections.Counter(), 'by_year': collections.Counter()} for p in PLACES + ['none', 'noloc']}
ppts = []
for c in cp:
    try: la, lo = float(c['latitude']), float(c['longitude'])
    except (KeyError, ValueError, TypeError): la = lo = 0
    if not la:
        wh = ['noloc']
    else:
        wh = where(la, lo) or ['306', 'none']  # every record here is a CB6 311 record by community board
        if '306' not in wh: wh = ['306'] + wh
        ppts.append([round(la, 6), round(lo, 6), c['created_date'][:10], c['descriptor'], c.get('incident_address') or c.get('street_name') or '', c['unique_key']])
    for p in (wh if wh != ['noloc'] else ['306', 'noloc']):
        a = agg[p]; a['total'] += 1; a['by_desc'][c['descriptor']] += 1; a['by_year'][c['created_date'][:4]] += 1
out['commercial311'] = {k: {'total': v['total'], 'by_desc': dict(v['by_desc']), 'by_year': dict(sorted(v['by_year'].items()))} for k, v in agg.items()}
out['commercial311_pts'] = ppts
out['c311_first'] = min(c['created_date'][:10] for c in cp); out['c311_last'] = max(c['created_date'][:10] for c in cp)
print('c311', {k: v['total'] for k, v in agg.items()})
json.dump(out, open(os.path.join(ROOT, 'data', 'bqe', 'cb6-enforcement.json'), 'w'), separators=(',', ':'))
