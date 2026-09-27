#!/usr/bin/env python3
"""Map layers for bkcb6.app/bergndeanblvd: MTA bus stops and routes (data.ny.gov 2ucp-7wg5, bzwk-3hb4, in effect),
subway lines and stations (repo files), NYC DOT bike routes (mzxg-pwib), NYC DOT speed limits (repo per-district
files from 5mad-ntua) and Citi Bike stations (repo GBFS snapshot), all clipped to the area around Bergen and Dean."""
import json, os, urllib.request, urllib.parse, collections
from shapely.geometry import shape, mapping, box, Point
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'bergendean')
cor = json.load(open(os.path.join(OUT, 'corridor.geojson')))
from shapely.ops import unary_union
C = unary_union([shape(f['geometry']) for f in cor['features']])
AREA = C.buffer(0.006)          # about 500 m either side of the corridor
bx = AREA.bounds
def get(u): return json.load(urllib.request.urlopen(u, timeout=600))
def q(base, ds, p): return base + ds + '.json?' + urllib.parse.urlencode(p)
def rnd(g, n=5):
    import shapely
    return json.loads(json.dumps(mapping(shapely.set_precision(g, 10 ** -n))))
layers = {}
# bus stops in effect
stops = get(q('https://data.ny.gov/resource/', '2ucp-7wg5', {'$select': 'stop_id,stop_name,route_short_name,latitude,longitude', '$where': f"in_effect='true' AND revenue_stop='1' AND latitude between {bx[1]} and {bx[3]} AND longitude between {bx[0]} and {bx[2]}", '$limit': 50000}))
S = {}
for r in stops:
    p = Point(float(r['longitude']), float(r['latitude']))
    if not AREA.contains(p): continue
    s = S.setdefault(r['stop_id'], {'n': r['stop_name'], 'll': [round(float(r['latitude']), 6), round(float(r['longitude']), 6)], 'r': set()})
    s['r'].add(r['route_short_name'])
layers['bus_stops'] = [[v['ll'][0], v['ll'][1], v['n'], sorted(v['r'])] for v in S.values()]
routes_here = sorted(set(r for v in S.values() for r in v['r']))
# bus route shapes in effect for those routes, clipped
rs = get(q('https://data.ny.gov/resource/', 'bzwk-3hb4', {'$select': 'route_short_name,route_color,direction_id,shape_id,vertices,geometry', '$where': "in_effect='true' AND route_short_name in(" + ','.join("'%s'" % r for r in routes_here) + ")", '$limit': 5000}))
best = {}
for r in rs:
    k = (r['route_short_name'], r['direction_id'])
    if k not in best or int(float(r['vertices'])) > int(float(best[k]['vertices'])): best[k] = r
feats = []
byroute = {}
for (rt, d), r in sorted(best.items()): byroute.setdefault(rt, []).append(r)
for rt, rr in sorted(byroute.items()):
    g = unary_union([shape(r['geometry']) for r in rr]).intersection(AREA)  # both directions, so one-way pairs like the B65 on Bergen and Dean both show
    if g.is_empty: continue
    feats.append({'type': 'Feature', 'properties': {'r': rt, 'c': '#' + (rr[0].get('route_color') or '0d1b4b'), 'dirs': len(rr)}, 'geometry': rnd(g)})
layers['bus_routes'] = {'type': 'FeatureCollection', 'features': feats}
# subway
sub = json.load(open(os.path.join(ROOT, 'data', 'nyc-subway-routes.geojson')))
layers['subway_lines'] = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'n': f['properties'].get('name'), 'c': f['properties'].get('color')}, 'geometry': rnd(shape(f['geometry']).intersection(AREA))} for f in sub['features'] if f.get('geometry') and shape(f['geometry']).intersects(AREA)]}
st = json.load(open(os.path.join(ROOT, 'data', 'nyc-subway-stations.geojson')))
layers['subway_stops'] = [[round(f['geometry']['coordinates'][1], 6), round(f['geometry']['coordinates'][0], 6), f['properties'].get('display_name') or f['properties'].get('stop_name'), f['properties'].get('daytime_routes') or f['properties'].get('routes'), f['properties'].get('ada')] for f in st['features'] if AREA.contains(Point(f['geometry']['coordinates'][:2]))]
# bike routes (NYC DOT), current
bk = get(q('https://data.cityofnewyork.us/resource/', 'mzxg-pwib', {'$select': 'street,fromstreet,tostreet,facilitycl,ft_facilit,tf_facilit,the_geom', '$where': f"boro='3' AND within_box(the_geom,{bx[3]},{bx[0]},{bx[1]},{bx[2]})", '$limit': 50000}))
bf = []
for r in bk:
    g = shape(r['the_geom']).intersection(AREA)
    if g.is_empty: continue
    bf.append({'type': 'Feature', 'properties': {'s': r.get('street'), 'f': r.get('fromstreet'), 't': r.get('tostreet'), 'cl': r.get('facilitycl'), 'ty': r.get('ft_facilit') or r.get('tf_facilit')}, 'geometry': rnd(g)})
layers['bike'] = {'type': 'FeatureCollection', 'features': bf}
layers['bike_query'] = q('https://data.cityofnewyork.us/resource/', 'mzxg-pwib', {'$select': 'street,fromstreet,tostreet,facilitycl,ft_facilit,tf_facilit', '$where': f"boro='3' AND within_box(the_geom,{bx[3]},{bx[0]},{bx[1]},{bx[2]})", '$limit': 50000})
# speed limits (repo per-district files from NYC DOT VZV_Speed Limits)
sf = []
for cd in ('302', '306', '308', '316', '303', '309', '317', '355'):
    fp = os.path.join(ROOT, 'data', 'speed-limits', cd + '.json')
    if not os.path.exists(fp): continue
    for f in json.load(open(fp))['features']:
        g = shape(f['geometry'])
        if g.intersects(AREA): sf.append({'type': 'Feature', 'properties': {'s': f['properties'].get('street'), 'sl': f['properties'].get('sl'), 'sz': f['properties'].get('sz')}, 'geometry': rnd(g)})
layers['speed'] = {'type': 'FeatureCollection', 'features': sf}
# Citi Bike stations (repo GBFS snapshot)
cb = json.load(open(os.path.join(ROOT, 'data', 'citibike_station_information.json')))
layers['citibike'] = [[round(s['lat'], 6), round(s['lon'], 6), s['name'], s.get('capacity')] for s in cb['data']['stations'] if AREA.contains(Point(s['lon'], s['lat']))]
layers['citibike_updated'] = cb.get('last_updated')
json.dump(layers, open(os.path.join(OUT, 'layers.json'), 'w'), separators=(',', ':'))
print({k: (len(v['features']) if isinstance(v, dict) and 'features' in v else len(v) if isinstance(v, list) else v) for k, v in layers.items() if k != 'bike_query'}, routes_here, os.path.getsize(os.path.join(OUT, 'layers.json')) // 1024, 'KB')
