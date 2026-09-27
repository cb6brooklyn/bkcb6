"""NYC's built bike boulevards, for comparison with Dean and Bergen: each corridor's centerline (CSCL), the bike
facilities along it (NYC DOT bike routes), and crashes and 311 within 100 ft by month since 2013 (NYPD, 311 two files).
Writes data/bergendean/boulevards.json. Limits come from the sources named in SRC."""
import json, os, csv, urllib.request, urllib.parse, collections, datetime, time
from shapely.geometry import shape, mapping, Point, LineString
from shapely.ops import unary_union, linemerge, substring, transform
from shapely import wkt as shwkt
from pyproj import Transformer, Geod
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, 'data', 'bergendean')
NYC = 'https://data.cityofnewyork.us/resource/'
def url(ds, q): return NYC + ds + '.json?' + urllib.parse.urlencode(q)
def get(u):
    for i in range(3):
        try: return json.load(urllib.request.urlopen(u, timeout=900))
        except Exception as e: err = e; time.sleep(5)
    raise err
TO = Transformer.from_crs(4326, 2263, always_xy=True); BACK = Transformer.from_crs(2263, 4326, always_xy=True)
P = lambda g: transform(lambda x, y, z=None: TO.transform(x, y), g); U = lambda g: transform(lambda x, y, z=None: BACK.transform(x, y), g)
G = Geod(ellps='WGS84')
TS = json.load(open(os.path.join(OUT, 'timeseries.json'))); START = TS['start'] + 'T00:00:00'; CM = TS['crash_months']; SM = TS['s311_months']
END = datetime.datetime.now(datetime.timezone.utc).date().isoformat() + 'T00:00:00'
S311 = (('76ig-c548', START, '2020-01-01T00:00:00'), ('erm2-nwe9', '2020-01-01T00:00:00', END))
BLVDS = [
    {'id': 'berry', 'name': 'Berry Street', 'nbhd': 'Williamsburg, Brooklyn', 'boro': '3', 'street': 'BERRY ST', 'from': 'BROADWAY', 'to': 'N  12 ST', 'from_label': 'Broadway', 'to_label': 'North 12th Street', 'built': 'Opened November 2023',
     'src': [['NYC DOT press release, November 21, 2023', 'https://www.nyc.gov/html/dot/html/pr2023/berry-st-bike-boulevard.shtml'], ['Streetsblog, November 21, 2023', 'https://nyc.streetsblog.org/2023/11/21/eyes-on-the-street-berry-street-bike-boulevard-is-a-model-for-low-traffic-streets']],
     'what': 'Two-way bike markings, curb extensions with planters and granite blocks, coral paint at intersections, loading zones, and one-way reversals on several blocks so through traffic cannot run the length of the street (NYC DOT).'},
    {'id': '39ave', 'name': '39th Avenue', 'nbhd': 'Sunnyside, Queens', 'boro': '4', 'street': '39 AVE', 'from': 'BARNETT AVE', 'to': 'WOODSIDE AVE', 'from_label': 'Barnett Avenue', 'to_label': 'Woodside Avenue', 'built': 'Implementation began September 2021',
     'src': [['NYC DOT project sheet (PDF)', 'https://www.nyc.gov/html/dot/downloads/pdf/39th-ave-bike-blvd-whh.pdf'], ['Streetsblog, June 16, 2021', 'https://nyc.streetsblog.org/2021/06/16/dot-finally-presents-its-bike-boulevard-vision-for-39th-ave-in-sunnyside']],
     'what': 'An Open Street made permanent with traffic calming, a protected bike lane, new pedestrian crossings, ramps and pedestrian space (NYC DOT).'},
    {'id': 'underhill', 'name': 'Underhill Avenue', 'nbhd': 'Prospect Heights, Brooklyn', 'boro': '3', 'street': 'UNDERHILL AVE', 'from': 'ATLANTIC AVE', 'to': 'EASTERN PKWY', 'from_label': 'Atlantic Avenue', 'to_label': 'Eastern Parkway', 'built': 'Proposed 2022, finished 2024 after a pause',
     'src': [['Streetsblog, July 5, 2022', 'https://nyc.streetsblog.org/2022/07/05/city-proposes-bike-and-pedestrian-upgrades-to-two-prospect-heights-avenues'], ['Brooklyn Paper', 'https://www.brooklynpaper.com/dot-underhill-avenue-bike-boulevard/']],
     'what': 'Some two-way blocks made one-way for cars with bike lanes in both directions, pinch points and heavy medians on the blocks that stay two-way, and the northernmost block closed at Lowry Triangle (Streetsblog, Brooklyn Paper).'},
    {'id': '31ave', 'name': '31st Avenue', 'nbhd': 'Astoria, Queens', 'boro': '4', 'street': '31 AVE', 'from': 'VERNON BLVD', 'to': 'STEINWAY ST', 'from_label': 'Vernon Boulevard', 'to_label': 'Steinway Street', 'built': 'Design unveiled May 2024, installed 2024',
     'src': [['Streetsblog, May 31, 2024', 'https://nyc.streetsblog.org/2024/05/31/city-officials-unveil-bike-boulevard-design-for-31st-avenue-in-queens']],
     'what': 'Parking-protected two-way bike path on the north side from Vernon Boulevard to 31st Street and the south side from 35th Street to Steinway Street, a shared street with one-way car traffic between 31st and 35th Streets, painted islands and curb extensions, and directional changes to divert cars (Streetsblog).'},
]
def cscl(name, boro):
    u = url('inkn-q76z', {'$select': 'physicalid,full_street_name,the_geom,l_low_hn,l_high_hn', '$where': f"full_street_name='{name}' AND boroughcode='{boro}'", '$limit': 5000})
    return [shape(r['the_geom']) for r in get(u)], u
def pt(g): return g if g.geom_type == 'Point' else list(g.geoms)[0]
def wkt(g):
    parts = [q for q in getattr(g, 'geoms', [g]) if q.geom_type == 'Polygon']
    return 'MULTIPOLYGON(' + ','.join('((' + ','.join('%.6f %.6f' % c for c in q.exterior.coords) + '))' for q in parts) + ')'
# bike facilities from the DOT file (the uploaded CSV, same dataset as mzxg-pwib)
BIKE = []
with open(os.path.join(ROOT, 'data', 'bergendean', 'bike_routes_2026-09-27.csv')) as f:
    for r in csv.DictReader(f):
        if r['status'] != 'Current' or not r['the_geom']: continue
        BIKE.append((r, P(shwkt.loads(r['the_geom']))))
print('bike segments', len(BIKE))
out = {'built': END[:10], 'start': TS['start'], 'crash_months': CM, 's311_months': SM, 'bike_file': 'NYC DOT New York City Bike Routes, downloaded September 27, 2026 (https://data.cityofnewyork.us/Transportation/New-York-City-Bike-Routes/mzxg-pwib)', 'boulevards': []}
COR = {f['properties']['k']: shape(f['geometry']) for f in json.load(open(os.path.join(OUT, 'corridor.geojson')))['features']}
BLVDS = [{'id': 'bergen', 'name': 'Bergen Street', 'nbhd': 'Boerum Hill to Brownsville, Brooklyn', 'boro': '3', 'corridor': 'bergen', 'from_label': 'Court Street', 'to_label': 'East New York Avenue', 'built': 'Proposed; design proposal due later in 2026, first phase targeted for 2027', 'src': [["NYC Mayor's Office, May 6, 2026", 'https://www.nyc.gov/mayors-office/news/2026/05/mayor-mamdani-joins-bergen-bike-bus-to-announce-safety-improveme']], 'what': 'Not designed yet (this page).'},
         {'id': 'dean', 'name': 'Dean Street', 'nbhd': 'Boerum Hill to Brownsville, Brooklyn', 'boro': '3', 'corridor': 'dean', 'from_label': 'Court Street', 'to_label': 'East New York Avenue', 'built': 'Proposed; design proposal due later in 2026, first phase targeted for 2027', 'src': [["NYC Mayor's Office, May 6, 2026", 'https://www.nyc.gov/mayors-office/news/2026/05/mayor-mamdani-joins-bergen-bike-bus-to-announce-safety-improveme']], 'what': 'Not designed yet (this page).'}] + BLVDS
for B in BLVDS:
    if B.get('corridor'):
        cor = COR[B['corridor']]; cu = ua = ub = 'https://github.com/cb6brooklyn/bkcb6/blob/main/data/bergendean/corridor.geojson'
        if cor.geom_type != 'LineString': cor = linemerge(cor)
    else:
        segs, cu = cscl(B['street'], B['boro']); line = linemerge(unary_union(segs))
        a, ua = cscl(B['from'], B['boro']); b, ub = cscl(B['to'], B['boro'])
        if line.geom_type != 'LineString':  # a street with gaps: take the piece that comes closest to both cross streets
            line = min(line.geoms, key=lambda g: g.distance(unary_union(a)) + g.distance(unary_union(b)))
        ia = line.intersection(unary_union(a)); ib = line.intersection(unary_union(b))
        if ia.is_empty or ib.is_empty:
            from shapely.ops import nearest_points
            if ia.is_empty: ia = nearest_points(line, unary_union(a))[0]
            if ib.is_empty: ib = nearest_points(line, unary_union(b))[0]
        pa, pb = line.project(pt(ia)), line.project(pt(ib)); cor = substring(line, min(pa, pb), max(pa, pb))
    pc = P(cor); buf = pc.buffer(100); W = wkt(U(buf).simplify(0.00003, preserve_topology=True))
    ft = round(G.geometry_length(cor) * 3.28084)
    if cor.geom_type != 'LineString': cor = max(cor.geoms, key=lambda g: g.length) if False else cor
    # bike facilities along it: share of length by facility type (feature within 30 ft, both directions)
    fac = collections.Counter(); cls = collections.Counter()
    for r, g in BIKE:
        if r['boro'] != B['boro']: continue
        if g.distance(pc) > 30: continue
        ov = g.intersection(pc.buffer(30)).length
        if ov < 20 or ov < 0.5 * g.length: continue  # crossing lanes are not on the street
        types = sorted(set(t for t in (r['ft_facilit'], r['tf_facilit']) if t))
        fac[('Class %s: ' % r['facilitycl']) + ' / '.join(types)] += ov; cls[r['facilitycl']] += ov
    # crashes and 311 by month, 100 ft band
    um = url('h9gi-nx95', {'$select': 'date_trunc_ym(crash_date) as m,count(*) as n,sum(number_of_persons_injured) as inj,sum(number_of_cyclist_injured) as cyc,sum(number_of_pedestrians_injured) as ped,sum(number_of_persons_killed) as kil', '$where': f"crash_date>='{START}' AND crash_date<'{END}' AND within_polygon(location,'{W}')", '$group': 'm', '$order': 'm', '$limit': 400})
    cm = [[0, 0, 0, 0, 0] for _ in CM]; cmi = {m: i for i, m in enumerate(CM)}
    for r in get(um):
        if r['m'][:7] in cmi: cm[cmi[r['m'][:7]]] = [int(r['n']), int(float(r.get('inj') or 0)), int(float(r.get('cyc') or 0)), int(float(r.get('ped') or 0)), int(float(r.get('kil') or 0))]
    sm = [0] * len(SM); smi = {m: i for i, m in enumerate(SM)}; surls = []
    for ds, a1, b1 in S311:
        u = url(ds, {'$select': 'date_trunc_ym(created_date) as m,count(*) as n', '$where': f"created_date>='{a1}' AND created_date<'{b1}' AND within_polygon(location,'{W}')", '$group': 'm', '$order': 'm', '$limit': 400}); surls.append(u)
        for r in get(u):
            if r['m'][:7] in smi: sm[smi[r['m'][:7]]] += int(r['n'])
    # bike facility geometry along the corridor, for the mini map
    feats = []
    for r, g in BIKE:
        ov2 = g.intersection(pc.buffer(30)).length if g.distance(pc) <= 30 else 0
        if r['boro'] != B['boro'] or ov2 < 20 or ov2 < 0.5 * g.length: continue
        types = sorted(set(t for t in (r['ft_facilit'], r['tf_facilit']) if t))
        feats.append({'type': 'Feature', 'properties': {'s': r['street'], 'cl': r['facilitycl'], 'ty': ' / '.join(types), 'f': r['fromstreet'], 't': r['tostreet'], 'd': r['instdate']}, 'geometry': json.loads(json.dumps(mapping(U(g))), parse_float=lambda s: round(float(s), 6))})
    # speed limits along it (NYC DOT VZV) and bus routes touching it are left to the page's own layers; districts crossed:
    cds = set()
    for f in json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features']:
        if shape(f['geometry']).buffer(0).intersects(cor): cds.add(str(f['properties']['cd']))
    B2 = dict(B); B2.update({'ft': ft, 'mi': round(ft / 5280, 2), 'geometry': json.loads(json.dumps(mapping(cor.simplify(0.00001))), parse_float=lambda s: round(float(s), 6)), 'cscl_urls': [cu, ua, ub], 'wkt': W,
        'bike_ft': {k: round(v) for k, v in fac.most_common()}, 'bike_class_ft': {k: round(v) for k, v in cls.items()}, 'bike': {'type': 'FeatureCollection', 'features': feats},
        'crash_url': um, 'crash_m': cm, 's311_urls': surls, 's311_m': sm, 'cds': sorted(cds)})
    out['boulevards'].append(B2)
    print(B['name'], ft, 'ft', dict(fac.most_common(4)), 'crashes', sum(x[0] for x in cm), '311', sum(sm), cds)
json.dump(out, open(os.path.join(OUT, 'boulevards.json'), 'w'), separators=(',', ':'))
print('size', os.path.getsize(os.path.join(OUT, 'boulevards.json')))
