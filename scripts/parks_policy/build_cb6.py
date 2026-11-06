import json, re, pickle, collections as C, warnings
warnings.filterwarnings('ignore')
from shapely.geometry import shape, Point, mapping
from shapely import make_valid
L = lambda n: json.load(open('raw/%s.json' % n))
m = pickle.load(open('out/mid.pkl', 'rb'))
A = json.load(open('out/all.json'))
pins = json.load(open('out/pins306.json'))
cap = json.load(open('out/cap306.json'))
CD = [f for f in json.load(open('raw/cds.geojson'))['features'] if f['properties']['boro_cd'] == '306'][0]
CB6 = make_valid(shape(CD['geometry']))
inCB6 = lambda lon, lat: CB6.contains(Point(lon, lat))
P = {p['gispropnum']: p for p in L('props')}
ids = m['parks_cd']['306']

def rnd(g):
    def r(c):
        if isinstance(c[0], (int, float)): return [round(c[0], 6), round(c[1], 6)]
        return [r(x) for x in c]
    d = mapping(g); return {'type': d['type'], 'coordinates': r(d['coordinates'])}

# inspections
feat = C.defaultdict(list)
for f in L('feat306'): feat[f['inspection_id']].append(f)
haz = C.defaultdict(list)
for h in L('haz306'): haz[h['feature']].append(h)
def insp_rows(pid):
    out = []
    for r in sorted(m['pip_prop'].get(pid, []), key=lambda r: r['date'], reverse=True):
        fs = feat.get(r['inspection_id'], [])
        bad = [f['feature_1'] for f in fs if f['rating'] in ('U', 'U/S')]
        notes = []
        for f in fs:
            for h in haz.get(f['feature_2'], []):
                t = ' '.join(x for x in [h.get('type') or '', h.get('problem') or ''] if x).strip()
                if h.get('location_comments'): t += ' (' + h['location_comments'].strip() + ')'
                notes.append([h.get('class') or '', f['feature_1'], t])
        out.append(dict(d=r['date'][:10], o=r['overall_condition'], c=r['cleanliness'], season=r.get('season'), v=r.get('visitorcount'), bad=bad, notes=notes))
    return out

# events in CB6 parks, next 14 days
EV = []
for e in L('events'):
    pk = [x.strip() for x in (e.get('parkids') or '').split(',') if x.strip()]
    ll = None
    if e.get('coordinates'):
        try:
            a, b = [float(x) for x in e['coordinates'].split(',')[:2]]; ll = (b, a)
        except Exception: pass
    if not (any(p in ids for p in pk) or (ll and inCB6(*ll))): continue
    EV.append(dict(t=e.get('title'), s=e.get('starttime'), e=e.get('endtime'), park=e.get('parknames'), pid=pk[0] if pk else None, loc=e.get('location'),
        cat=e.get('categories'), url=(e.get('link') or {}).get('url'), reg=(e.get('registration_url') or {}).get('url'), lat=ll[1] if ll else None, lon=ll[0] if ll else None,
        d=(e.get('description') or '')[:260]))
EV.sort(key=lambda e: e['s'] or '')

# volunteer groups for CB6 parks
GR = []
for g in L('groups'):
    pk = [x.strip() for x in (g.get('prop_ids') or '').split(',')]
    hit = [p for p in pk if p in ids]
    if not hit: continue
    GR.append(dict(n=g.get('name'), parks=[P[p].get('signname') for p in hit], url=(g.get('url') or {}).get('url'), web=(g.get('website') or {}).get('url'),
        areas=g.get('interest_areas'), size=g.get('group_size'), d=(g.get('description') or '')[:300]))

# capital projects by park
capby = C.defaultdict(list)
for c in cap:
    for p in (c.get('pid') or '').split(','):
        capby[p.strip()].append(c['id'])

# amenities by park: what sits inside each park's shape
shp = {i: make_valid(shape(P[i]['multipolygon'])) for i in ids}
def park_of(lat, lon):
    pt = Point(lon, lat)
    best = None
    for i, g in shp.items():
        if g.buffer(0.00015).contains(pt):
            if best is None or g.area < shp[best].area: best = i
    return best
KIND = ['play', 'restrooms', 'fountains', 'spray', 'athletic', 'dogs', 'pools', 'skate', 'monuments']
amen = C.defaultdict(C.Counter); sports = C.defaultdict(C.Counter)
for k in KIND:
    for p in pins.get(k, []):
        pk = park_of(p[0], p[1])
        if pk:
            amen[pk][k] += 1
            if k == 'athletic': sports[pk][p[3]] += 1
for k in pins:
    for p in pins[k]:
        p.append(park_of(p[0], p[1]) or '')

PARKS = []
for i in ids:
    p = P[i]; g = shp[i]
    rows = insp_rows(i)
    n = len(rows); oa = sum(r['o'] == 'A' for r in rows); ca = sum(r['c'] == 'A' for r in rows)
    inter = g.intersection(CB6)
    share = inter.area / g.area if g.area else 1
    c = g.representative_point()
    PARKS.append(dict(id=i, n=p.get('signname'), type=p.get('typecategory'), sub=p.get('subcategory'), acres=round(float(p.get('acres') or 0), 2),
        inCB6=round(share, 2), addr=p.get('address'), loc=p.get('location'), acq=(p.get('acquisitiondate') or '')[:4], waterfront=p.get('waterfront') == 'True',
        jur=p.get('jurisdiction'), cb=p.get('communityboard'), lat=round(c.y, 6), lon=round(c.x, 6),
        insp=dict(n=n, o=round(100 * oa / n, 1) if n else None, c=round(100 * ca / n, 1) if n else None, rows=rows),
        amen=dict(amen[i]), sports=dict(sports[i]), cap=capby.get(i, []), url='https://www.nycgovparks.org/parks/' + i,
        g=rnd(g.simplify(0.000015, preserve_topology=True))))
PARKS.sort(key=lambda x: -x['acres'])

# Prospect Park, next door
PP = [p for p in L('props') if p['gispropnum'] == 'B073'][0]
prospect = dict(id='B073', n=PP.get('signname'), acres=float(PP['acres']), g=rnd(make_valid(shape(PP['multipolygon'])).simplify(0.00003, preserve_topology=True)))

# 311 and tree requests in CB6
def pt(v):
    mm = re.search(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)', str(v or ''))
    return (float(mm.group(2)), float(mm.group(1))) if mm else None
c311 = []
for r in L('c311_306'):
    if not r.get('latitude'): continue
    c311.append([round(float(r['latitude']), 6), round(float(r['longitude']), 6), r['complaint_type'], r.get('descriptor') or '', r['created_date'][:10], r.get('status') or '',
        (r.get('incident_address') or '').title(), (r.get('park_facility_name') or '') if (r.get('park_facility_name') or '') != 'Unspecified' else ''])
fsr = []
for r in L('fsr306'):
    ll = pt(r.get('location'))
    if not ll: continue
    fsr.append([round(ll[0], 6), round(ll[1], 6), r.get('srcategory') or '', r.get('srtype') or '', r.get('srpriority') or '', r.get('srstatus') or '', (r.get('createddate') or '')[:10], r.get('parkname') or ''])

# street trees in CB6
ps = {x['globalid']: x for x in L('ps306')}
trees = []
for t in L('trees306'):
    ll = (t.get('location') or {}).get('coordinates')
    if not ll or not inCB6(ll[0], ll[1]): continue
    trees.append(t)
sp = C.Counter(); cond = C.Counter(); site = C.Counter(); dbh = []
for t in trees:
    s = ps.get(t.get('plantingspaceglobalid'), {}).get('pssite') or 'Unknown'
    site[s] += 1
    if s != 'Street': continue
    sp[(t.get('genusspecies') or 'Unknown').split(' - ')[-1].strip().capitalize()] += 1
    cond[t.get('tpcondition') or 'Unknown'] += 1
    try: dbh.append(float(t['dbh']))
    except Exception: pass
TREES = dict(n=sum(sp.values()), site=dict(site), species=sp.most_common(15), nspecies=len(sp), cond=dict(cond), dbh=round(sum(dbh) / len(dbh), 1) if dbh else None)

D = A['D']['BK06']; BO = A['BO']
out = dict(name='CB6', district='BK06', win=A['win'], D=D, BK=BO['Brooklyn'], NYC=BO['NYC'], RK={k: dict(bk=v['bk'].get('BK06'), nyc=v['nyc'].get('BK06')) for k, v in A['RK'].items()},
    parks=PARKS, prospect=prospect, pins=pins, cap=cap, events=EV, groups=GR, trees=TREES,
    c311=dict(byType=C.Counter(x[2] for x in c311).most_common(), pts=c311, n=len(L('c311_306'))), fsr=dict(byCat=C.Counter(x[2] for x in fsr).most_common(), pts=fsr, n=len(L('fsr306'))),
    sources=dict(props='enfh-gkve', pip='yg3y-7juh', feat='5mma-5n3h', haz='ibip-ftv5'))
json.dump(out, open('out/cb6.json', 'w'), separators=(',', ':'))
print(len(PARKS), len(EV), len(GR), len(cap), TREES['n'], TREES['site'], len(c311), len(fsr))
print([ (p['n'], p['insp']['n'], p['amen']) for p in PARKS[:8]])
print([g['n'] for g in GR])
