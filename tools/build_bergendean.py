#!/usr/bin/env python3
"""Build data/bergendean/*.json for bkcb6.app/bergndeanblvd (the Dean and Bergen bike boulevard page).
Corridor = Bergen Street and Dean Street in Brooklyn as drawn in the NYC street centerline (CSCL, inkn-q76z).
Block = Bergen Street between 4th Avenue and 5th Avenue, cut from that centerline at the 4 AVE and 5 AVE centerlines.
"On the block" and "on the corridor" = within 100 feet of those centerlines (includes the intersections).
Every count is the result of a stored NYC Open Data / NY Open Data query, saved with its URL."""
import json, os, urllib.request, urllib.parse, collections
from shapely.geometry import shape, mapping, Point
from shapely.ops import unary_union, linemerge, substring, transform
from pyproj import Transformer, Geod
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'bergendean')
NYC = 'https://data.cityofnewyork.us/resource/'; NYS = 'https://data.ny.gov/resource/'
TO = Transformer.from_crs(4326, 2263, always_xy=True); BACK = Transformer.from_crs(2263, 4326, always_xy=True)
P = lambda g: transform(lambda x, y, z=None: TO.transform(x, y), g); U = lambda g: transform(lambda x, y, z=None: BACK.transform(x, y), g)
G = Geod(ellps='WGS84')
import datetime
from zoneinfo import ZoneInfo
END = datetime.datetime.now(ZoneInfo('America/New_York')).date().isoformat() + 'T00:00:00'  # every query stops at the start of the build day, so counts and map points match
def url(base, ds, q): return base + ds + '.json?' + urllib.parse.urlencode(q)
def get(u): return json.load(urllib.request.urlopen(u, timeout=600))
def cl(name):
    return get(url(NYC, 'inkn-q76z', {'$select': 'physicalid,full_street_name,the_geom', '$where': f"full_street_name='{name}' AND boroughcode='3'", '$limit': 5000}))
bergen = linemerge(unary_union([shape(x['the_geom']) for x in cl('BERGEN ST')]))
dean = linemerge(unary_union([shape(x['the_geom']) for x in cl('DEAN ST')]))
a4 = unary_union([shape(x['the_geom']) for x in cl('4 AVE')]); a5 = unary_union([shape(x['the_geom']) for x in cl('5 AVE')])
def pt(g): return g if g.geom_type == 'Point' else list(g.geoms)[0]
p4, p5 = pt(bergen.intersection(a4)), pt(bergen.intersection(a5))
block = substring(bergen, min(bergen.project(p4), bergen.project(p5)), max(bergen.project(p4), bergen.project(p5)))
def buf(g, ft=100, tol=0.00003): return U(P(g).buffer(ft)).simplify(tol, preserve_topology=True)
def wkt(g):
    parts = [q for q in getattr(g, 'geoms', [g]) if q.geom_type == 'Polygon']
    return 'MULTIPOLYGON(' + ','.join('((' + ','.join('%.6f %.6f' % c for c in q.exterior.coords) + '))' for q in parts) + ')'
AREAS = {'block': buf(block), 'bergen': buf(bergen), 'dean': buf(dean)}
CB6 = [shape(f['geometry']).buffer(0) for f in json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features'] if str(f['properties']['cd']) == '306'][0].simplify(0.00002, preserve_topology=True)
AREAS['cb6'] = CB6 if CB6.geom_type == 'Polygon' else max(CB6.geoms, key=lambda g: g.area)
W = {k: wkt(v) for k, v in AREAS.items()}
out = {'lengths_mi': {'bergen': round(G.geometry_length(bergen) / 1609.344, 2), 'dean': round(G.geometry_length(dean) / 1609.344, 2), 'block_ft': round(G.geometry_length(block) * 3.28084)}}
geo = {'type': 'FeatureCollection', 'features': [
    {'type': 'Feature', 'properties': {'k': 'bergen', 'name': 'Bergen Street'}, 'geometry': mapping(bergen)},
    {'type': 'Feature', 'properties': {'k': 'dean', 'name': 'Dean Street'}, 'geometry': mapping(dean)},
    {'type': 'Feature', 'properties': {'k': 'block', 'name': 'Bergen Street, 4th Avenue to 5th Avenue'}, 'geometry': mapping(block)}]}
json.dump(geo, open(os.path.join(OUT, 'corridor.geojson'), 'w'), separators=(',', ':'))
# ---- districts crossed and near the block
files = [('cd', 'data/community-districts.geojson', 'boro_cd'), ('council', 'data/council-districts.geojson', 'cc'), ('senate', 'data/senate-districts.geojson', 'sd'),
         ('assembly', 'data/assembly-districts.geojson', 'ad'), ('precinct', 'data/police-precincts-citywide.geojson', 'precinct'), ('congress', 'data/congress-districts-simple.geojson', 'cong_dist')]
bp = P(block); samp = [bp.interpolate(i / 40, normalized=True) for i in range(41)]
dist = {}
for key, f, k in files:
    fs = [(str(int(float(x['properties'][k]))), P(shape(x['geometry'])).buffer(0)) for x in json.load(open(os.path.join(ROOT, f)))['features']]
    cor = {}
    for nm, L in (('bergen', P(bergen)), ('dean', P(dean))):
        cor[nm] = {i: round(L.intersection(g).length / 5280, 2) for i, g in fs if L.intersection(g).length > 30}
    own = [i for i, g in fs if g.contains(bp.interpolate(0.5, normalized=True))]
    near = sorted([(i, round(bp.distance(g)), round(max(p.distance(g) for p in samp))) for i, g in fs if i not in own and bp.distance(g) < 3000], key=lambda x: x[1])
    # label point for each district: the middle of the longer street's run through it
    lab = {}
    for i, g in fs:
        best = None
        for L in (P(bergen), P(dean)):
            seg = L.intersection(g)
            if seg.length > 30 and (best is None or seg.length > best.length): best = seg
        if best is not None:
            m = U(best.interpolate(0.5, normalized=True)) if best.geom_type == 'LineString' else U(max(best.geoms, key=lambda x: x.length).interpolate(0.5, normalized=True))
            lab[i] = [round(m.y, 6), round(m.x, 6)]
    dist[key] = {'corridor': cor, 'block': own, 'near': near[:4], 'label': lab}
out['districts'] = dist
# ---- crashes (h9gi-nx95), 2020 to latest
CSEL = 'date_extract_y(crash_date) as year,count(*) as crashes,sum(number_of_persons_injured) as injured,sum(number_of_persons_killed) as killed,sum(number_of_cyclist_injured) as cyc_inj,sum(number_of_cyclist_killed) as cyc_kil,sum(number_of_pedestrians_injured) as ped_inj,sum(number_of_pedestrians_killed) as ped_kil'
crash = {}
for k in ('block', 'bergen', 'dean', 'cb6'):
    u = url(NYC, 'h9gi-nx95', {'$select': CSEL, '$where': f"crash_date>='2020-01-01T00:00:00' AND crash_date<'{END}' AND within_polygon(location,'{W[k]}')", '$group': 'year', '$order': 'year'})
    rows = get(u); crash[k] = {'url': u, 'rows': [{kk: (int(float(v)) if kk != 'year' else v) for kk, v in r.items()} for r in rows]}
    crash[k]['total'] = {f: sum(r.get(f, 0) for r in crash[k]['rows']) for f in ('crashes', 'injured', 'killed', 'cyc_inj', 'cyc_kil', 'ped_inj', 'ped_kil')}
    print('crash', k, crash[k]['total'])
out['crash_last'] = get(url(NYC, 'h9gi-nx95', {'$select': 'max(crash_date) as d', '$where': f"crash_date<'{END}'"}))[0]['d'][:10]
out['crashes'] = crash
# ---- 311 (erm2-nwe9), 2020 to latest
s311 = {}
for k in ('block', 'bergen', 'dean'):
    ut = url(NYC, 'erm2-nwe9', {'$select': 'complaint_type,count(*) as n', '$where': f"created_date>='2020-01-01T00:00:00' AND created_date<'{END}' AND within_polygon(location,'{W[k]}')", '$group': 'complaint_type', '$order': 'n DESC', '$limit': 400})
    uy = url(NYC, 'erm2-nwe9', {'$select': 'date_extract_y(created_date) as year,count(*) as n', '$where': f"created_date>='2020-01-01T00:00:00' AND created_date<'{END}' AND within_polygon(location,'{W[k]}')", '$group': 'year', '$order': 'year'})
    s311[k] = {'types_url': ut, 'types': [[r['complaint_type'], int(r['n'])] for r in get(ut)], 'year_url': uy, 'years': [[r['year'], int(r['n'])] for r in get(uy)]}
    s311[k]['total'] = sum(n for _, n in s311[k]['years']); print('311', k, s311[k]['total'], s311[k]['types'][:3])
um = url(NYC, 'erm2-nwe9', {'$select': "date_trunc_ym(created_date) as month,count(*) as n", '$where': f"created_date>='2020-01-01T00:00:00' AND created_date<'{END}' AND within_polygon(location,'{W['block']}')", '$group': 'month', '$order': 'month'})
s311['block']['month_url'] = um; s311['block']['months'] = [[r['month'][:7], int(r['n'])] for r in get(um)]
out['s311'] = s311; out['s311_last'] = get(url(NYC, 'erm2-nwe9', {'$select': 'max(created_date) as d', '$where': f"created_date<'{END}'"}))[0]['d'][:10]
# ---- NYPD complaints near the block (historic qgea-i56i from 2020, plus year to date 5uac-w243)
crime = {}
for ds, col in (('qgea-i56i', 'lat_lon'), ('5uac-w243', 'lat_lon')):
    wh = f"cmplnt_fr_dt>='2020-01-01T00:00:00' AND cmplnt_fr_dt<'{END}' AND within_polygon({col},'{W['block']}')"
    uy = url(NYC, ds, {'$select': 'date_extract_y(cmplnt_fr_dt) as year,law_cat_cd,count(*) as n', '$where': wh, '$group': 'year,law_cat_cd', '$order': 'year'})
    uo = url(NYC, ds, {'$select': 'ofns_desc,count(*) as n', '$where': wh, '$group': 'ofns_desc', '$order': 'n DESC', '$limit': 100})
    um = url(NYC, ds, {'$select': 'date_trunc_ym(cmplnt_fr_dt) as month,count(*) as n', '$where': wh, '$group': 'month', '$order': 'month'})
    crime[ds] = {'year_url': uy, 'years': get(uy), 'ofns_url': uo, 'ofns': get(uo), 'month_url': um, 'months': get(um)}
    print('crime', ds, sum(int(r['n']) for r in crime[ds]['years']))
out['crime'] = crime
# ---- bus speeds (MTA, data.ny.gov): route-level monthly speed = sum(distance x trips) / sum(time x trips)
bus = {}
for ds in ('58t6-89vi', 'kufs-yh3x'):
    for r_ in ('B65', 'B63', 'B41', 'B45'):
        u = url(NYS, ds, {'$select': 'year,month,sum(road_distance*bus_trip_count) as dt,sum(average_travel_time*bus_trip_count) as tt,sum(bus_trip_count) as trips', '$where': f"route_id='{r_}'", '$group': 'year,month', '$order': 'year,month'})
        rows = get(u)
        bus.setdefault(r_, {'urls': [], 'months': []}); bus[r_]['urls'].append(u)
        bus[r_]['months'] += [[f"{r['year']}-{int(r['month']):02d}", round(float(r['dt']) / float(r['tt']) * 60, 2)] for r in rows if float(r.get('tt') or 0) > 0]
    print('bus', r_, len(bus[r_]['months']))
out['bus'] = bus
# ---- truck routes on the corridor (repo per-district files from NYC DOT truck routes) and Oct 4, 2026 changes
tr = collections.defaultdict(lambda: collections.Counter())
cds = sorted(set(i for d in dist['cd']['corridor'].values() for i in d))
for cd in cds:
    fp = os.path.join(ROOT, 'data', 'truck-routes', cd + '.json')
    if not os.path.exists(fp): continue
    for f in json.load(open(fp))['features']:
        st = f['properties'].get('street', '')
        if st in ('BERGEN STREET', 'DEAN STREET') and f.get('geometry'):
            tr[st][f['properties'].get('routetype')] += 1
blk_routes = []
fp = os.path.join(ROOT, 'data', 'truck-routes', '306.json')
for f in json.load(open(fp))['features']:
    if f.get('geometry') and P(shape(f['geometry'])).distance(bp.interpolate(0.5, normalized=True)) < 40:
        blk_routes.append([f['properties'].get('street'), f['properties'].get('routetype')])
chg = json.load(open(os.path.join(ROOT, 'data', 'truck-routes', 'changes-2026-10-04.json')))['entries']
cor = P(unary_union([bergen, dean]))
near_chg = [[e['kind'], e['text']] for e in chg if e.get('geometry') and P(shape(e['geometry'])).distance(cor) < 60]
out['trucks'] = {'cds': cds, 'segments': {k: dict(v) for k, v in tr.items()}, 'block': blk_routes, 'oct4_on_corridor': near_chg, 'oct4_total': len(chg)}
print('trucks', out['trucks'])
out['wkt'] = W
json.dump(out, open(os.path.join(OUT, 'summary.json'), 'w'), separators=(',', ':'))
# ---- map points: crashes on the corridor and 311 on the block (same areas and dates as the counts)
pts = {'crashes': [], 's311': []}
seen = set()
for k in ('bergen', 'dean', 'block'):
    u = url(NYC, 'h9gi-nx95', {'$select': 'collision_id,crash_date,latitude,longitude,on_street_name,cross_street_name,number_of_persons_injured,number_of_persons_killed,number_of_cyclist_injured,number_of_pedestrians_injured', '$where': f"crash_date>='2020-01-01T00:00:00' AND crash_date<'{END}' AND within_polygon(location,'{W[k]}')", '$limit': 50000})
    for r in get(u):
        if r['collision_id'] in seen: continue
        seen.add(r['collision_id'])
        pts['crashes'].append([round(float(r['latitude']), 6), round(float(r['longitude']), 6), r['crash_date'][:10], (r.get('on_street_name') or '').strip(), (r.get('cross_street_name') or '').strip(),
                               int(r.get('number_of_persons_injured') or 0), int(r.get('number_of_persons_killed') or 0), int(r.get('number_of_cyclist_injured') or 0), int(r.get('number_of_pedestrians_injured') or 0), r['collision_id']])
u = url(NYC, 'erm2-nwe9', {'$select': 'unique_key,created_date,complaint_type,descriptor,incident_address,latitude,longitude', '$where': f"created_date>='2020-01-01T00:00:00' AND created_date<'{END}' AND within_polygon(location,'{W['block']}')", '$limit': 50000})
pts['s311'] = [[round(float(r['latitude']), 6), round(float(r['longitude']), 6), r['created_date'][:10], r.get('complaint_type', ''), r.get('descriptor', ''), r.get('incident_address', ''), r['unique_key']] for r in get(u) if r.get('latitude')]
json.dump(pts, open(os.path.join(OUT, 'points.json'), 'w'), separators=(',', ':'))
print('points', len(pts['crashes']), len(pts['s311']))
