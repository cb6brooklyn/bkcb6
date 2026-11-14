#!/usr/bin/env python3
"""The crash map in the apps (an Apple map, screens.json node "crashcount-map"), the same crashes CrashCount maps.

Every crash in NYPD's Motor Vehicle Collisions on NYC Open Data (h9gi-nx95) since January 1 of this year, the source
CrashCount uses. Writes to app/data/civic/crashcount/:
  boards.geojson  every community district, with this year's crashes, people injured and killed, pedestrians and
                  cyclists injured and killed (by the crash's coordinates; crashes with none are counted citywide only)
  deaths.geojson  every crash in which someone was killed, as a point
  squares.geojson every crash with someone injured or killed, counted in squares of about 400 meters
  summary.json    the citywide totals and the date range
Runs daily in app-feeds.yml. Usage: crashcount_map.py [saved rows.json]
"""
import datetime, json, os, sys, urllib.parse, urllib.request
from collections import defaultdict
from shapely.geometry import shape, Point, mapping
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'app/data/civic/crashcount')
TOKEN = 'HvFoIfzodzpRML7a1104Ca2tM'
YEAR = datetime.date.today().year
FIELDS = ('collision_id,crash_date,crash_time,on_street_name,cross_street_name,off_street_name,number_of_persons_injured,'
          'number_of_persons_killed,number_of_pedestrians_injured,number_of_pedestrians_killed,number_of_cyclist_injured,'
          'number_of_cyclist_killed,latitude,longitude')
BORO = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
SHORT = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}


def fetch():
    rows, off = [], 0
    while True:
        q = urllib.parse.urlencode({'$select': FIELDS, '$where': "crash_date >= '%d-01-01T00:00:00'" % YEAR, '$order': 'collision_id',
                                    '$limit': 50000, '$offset': off, '$$app_token': TOKEN})
        b = json.load(urllib.request.urlopen('https://data.cityofnewyork.us/resource/h9gi-nx95.json?' + q, timeout=300))
        rows += b; off += len(b)
        if len(b) < 50000: return rows


def n(r, k): return int(r.get(k) or 0)


def street(r):
    on, cross, offs = (r.get('on_street_name') or '').strip().title(), (r.get('cross_street_name') or '').strip().title(), (r.get('off_street_name') or '').strip().title()
    if on and cross: return '%s and %s' % (on, cross)
    return on or offs or cross or 'Street not recorded'


def day(r): return datetime.date.fromisoformat(r['crash_date'][:10]).strftime('%b %-d, %Y')


rows = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else fetch()
if not rows: sys.exit('no rows; files left as they were')
os.makedirs(OUT, exist_ok=True)

cds = json.load(open(os.path.join(ROOT, 'data/community-districts.geojson')))['features']
geoms = [shape(f['geometry']) for f in cds]
tree = STRtree(geoms)
tot = defaultdict(lambda: defaultdict(int))
deaths, squares = [], defaultdict(lambda: defaultdict(int))
city = defaultdict(int); located = 0
for r in rows:
    k = {'crashes': 1, 'injured': n(r, 'number_of_persons_injured'), 'killed': n(r, 'number_of_persons_killed'),
         'pedinj': n(r, 'number_of_pedestrians_injured'), 'pedkill': n(r, 'number_of_pedestrians_killed'),
         'cycinj': n(r, 'number_of_cyclist_injured'), 'cyckill': n(r, 'number_of_cyclist_killed')}
    for a, v in k.items(): city[a] += v
    try: lat, lon = float(r.get('latitude') or 0), float(r.get('longitude') or 0)
    except ValueError: lat = lon = 0
    if not (40.4 < lat < 41.0 and -74.3 < lon < -73.6): continue
    located += 1
    p = Point(lon, lat)
    for i in tree.query(p):
        if geoms[i].contains(p):
            for a, v in k.items(): tot[cds[i]['properties']['boro_cd']][a] += v
            break
    if k['killed']:
        deaths.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [round(lon, 6), round(lat, 6)]},
                       'properties': {'date': day(r), 'time': r.get('crash_time', ''), 'street': street(r), 'killed': k['killed'], 'injured': k['injured'],
                                      'who': ', '.join(x for x in [('%d pedestrian%s' % (k['pedkill'], '' if k['pedkill'] == 1 else 's')) if k['pedkill'] else '',
                                                                    ('%d cyclist%s' % (k['cyckill'], '' if k['cyckill'] == 1 else 's')) if k['cyckill'] else ''] if x)}})
    if k['injured'] or k['killed']:
        cell = (round(lon / 0.005) * 0.005, round(lat / 0.0036) * 0.0036)
        s = squares[cell]; s['crashes'] += 1; s['injured'] += k['injured']; s['killed'] += k['killed']

boards = []
for f, g in zip(cds, geoms):
    cd = f['properties']['boro_cd']
    if int(cd[1:]) > 18: continue  # parks, airports and other joint interest areas: counted citywide
    t = tot[cd]
    boards.append({'type': 'Feature', 'geometry': mapping(g.simplify(0.0003, preserve_topology=True)),
                   'properties': {'cd': cd, 'name': '%s Community Board %d' % (BORO[cd[0]], int(cd[1:])), 'short': '%sCB%d' % (SHORT[cd[0]], int(cd[1:])),
                                  'crashes': t['crashes'], 'injured': t['injured'], 'killed': t['killed'], 'pedinj': t['pedinj'], 'pedkill': t['pedkill'],
                                  'cycinj': t['cycinj'], 'cyckill': t['cyckill']}})
sq = []
for (x, y), s in squares.items():
    w, h = 0.0025, 0.0018
    sq.append({'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [[[round(x - w, 5), round(y - h, 5)], [round(x + w, 5), round(y - h, 5)],
               [round(x + w, 5), round(y + h, 5)], [round(x - w, 5), round(y + h, 5)], [round(x - w, 5), round(y - h, 5)]]]},
               'properties': dict(s)})


def dump(name, obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    for c in ['[[[', ']]]']: pass
    open(os.path.join(OUT, name), 'w', encoding='utf-8').write(s)


dates = sorted(r['crash_date'][:10] for r in rows)
summary = {'from': datetime.date.fromisoformat(dates[0]).strftime('%b %-d, %Y'), 'to': datetime.date.fromisoformat(dates[-1]).strftime('%b %-d, %Y'),
           'year': YEAR, 'crashes': city['crashes'], 'injured': city['injured'], 'killed': city['killed'], 'pedinj': city['pedinj'], 'pedkill': city['pedkill'],
           'cycinj': city['cycinj'], 'cyckill': city['cyckill'], 'located': located, 'deathCrashes': len(deaths), 'squares': len(sq),
           'source': 'NYPD Motor Vehicle Collisions, NYC Open Data (h9gi-nx95)'}
dump('boards.geojson', {'type': 'FeatureCollection', 'features': boards})
dump('deaths.geojson', {'type': 'FeatureCollection', 'features': deaths})
dump('squares.geojson', {'type': 'FeatureCollection', 'features': sq})
json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1)
print(json.dumps(summary))
