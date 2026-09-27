#!/usr/bin/env python3
"""Build data/bqe/enforcement.json for bkcb6.app/BQE/carrollgardens-gowanus: NYPD moving violation
summonses for truck routes (NYC Traffic Rules 4-13, codes 413*) and vehicle size/weight (VTL 385, codes
385*), NYPD crashes involving trucks, and 311 commercial-vehicle parking complaints, counted for Carroll
Gardens, Gowanus, CB6 and each community district the BQE crosses, with CB6-area points for the map."""
import json, os, collections, urllib.request, urllib.parse
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOC = 'https://data.cityofnewyork.us/resource/'
def get(ds, q):
    return json.load(urllib.request.urlopen(SOC + ds + '.json?' + urllib.parse.urlencode(q), timeout=600))
def pages(ds, q):
    out, off = [], 0
    while True:
        qq = dict(q, **{'$limit': 50000, '$offset': off}); r = get(ds, qq); out += r
        if len(r) < 50000: return out
        off += 50000
cdf = json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features']
CDG = [(str(f['properties']['cd']), shape(f['geometry']).buffer(0)) for f in cdf]
CB6 = [g for c, g in CDG if c == '306'][0]
NBG = {n: shape(f['geometry']).buffer(0).intersection(CB6) for f in json.load(open(os.path.join(ROOT, 'data', 'city-neighborhoods.geojson')))['features'] for n in [f['properties']['nb']] if n in ('Carroll Gardens', 'Gowanus')}
ALONG = json.load(open(os.path.join(ROOT, 'data', 'bqe', 'counts.json')))['along']
tree = STRtree([g for c, g in CDG])
def cd_of(lat, lon):
    p = Point(lon, lat)
    for i in tree.query(p):
        if CDG[i][1].contains(p): return CDG[i][0]
    return None
VIEW = CB6.buffer(0.012)
CDP = {c: g for c, g in CDG if c in ALONG or c == '306'}  # tested directly: 355 (Prospect Park) overlaps CB6
def tally(recs, getpt, getyr):
    by = {'Carroll Gardens': collections.Counter(), 'Gowanus': collections.Counter(), '306': collections.Counter()}
    for cd in ALONG: by.setdefault(cd, collections.Counter())
    city = collections.Counter(); pts = []; noloc = 0
    for r in recs:
        pt = getpt(r); yr = getyr(r)
        city[yr] += 1
        if not pt: noloc += 1; continue
        p = Point(pt[1], pt[0])
        for cd in [c for c in by if c.isdigit()]:
            if CDP[cd].contains(p): by[cd][yr] += 1
        for n, g in NBG.items():
            if g.contains(p): by[n][yr] += 1
        if VIEW.contains(p): pts.append(r)
    return by, city, pts, noloc
def fpt(r, la='latitude', lo='longitude'):
    try:
        a, b = float(r.get(la) or 0), float(r.get(lo) or 0)
        return (a, b) if a and b else None
    except ValueError: return None
out = {}
# ---- summonses
summ = []
for ds in ('bme5-7ty4', '57p3-pdcj'):
    summ += [dict(x, ds=ds) for x in pages(ds, {'$select': 'evnt_key,violation_date,chg_law_cd,violation_code,veh_category,latitude,longitude', '$where': "violation_code like '413%' OR violation_code like '385%'", '$order': 'evnt_key'})]
for key, pre in (('truckroute', '413'), ('sizeweight', '385')):
    recs = [r for r in summ if r['violation_code'].startswith(pre)]
    by, city, pts, noloc = tally(recs, fpt, lambda r: r['violation_date'][:4])
    out[key] = {'by': {k: dict(sorted(v.items())) for k, v in by.items()}, 'city': dict(sorted(city.items())), 'noloc': noloc,
                'first': min(r['violation_date'][:10] for r in recs), 'last': max(r['violation_date'][:10] for r in recs),
                'pts': [[round(float(r['latitude']), 6), round(float(r['longitude']), 6), r['violation_date'][:10], r['violation_code'], r.get('veh_category', ''), r['ds'], r['evnt_key']] for r in pts]}
    print(key, 'records', len(recs), 'no loc', noloc, {k: sum(v.values()) for k, v in by.items()})
# ---- crashes involving trucks (NYPD Motor Vehicle Collisions)
TRK = ['BOX TRUCK', 'TRACTOR TRUCK DIESEL', 'TRACTOR TRUCK GASOLINE', 'DUMP', 'FLAT BED', 'GARBAGE OR REFUSE', 'TANKER', 'CONCRETE MIXER', 'LARGE COM VEH(6 OR MORE TIRES)', 'TOW TRUCK / WRECKER', 'ARMORED TRUCK', 'BEVERAGE TRUCK', 'STAKE OR RACK', 'CHASSIS CAB', 'REFRIGERATED VAN', 'TRUCK']
VT = ['vehicle_type_code1', 'vehicle_type_code2', 'vehicle_type_code_3', 'vehicle_type_code_4', 'vehicle_type_code_5']
w = ' OR '.join("upper(%s) in (%s)" % (f, ','.join("'%s'" % t for t in TRK)) for f in VT)
minx, miny, maxx, maxy = CB6.buffer(0.02).bounds
crashes = pages('h9gi-nx95', {'$select': 'collision_id,crash_date,on_street_name,cross_street_name,latitude,longitude,number_of_persons_injured,number_of_persons_killed,vehicle_type_code1,vehicle_type_code2,vehicle_type_code_3',
                              '$where': f"({w}) AND latitude between {miny} and {maxy} AND longitude between {minx} and {maxx}", '$order': 'collision_id'})
bl = json.load(open(os.path.join(ROOT, 'data', 'bqe', 'bqe-lines.geojson')))['features']
from shapely.ops import unary_union
HWY = unary_union([shape(f['geometry']) for f in bl]).buffer(0.0004)  # about 40 m either side of the BQE and its ramps
def on_hwy(c):
    n = ((c.get('on_street_name') or '') + ' ' + (c.get('cross_street_name') or '')).upper()
    return 'EXPRESSWAY' in n or 'EXPWY' in n or 'RAMP' in n or HWY.contains(Point(float(c['longitude']), float(c['latitude'])))
cr = {}
for n, g in list(NBG.items()) + [('306', CB6)]:
    sel = [c for c in crashes if fpt(c) and g.contains(Point(float(c['longitude']), float(c['latitude'])))]
    cr[n] = {'crashes': len(sel), 'injured': sum(int(c.get('number_of_persons_injured') or 0) for c in sel), 'killed': sum(int(c.get('number_of_persons_killed') or 0) for c in sel),
             'by_year': dict(sorted(collections.Counter(c['crash_date'][:4] for c in sel).items())),
             'hwy': sum(1 for c in sel if on_hwy(c)), 'streets': sum(1 for c in sel if not on_hwy(c)),
             'streets_injured': sum(int(c.get('number_of_persons_injured') or 0) for c in sel if not on_hwy(c)),
             'streets_killed': sum(int(c.get('number_of_persons_killed') or 0) for c in sel if not on_hwy(c))}
out['crashes'] = cr
out['crash_types'] = TRK
out['crash_first'] = min(c['crash_date'][:10] for c in crashes) if crashes else None
out['crash_last'] = max(c['crash_date'][:10] for c in crashes) if crashes else None
out['crash_pts'] = [[round(float(c['latitude']), 6), round(float(c['longitude']), 6), c['crash_date'][:10], c.get('on_street_name') or '', c.get('cross_street_name') or '', int(c.get('number_of_persons_injured') or 0), int(c.get('number_of_persons_killed') or 0), c['collision_id'], 1 if on_hwy(c) else 0]
                    for c in crashes if fpt(c) and any(g.contains(Point(float(c['longitude']), float(c['latitude']))) for g in NBG.values())]
print('crashes', cr)
# ---- 311 commercial vehicle parking complaints in CB6
cp = pages('erm2-nwe9', {'$select': 'unique_key,created_date,descriptor,incident_address,street_name,latitude,longitude', '$where': "community_board='06 BROOKLYN' AND descriptor in('Commercial Overnight Parking','Overnight Commercial Storage')", '$order': 'unique_key'})
c311 = {}
for n, g in NBG.items():
    sel = [c for c in cp if fpt(c) and g.contains(Point(float(c['longitude']), float(c['latitude'])))]
    c311[n] = {'total': len(sel), 'by_desc': dict(collections.Counter(c['descriptor'] for c in sel)), 'by_year': dict(sorted(collections.Counter(c['created_date'][:4] for c in sel).items()))}
out['commercial311'] = {'cb6_total': len(cp), 'cb6_noloc': sum(1 for c in cp if not fpt(c)), 'by': c311, 'first': min(c['created_date'][:10] for c in cp), 'last': max(c['created_date'][:10] for c in cp),
                        'pts': [[round(float(c['latitude']), 6), round(float(c['longitude']), 6), c['created_date'][:10], c['descriptor'], c.get('incident_address') or c.get('street_name') or '', c['unique_key']]
                                for c in cp if fpt(c) and any(g.contains(Point(float(c['longitude']), float(c['latitude']))) for g in NBG.values())]}
print('commercial 311', out['commercial311']['cb6_total'], c311)
json.dump(out, open(os.path.join(ROOT, 'data', 'bqe', 'enforcement.json'), 'w'), separators=(',', ':'))
