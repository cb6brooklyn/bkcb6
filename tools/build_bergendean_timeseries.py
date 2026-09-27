"""Time series for bkcb6.app/bergndeanblvd so the page can show any window (last 12 months by default, or longer)
and break it down by month, by day and by day of the week. Writes data/bergendean/timeseries.json.

Crashes: NYPD Motor Vehicle Collisions (h9gi-nx95), every crash with a mapped point within 100 ft of Bergen or Dean
since January 1, 2013 (the file begins July 2012), each counted once on its nearest block.
311: the 2010 to 2019 file (76ig-c548) and the 2020 to present file (erm2-nwe9), same band, same rule.
Comparison areas: the four community districts the corridor crosses and Brooklyn, by month, from the same files."""
import json, os, urllib.request, urllib.parse, collections, datetime, time
from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, 'data', 'bergendean')
NYC = 'https://data.cityofnewyork.us/resource/'
def url(ds, q): return NYC + ds + '.json?' + urllib.parse.urlencode(q)
def get(u):
    for i in range(3):
        try: return json.load(urllib.request.urlopen(u, timeout=900))
        except Exception as e: err = e; time.sleep(5)
    raise err
S = json.load(open(os.path.join(OUT, 'summary.json'))); BK = json.load(open(os.path.join(OUT, 'blocks.json'))); CX = S['context']
START = '2013-01-01T00:00:00'
END = S['end'] if 'T' in S.get('end', '') else datetime.datetime.now(datetime.timezone.utc).date().isoformat() + 'T00:00:00'
S311 = (('76ig-c548', START, '2020-01-01T00:00:00'), ('erm2-nwe9', '2020-01-01T00:00:00', END))
TO = Transformer.from_crs(4326, 2263, always_xy=True); P = lambda g: transform(lambda x, y, z=None: TO.transform(x, y), g)
lines = [P(shape(f['geometry'])) for f in BK['geo']['features']]; tree = STRtree(lines); NB = len(lines)
def nearest(lon, lat):
    pt = P(Point(lon, lat)); i = int(tree.nearest(pt)); return i if lines[i].distance(pt) <= 100 else None
# month index
def months_between(a, b):
    y, m = int(a[:4]), int(a[5:7]); out = []
    while (y, m) <= (int(b[:4]), int(b[5:7])): out.append('%d-%02d' % (y, m)); m += 1; (y, m) = (y + 1, 1) if m == 13 else (y, m)
    return out
crash_last = get(url('h9gi-nx95', {'$select': 'max(crash_date) as d', '$where': f"crash_date<'{END}'"}))[0]['d'][:10]
s311_last = get(url('erm2-nwe9', {'$select': 'max(created_date) as d', '$where': f"created_date<'{END}'"}))[0]['d'][:10]
CM = months_between(START, crash_last); SM = months_between(START, s311_last); cmi = {m: i for i, m in enumerate(CM)}; smi = {m: i for i, m in enumerate(SM)}
print('months', len(CM), len(SM), crash_last, s311_last)
# ---- crashes on the corridor, point by point
CSEL = 'collision_id,crash_date,crash_time,latitude,longitude,number_of_persons_injured,number_of_persons_killed,number_of_cyclist_injured,number_of_pedestrians_injured'
crash_urls = {}; seen = set(); crashes = []
for k in ('bergen', 'dean'):
    u = url('h9gi-nx95', {'$select': CSEL, '$where': f"crash_date>='{START}' AND crash_date<'{END}' AND within_polygon(location,'{S['wkt'][k]}')", '$limit': 100000}); crash_urls[k] = u
    for r in get(u):
        if r['collision_id'] in seen or not r.get('latitude'): continue
        seen.add(r['collision_id']); crashes.append((k, r))
print('crashes', len(crashes))
blk_cm = [[[0, 0, 0, 0, 0] for _ in CM] for _ in range(NB)]           # per block per month: n, injured, cyclists, pedestrians, killed
st_cd = {k: collections.Counter() for k in ('bergen', 'dean')}            # per street per day: n
st_ch = {k: [0] * 24 for k in ('bergen', 'dean')}                         # per street per hour (all time; the page filters hours by window from the daily+hour table below)
st_cdh = {k: collections.defaultdict(lambda: [0] * 24) for k in ('bergen', 'dean')}  # per street per month per hour
for k, r in crashes:
    b = nearest(float(r['longitude']), float(r['latitude'])); d = r['crash_date'][:10]; m = d[:7]
    if b is None or m not in cmi: continue
    v = blk_cm[b][cmi[m]]; v[0] += 1; v[1] += int(float(r.get('number_of_persons_injured') or 0)); v[2] += int(float(r.get('number_of_cyclist_injured') or 0)); v[3] += int(float(r.get('number_of_pedestrians_injured') or 0)); v[4] += int(float(r.get('number_of_persons_killed') or 0))
    sk = BK['blocks'][b]['sk']; st_cd[sk][d] += 1
    try: h = int((r.get('crash_time') or '0:00').split(':')[0]) % 24
    except ValueError: h = 0
    st_cdh[sk][m][h] += 1
# ---- 311 on the corridor, point by point, two files
s311_urls = {}; seen = set(); reqs = []
for ds, a, b in S311:
    for k in ('bergen', 'dean'):
        u = url(ds, {'$select': 'unique_key,created_date,complaint_type,latitude,longitude', '$where': f"created_date>='{a}' AND created_date<'{b}' AND within_polygon(location,'{S['wkt'][k]}')", '$limit': 500000}); s311_urls['%s_%s' % (k, ds)] = u
        for r in get(u):
            if r['unique_key'] in seen or not r.get('latitude'): continue
            seen.add(r['unique_key']); reqs.append((k, r))
        print('311', ds, k, len(reqs))
tcount = collections.Counter(r['complaint_type'] for _, r in reqs); TOPT = [t for t, _ in tcount.most_common(40)]; ti = {t: i for i, t in enumerate(TOPT)}
blk_sm = [[0] * len(SM) for _ in range(NB)]; blk_st = [[[0] * len(SM) for _ in range(len(TOPT) + 1)] for _ in range(NB)]  # per block per month; per block per type (top 14 + other) per month
st_sd = {k: collections.Counter() for k in ('bergen', 'dean')}; st_sdh = {k: collections.defaultdict(lambda: [0] * 24) for k in ('bergen', 'dean')}
for k, r in reqs:
    b = nearest(float(r['longitude']), float(r['latitude'])); d = r['created_date'][:10]; m = d[:7]
    if b is None or m not in smi: continue
    blk_sm[b][smi[m]] += 1; blk_st[b][ti.get(r['complaint_type'], len(TOPT))][smi[m]] += 1
    sk = BK['blocks'][b]['sk']; st_sd[sk][d] += 1; st_sdh[sk][m][int(r['created_date'][11:13])] += 1
# ---- comparison areas by month (aggregate queries)
from shapely.geometry import shape as _shape
def wkt(g):
    parts = [q for q in getattr(g, 'geoms', [g]) if q.geom_type == 'Polygon']
    return 'MULTIPOLYGON(' + ','.join('((' + ','.join('%.6f %.6f' % c for c in q.exterior.coords) + '))' for q in parts) + ')'
areas = {}
for f in json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features']:
    cd = str(f['properties'].get('cd'))
    if cd in ('302', '306', '308', '316'): areas[cd] = ('poly', wkt(_shape(f['geometry']).buffer(0).simplify(0.00002, preserve_topology=True)), CX['cds'][cd]['mi'])
areas['brooklyn'] = ('boro', None, CX['bk_street_mi']['mi'])
AR = {}
for a, (kind, wk, mi) in areas.items():
    cw = f"crash_date>='{START}' AND crash_date<'{END}' AND " + (f"within_polygon(location,'{wk}')" if kind == 'poly' else "borough='BROOKLYN'")
    um = url('h9gi-nx95', {'$select': 'date_trunc_ym(crash_date) as m,count(*) as n,sum(number_of_persons_injured) as inj,sum(number_of_cyclist_injured) as cyc,sum(number_of_pedestrians_injured) as ped,sum(number_of_persons_killed) as kil', '$where': cw, '$group': 'm', '$order': 'm', '$limit': 400})
    cm = [[0, 0, 0, 0, 0] for _ in CM]
    for r in get(um):
        if r['m'][:7] in cmi: cm[cmi[r['m'][:7]]] = [int(r['n']), int(float(r.get('inj') or 0)), int(float(r.get('cyc') or 0)), int(float(r.get('ped') or 0)), int(float(r.get('kil') or 0))]
    sm = [0] * len(SM); surls = []
    for ds, a1, b1 in S311:
        u = url(ds, {'$select': 'date_trunc_ym(created_date) as m,count(*) as n', '$where': f"created_date>='{a1}' AND created_date<'{b1}' AND " + (f"within_polygon(location,'{wk}')" if kind == 'poly' else "borough='BROOKLYN'"), '$group': 'm', '$order': 'm', '$limit': 400}); surls.append(u)
        for r in get(u):
            if r['m'][:7] in smi: sm[smi[r['m'][:7]]] += int(r['n'])
    AR[a] = {'mi': mi, 'crash_url': um, 'crash_m': cm, 's311_urls': surls, 's311_m': sm}
    print('area', a, sum(x[0] for x in cm), sum(sm))
# crashes without a borough label, by month, to state the Brooklyn floor
u = url('h9gi-nx95', {'$select': 'date_trunc_ym(crash_date) as m,count(*) as n', '$where': f"crash_date>='{START}' AND crash_date<'{END}' AND borough IS NULL", '$group': 'm', '$order': 'm', '$limit': 400}); nob = [0] * len(CM)
for r in get(u):
    if r['m'][:7] in cmi: nob[cmi[r['m'][:7]]] = int(r['n'])
u2 = url('h9gi-nx95', {'$select': 'date_trunc_ym(crash_date) as m,count(*) as n', '$where': f"crash_date>='{START}' AND crash_date<'{END}'", '$group': 'm', '$order': 'm', '$limit': 400}); allc = [0] * len(CM)
for r in get(u2):
    if r['m'][:7] in cmi: allc[cmi[r['m'][:7]]] = int(r['n'])
def daily(counter, first, last):
    d = datetime.date.fromisoformat(first); out = []
    while d <= datetime.date.fromisoformat(last): out.append(counter.get(d.isoformat(), 0)); d += datetime.timedelta(days=1)
    return out
out = {'built': END[:10], 'start': START[:10], 'crash_last': crash_last, 's311_last': s311_last, 'crash_months': CM, 's311_months': SM,
       'crash_urls': crash_urls, 's311_urls': s311_urls, 'types': TOPT,
       'blocks': [{'cm': blk_cm[i], 'sm': blk_sm[i], 'st': blk_st[i]} for i in range(NB)],
       'streets': {k: {'crash_daily': daily(st_cd[k], START[:10], crash_last), 's311_daily': daily(st_sd[k], START[:10], s311_last),
                       'crash_mh': [st_cdh[k].get(m, [0] * 24) for m in CM], 's311_mh': [st_sdh[k].get(m, [0] * 24) for m in SM], 'mi': S['lengths_mi'][k]} for k in ('bergen', 'dean')},
       'areas': AR, 'crash_noboro_m': nob, 'crash_all_m': allc, 'noboro_url': u, 'all_url': u2}
json.dump(out, open(os.path.join(OUT, 'timeseries.json'), 'w'), separators=(',', ':'))
print('size', os.path.getsize(os.path.join(OUT, 'timeseries.json')), 'corridor crashes counted', sum(v[0] for b in blk_cm for v in b), '311 counted', sum(sum(b) for b in blk_sm))
