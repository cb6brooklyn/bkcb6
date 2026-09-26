#!/usr/bin/env python3
"""Build data/bqe/ for bkcb6.app/BQE: BQE mainline and ramps by section, count locations,
CDs along the BQE, and citywide 311 Truck Route Violation complaints."""
import json, glob, urllib.request, urllib.parse, collections, os
from shapely.geometry import shape, mapping, Point, LineString
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'bqe')
os.makedirs(OUT, exist_ok=True)

def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

# ---- 1. BQE mainline + ramps from the DOT truck route files -------------------
MAIN = {'BROOKLYN QUEENS EXPRESSWAY', 'BROOKLYN QUEENS EXPRESSWAY EAST', 'BROOKLYN QUEENS EXPRESSWAY WEST',
        'GOWANUS EXPRESSWAY', 'KOSCIUSZKO BRIDGE'}
def is_ramp(s):
    return (s.startswith('BQE ') or s.startswith('BROOKLYN QUEENS EP ') or s.startswith('BROOKLYN QUEENS EXPWY ')
            or s.startswith('BROOKLYN QUEENS EXPRESSWAY EN') or s.startswith('GOWANUS EP ') or s.startswith('GOWANUS EXPWY ')
            or (s.startswith('GOWANUS EXPRESSWAY ') and s != 'GOWANUS EXPRESSWAY') or s == 'HUGH L CAREY TUNNEL NB EN BQE')
# BQE Central limits (NYC DOT: Atlantic Avenue to Sands Street), from NYC Geoclient intersections
ATL = (-73.999203, 40.691573)   # Atlantic Avenue & Brooklyn Queens Expressway
SANDS = (-73.984651, 40.699836) # Sands Street & Brooklyn Queens Expressway
def section(s, borocd, mid):
    x, y = mid
    if s == 'KOSCIUSZKO BRIDGE': return 'kosciuszko'
    if str(borocd).startswith('4'): return 'queens'
    if y < ATL[1]: return 'south'
    if x <= SANDS[0]: return 'central'
    return 'north'
seen = set(); feats = []
for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'truck-routes', '*.json'))):
    d = json.load(open(f))
    if not isinstance(d, dict) or 'features' not in d: continue
    for ft in d['features']:
        p = ft['properties']; s = (p.get('street') or '').strip()
        kind = 'main' if s in MAIN else ('ramp' if is_ramp(s) else None)
        if not kind or not ft.get('geometry'): continue
        g = shape(ft['geometry'])
        key = (p.get('segmentid'), round(g.length, 9), s)
        if key in seen: continue
        seen.add(key)
        c = g.interpolate(0.5, normalized=True)
        sec = section(s, p.get('borocd'), (c.x, c.y))
        feats.append({'type': 'Feature', 'geometry': mapping(g),
                      'properties': {'k': kind, 'sec': sec, 'st': s, 'seg': p.get('segmentid'), 'cd': p.get('borocd')}})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(OUT, 'bqe-lines.geojson'), 'w'), separators=(',', ':'))
cnt = collections.Counter((f['properties']['k'], f['properties']['sec']) for f in feats)
print('lines', len(feats), dict(cnt))

# ---- 2. community districts the BQE mainline passes through -------------------
cds = json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))
mainline = unary_union([shape(f['geometry']) for f in feats if f['properties']['k'] == 'main'])
along = []
for f in cds['features']:
    g = shape(f['geometry'])
    if g.intersects(mainline) and g.intersection(mainline).length > 0.0015:
        along.append(str(f['properties']['cd']))
print('cds along', sorted(along))
OVF = {'council': ('data/council-districts.geojson', 'cc'), 'senate': ('data/senate-districts.geojson', 'sd'),
       'assembly': ('data/assembly-districts.geojson', 'ad'), 'congress': ('data/congress-districts-simple.geojson', 'cong_dist')}
ov = {}
for k, (fn, prop) in OVF.items():
    g = json.load(open(os.path.join(ROOT, fn))); ov[k] = []
    for f in g['features']:
        s = shape(f['geometry'])
        if not s.is_valid: s = s.buffer(0)
        hit = s.intersection(mainline)
        if hit.length > 0.0015:
            lp = s.intersection(mainline.buffer(0.004)).representative_point()
            ov[k].append({'d': int(float(f['properties'][prop])), 'lp': [round(lp.y, 5), round(lp.x, 5)]})
    ov[k].sort(key=lambda o: o['d'])
print({k: [o['d'] for o in v] for k, v in ov.items()})

# ---- 3. count locations ------------------------------------------------------
segs = {}
for f in feats: segs.setdefault(str(f['properties']['seg']), shape(f['geometry']))
for f in glob.glob(os.path.join(ROOT, 'data', 'truck-routes', '*.json')):
    d = json.load(open(f))
    if not isinstance(d, dict) or 'features' not in d: continue
    for ft in d['features']:
        if ft.get('geometry'): segs.setdefault(str(ft['properties'].get('segmentid')), shape(ft['geometry']))
def seg_pt(sid):
    g = segs.get(str(sid))
    if g is None: return None
    c = g.interpolate(0.5, normalized=True); return [round(c.y, 6), round(c.x, 6)]
def atr_pt(sid):
    q = urllib.parse.urlencode({'segmentid': sid, '$select': 'wktgeom', '$limit': 1})
    r = get('https://data.cityofnewyork.us/resource/7ym2-wayt.json?' + q)
    if not r: return None
    wkt = r[0]['wktgeom']
    from shapely import wkt as W
    from pyproj import Transformer
    g = W.loads(wkt); c = g.interpolate(0.5, normalized=True) if g.geom_type != 'Point' else g
    lon, lat = Transformer.from_crs(2263, 4326, always_xy=True).transform(c.x, c.y)
    return [round(lat, 6), round(lon, 6)]
GEO = 'b913bdfb9c47466589d0f08c99c75b21'
from shapely.ops import nearest_points
def on_main(lat, lon, names=None):
    ls = unary_union([shape(f['geometry']) for f in feats if f['properties']['k'] == 'main' and (not names or f['properties']['st'] in names)])
    p = nearest_points(ls, Point(lon, lat))[0]; return [round(p.y, 6), round(p.x, 6)]
def kos():
    g = unary_union([shape(f['geometry']) for f in feats if f['properties']['st'] == 'KOSCIUSZKO BRIDGE'])
    c = g.centroid; p = nearest_points(g, c)[0]; return [round(p.y, 6), round(p.x, 6)]
def ix(a, b):
    for comp in (None, 'E', 'W', 'N', 'S'):
        prm = {'crossStreetOne': a, 'crossStreetTwo': b, 'borough': 'Brooklyn', 'subscription-key': GEO}
        if comp: prm['compassDirection'] = comp
        d = get('https://api.nyc.gov/geoclient/v2/intersection.json?' + urllib.parse.urlencode(prm), {'Referer': 'https://bkcb6.app/'})['intersection']
        if d.get('latitude'): return float(d['latitude']), float(d['longitude'])
    raise ValueError('no intersection %s / %s' % (a, b))
def mid(a, b, c):
    p1 = ix(a, b); p2 = ix(a, c); return [round((p1[0] + p2[0]) / 2, 6), round((p1[1] + p2[1]) / 2, 6)]
V = 'https://data.cityofnewyork.us/resource/96ay-ea4r.json?segmentid='
W21 = '&$where=date%3E%3D%272021-01-01%27'
A = 'https://data.cityofnewyork.us/resource/7ym2-wayt.json?'
counts = [
 # BQE mainline
 dict(g='bqe', name='Kosciuszko Bridge', pt=seg_pt('144290') or kos(), date='Nov 5, 2014', rows=[
   ['Northbound', '49,493', '5,667', '2,262', V+'144290'], ['Southbound', '47,694', '5,080', '1,535', V+'135718']]),
 dict(g='bqe', name='BQE at Joralemon Street', pt=atr_pt('142655'), date='May 3 to 11, 2025', note='Automated count, vehicles not classified', rows=[
   ['Northbound', '63,346', None, None, A+'boro=Brooklyn&street=BROOKLYN%20QUEENS%20EXPRESSWAY&yr=2025&$limit=5000'],
   ['Southbound', '65,711', None, None, A+'boro=Brooklyn&street=BROOKLYN%20QUEENS%20EXPRESSWAY&yr=2025&$limit=5000']]),
 dict(g='bqe', name='BQE, Kane Street to Sackett Street', pt=seg_pt('143432') or on_main(*mid('Hicks Street', 'Kane Street', 'Sackett Street')), date='Apr 4 to 5, 2023', rows=[
   ['Northbound', '49,510', '5,628', '2,406', V+'143432'], ['Southbound', '73,162', '6,101', '2,210', V+'143431']]),
 # CB6 streets
 dict(g='street', name='Hicks Street, Degraw to Kane', pt=seg_pt('22227') or mid('Hicks Street', 'De Graw Street', 'Kane Street'), date='Mar and Apr 2025', rows=[
   ['Northbound (Apr 23 to 24)', '15,142', '502', '72', V+'22227'], ['Southbound (Mar 25 to 26)', '1,386', '38', '2', V+'22221']]),
 dict(g='street', name='Court Street, Sackett to Union', pt=seg_pt('22407') or mid('Court Street', 'Sackett Street', 'Union Street'), date='Mar 25 to 26, 2025', rows=[
   ['Southbound', '6,156', '351', '35', V+'22407']]),
 dict(g='street', name='Smith Street, Sackett to Degraw', pt=seg_pt('22539') or mid('Smith Street', 'Sackett Street', 'De Graw Street'), date='Mar 25 to 26, 2025', rows=[
   ['Northbound', '5,309', '286', '26', V+'22539']]),
 dict(g='street', name='Columbia Street, Kane to Degraw', pt=seg_pt('22023') or mid('Columbia Street', 'Kane Street', 'De Graw Street'), date='Nov 20, 2019', rows=[
   ['Southbound', '6,543', '675', '164', V+'22023&direction=SB'], ['Northbound', '5,576', '427', '78', V+'22023&direction=NB']]),
 dict(g='street', name='Hamilton Avenue, 14 Street to body of water', pt=seg_pt('22096') or list(ix('Hamilton Avenue', '14 Street')), date='Oct 8, 2015', rows=[
   ['Northbound', '37,402', '2,574', '848', V+'22096'], ['Southbound', '21,692', '1,864', '574', V+'187982']]),
 dict(g='street', name='3rd Avenue, Baltic to Butler', pt=seg_pt('22806') or mid('3 Avenue', 'Baltic Street', 'Butler Street'), date='Jan 19, 2021', rows=[
   ['Northbound', '4,623', '389', '52', V+'22806'+W21], ['Southbound', '2,801', '147', '8', V+'22806'+W21]]),
 dict(g='street', name='Union Street, Hoyt to Bond', pt=mid('Union Street', 'Hoyt Street', 'Bond Street'), date='Jan 19, 2021', rows=[
   ['Eastbound', '2,909', '134', '5', V+'22534'+W21]]),
]
for c in counts: print(c['name'], c['pt'])
json.dump({'counts': counts, 'along': sorted(along), 'ov': ov}, open(os.path.join(OUT, 'counts.json'), 'w'), indent=1)

# ---- 4. citywide 311 Truck Route Violation complaints --------------------------
rows = []; off = 0
while True:
    q = urllib.parse.urlencode({'$select': 'unique_key,created_date,incident_address,street_name,cross_street_1,community_board,latitude,longitude',
                                '$where': "descriptor='Truck Route Violation'", '$order': 'unique_key', '$limit': 50000, '$offset': off})
    r = get('https://data.cityofnewyork.us/resource/erm2-nwe9.json?' + q)
    rows += r
    if len(r) < 50000: break
    off += 50000
pts = []; nogeo = 0
for r in rows:
    if not r.get('latitude') or not r.get('longitude'): nogeo += 1; continue
    pts.append([round(float(r['latitude']), 6), round(float(r['longitude']), 6), r['created_date'][:10],
                r.get('incident_address') or r.get('street_name') or '', r.get('community_board') or '', r['unique_key']])
json.dump({'total': len(rows), 'no_location': nogeo, 'first': min(p[2] for p in pts), 'last': max(p[2] for p in pts), 'p': pts},
          open(os.path.join(OUT, 'truck-complaints.json'), 'w'), separators=(',', ':'))
print('complaints', len(rows), 'mapped', len(pts), 'no location', nogeo)
