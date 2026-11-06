import json, re, collections as C, datetime as dt
from shapely.geometry import shape, Point, mapping
from shapely.ops import transform
import warnings; warnings.filterwarnings('ignore')
from shapely.strtree import STRtree
from shapely import make_valid
import pyproj

L = lambda n: json.load(open('raw/%s.json' % n))
OUT = 'out/'
import os; os.makedirs(OUT, exist_ok=True)
BOROS = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
BL = {'M': 'Manhattan', 'X': 'Bronx', 'B': 'Brooklyn', 'Q': 'Queens', 'R': 'Staten Island'}
AB = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
def code(cd):  # '306' -> 'BK06'
    cd = str(cd)
    return AB[cd[0]] + cd[1:].zfill(2)
proj = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:2263', always_xy=True).transform
SQFT_ACRE = 43560.0

# ---------- districts and population ----------
SD = json.load(open('/root/bkcb6/sanitation-policy/nyc/districts.geojson'))
DIST = {f['properties']['b']: f['properties'] for f in SD['features']}
POP = {k: v['pop'] for k, v in DIST.items()}
BOROPOP = json.load(open('/root/bkcb6/sanitation-policy/nyc/nyc.json'))['boroPop']
NYCPOP = sum(BOROPOP.values())
cds = json.load(open('raw/cds.geojson'))['features']
CDG = {}
for f in cds:
    bc = f['properties']['boro_cd']
    g = make_valid(shape(f['geometry']))
    CDG[bc] = g
CDP = {bc: transform(proj, g) for bc, g in CDG.items()}
cdkeys = list(CDG)
tree_cd = STRtree([CDG[k] for k in cdkeys])
def cd_of(lon, lat):
    p = Point(lon, lat)
    for i in tree_cd.query(p):
        if CDG[cdkeys[i]].contains(p):
            return cdkeys[i]
    return None
def is59(bc): return bc and int(bc[1:]) <= 18 and code(bc) in POP

# ---------- properties ----------
P = L('props')
props = {}
for p in P:
    cbs = re.findall(r'\d{3}', str(p.get('communityboard') or ''))
    try:
        g = make_valid(shape(p['multipolygon'])) if p.get('multipolygon') else None
    except Exception:
        g = None
    props[p['gispropnum']] = dict(id=p['gispropnum'], name=p.get('signname') or p.get('name311'), type=p.get('typecategory'),
        sub=p.get('subcategory'), acres=float(p.get('acres') or 0), addr=p.get('address'), loc=p.get('location'), boro=BL.get(p.get('borough')),
        cbs=cbs, g=g, jur=p.get('jurisdiction'), retired=p.get('retired'), waterfront=p.get('waterfront'), zip=p.get('zipcode'))
def prop(i):
    if not i: return None
    i = i.strip()
    return props.get(i) or props.get(i.split('-')[0]) or None
def pcent(pr):
    if pr and pr['g'] is not None and not pr['g'].is_empty:
        c = pr['g'].representative_point(); return (c.x, c.y)
    return None

# acres by CD (geometric intersection)
acres_cd = C.Counter(); parks_cd = C.defaultdict(set)
for pr in props.values():
    if pr['g'] is None or pr['g'].is_empty: continue
    gp = transform(proj, pr['g'])
    for i in tree_cd.query(pr['g']):
        k = cdkeys[i]
        a = gp.intersection(CDP[k]).area / SQFT_ACRE
        if a >= 0.02 and a >= 0.1 * gp.area / SQFT_ACRE:
            acres_cd[k] += a; parks_cd[k].add(pr['id'])
acres_boro = C.Counter(); n_boro = C.Counter()
for pr in props.values():
    acres_boro[pr['boro']] += pr['acres']; n_boro[pr['boro']] += 1

# ---------- point helpers: assign to CD by location, else by property ----------
def geo_pt(v):
    if not v: return None
    if isinstance(v, dict):
        try:
            g = shape(v); c = g.representative_point() if g.geom_type != 'Point' else g; return (c.x, c.y)
        except Exception: return None
    m = re.search(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)', str(v))
    if m: return (float(m.group(1)), float(m.group(2)))
    return None
def place(lonlat, pid=None):
    cd = cd_of(*lonlat) if lonlat else None
    if cd is None and pid:
        pr = prop(pid); c = pcent(pr)
        if c: cd = cd_of(*c)
    return cd

counts = C.defaultdict(C.Counter)   # metric -> cd -> n
boro_counts = C.defaultdict(C.Counter)
cb6pins = C.defaultdict(list)
def boro_of(cd, pid=None, fallback=None):
    if cd: return BOROS[cd[0]]
    pr = prop(pid) if pid else None
    return (pr and pr['boro']) or fallback

# fountains
for r in L('fountains'):
    ll = geo_pt(r.get('the_geom')); cd = place(ll, r.get('gispropnum'))
    counts['fountains'][cd] += 1; boro_counts['fountains'][boro_of(cd, r.get('gispropnum'), BL.get(r.get('borough')))] += 1
    if cd == '306': pr = prop(r.get('gispropnum')); cb6pins['fountains'].append([round(ll[1], 6), round(ll[0], 6), (pr or {}).get('name') or r.get('propertyna'), r.get('position') or ''])
# spray showers
for r in L('spray'):
    ll = geo_pt(r.get('point')); cd = place(ll, r.get('propid'))
    counts['spray'][cd] += 1; boro_counts['spray'][boro_of(cd, r.get('propid'), BL.get(r.get('boro')))] += 1
    if cd == '306': cb6pins['spray'].append([round(ll[1], 6), round(ll[0], 6), r.get('sitename') or r.get('propname'), ''])
# playgrounds (dedicated children's areas)
for r in L('dca'):
    ll = geo_pt(r.get('shape')); cd = place(ll, r.get('gispropnum'))
    counts['play'][cd] += 1; boro_counts['play'][boro_of(cd, r.get('gispropnum'), BL.get(r.get('borough')))] += 1
    if cd == '306': cb6pins['play'].append([round(ll[1], 6), round(ll[0], 6), r.get('publicname'), r.get('publiclocation') or ''])
# dog runs
for r in L('dogs'):
    if r.get('featurestatus') not in (None, 'Active'): continue
    ll = geo_pt(r.get('the_geom')); cd = place(ll, r.get('gispropnum'))
    counts['dogs'][cd] += 1; boro_counts['dogs'][boro_of(cd, r.get('gispropnum'), BL.get(r.get('borough')))] += 1
    if cd == '306': cb6pins['dogs'].append([round(ll[1], 6), round(ll[0], 6), r.get('name'), r.get('dog_area_type') or ''])
# pools
for r in L('pools'):
    ll = geo_pt(r.get('polygon')); cd = place(ll, r.get('gispropnum'))
    counts['pools'][cd] += 1; boro_counts['pools'][boro_of(cd, r.get('gispropnum'), BL.get(r.get('borough')))] += 1
    if cd == '306': cb6pins['pools'].append([round(ll[1], 6), round(ll[0], 6), r.get('name'), ' '.join(x for x in [r.get('location'), r.get('pooltype')] if x)])
# skateparks
for r in L('skate'):
    ll = geo_pt(r.get('the_geom')); cd = place(ll, r.get('gispropnum'))
    counts['skate'][cd] += 1; boro_counts['skate'][boro_of(cd, r.get('gispropnum'), BL.get(r.get('borough')))] += 1
    if cd == '306': cb6pins['skate'].append([round(ll[1], 6), round(ll[0], 6), r.get('name'), r.get('park_surfa') or ''])
# athletic facilities
SPORT = {'BKB': 'Basketball', 'HDB': 'Handball', 'TNS': 'Tennis', 'SOC': 'Soccer', 'SCR': 'Soccer', 'HKY': 'Hockey', 'MPPA': 'Multi-purpose', 'RBY': 'Rugby', 'FFB': 'Flag football', 'BSB': 'Baseball', 'SFB': 'Softball', 'FTB': 'Football', 'VLB': 'Volleyball',
         'TRK': 'Running track', 'BOC': 'Bocce', 'CRK': 'Cricket', 'HOC': 'Hockey', 'LAC': 'Lacrosse', 'RUG': 'Rugby', 'FRB': 'Frisbee', 'KIK': 'Kickball', 'NTB': 'Netball',
         'PKB': 'Pickleball', 'MUL': 'Multi-purpose', 'MPP': 'Multi-purpose', 'TBL': 'T-ball'}
for r in L('athletic'):
    if r.get('featurestatus') != 'Active': continue
    ll = geo_pt(r.get('multipolygon')); cd = place(ll, r.get('gispropnum'))
    counts['athletic'][cd] += 1; boro_counts['athletic'][boro_of(cd, r.get('gispropnum'), BL.get(r.get('borough')))] += 1
    if cd == '306':
        sp = SPORT.get(r.get('primary_sport'))
        if not sp:
            fl = [k for k in ['basketball', 'handball', 'tennis', 'regulation_soccer', 'nonregulation_soccer', 'adult_softball', 'll_softball', 'adult_baseball', 'll_baseb_12andunder', 'volleyball', 'bocce', 'pickleball', 'track_and_field', 'kickball', 'frisbee'] if r.get(k) == 'True']
            sp = {'regulation_soccer': 'Soccer', 'nonregulation_soccer': 'Soccer', 'adult_softball': 'Softball', 'll_softball': 'Softball', 'adult_baseball': 'Baseball', 'll_baseb_12andunder': 'Baseball', 'track_and_field': 'Running track'}.get(fl[0], fl[0].title()) if fl else 'Multi-purpose'
        pr = prop(r.get('gispropnum'))
        extra = [x for x in ['Lighted' if r.get('field_lighted') == 'True' else '', r.get('surface_type') or '', 'Accessible' if r.get('accessible') == 'True' else ''] if x]
        cb6pins['athletic'].append([round(ll[1], 6), round(ll[0], 6), (pr or {}).get('name') or '', sp, ' · '.join(extra)])
# community gardens
for r in L('gardens'):
    if (r.get('status') or 'Active') != 'Active': continue
    ll = (float(r['lon']), float(r['lat'])) if r.get('lat') else geo_pt(r.get('multipolygon'))
    cd = place(ll) if ll else (r.get('communityboard') or None)
    counts['gardens'][cd] += 1; boro_counts['gardens'][BL.get(r.get('borough')) or boro_of(cd)] += 1
    if cd == '306': cb6pins['gardens'].append([round(ll[1], 6), round(ll[0], 6), r.get('gardenname'), r.get('address') or '', r.get('juris') or ''])
# monuments
for r in L('monuments'):
    if r.get('extant') == 'N' or r.get('featurestatus') not in (None, 'Active'): continue
    ll = geo_pt(r.get('shape'));
    if not ll: continue
    cd = place(ll, r.get('parknumber'))
    counts['monuments'][cd] += 1; boro_counts['monuments'][boro_of(cd, r.get('parknumber'), r.get('borough'))] += 1
    if cd == '306':
        pr = prop(r.get('parknumber'))
        cb6pins['monuments'].append([round(ll[1], 6), round(ll[0], 6), r.get('name'), (pr or {}).get('name') or r.get('location') or '', ', '.join(x for x in [r.get('descrip'), r.get('sculptor'), (r.get('dedicated') or '')[:4]] if x)])
# comfort stations: no coordinates, so each sits at its park
for r in L('restrooms'):
    pr = prop(r.get('prop_id')); c = pcent(pr); cd = cd_of(*c) if c else None
    counts['restrooms'][cd] += 1; boro_counts['restrooms'][boro_of(cd, r.get('prop_id'))] += 1
    if cd == '306': cb6pins['restrooms'].append([round(c[1], 6), round(c[0], 6), pr['name'], r.get('cs_id')])

# capital projects
cap_cd = C.defaultdict(list)
for r in L('cap'):
    if r.get('latitude'):
        ll = (float(r['longitude']), float(r['latitude']))
    else:
        pr = prop((r.get('parkid') or '').split(',')[0]); ll = pcent(pr)
    cd = place(ll) if ll else None
    ph = r.get('currentphase') or ''
    active = ph != 'completed'
    if active:
        counts['capital'][cd] += 1; boro_counts['capital'][r.get('borough') or boro_of(cd)] += 1
    if cd == '306' and ll:
        cap_cd['306'].append(dict(lat=round(ll[1], 6), lon=round(ll[0], 6), id=r.get('trackerid'), t=r.get('title'), s=r.get('summary'), ph=ph,
            dp=r.get('designpercentcomplete'), pp=r.get('procurementpercentcomplete'), cp=r.get('constructionpercentcomplete'),
            fund=r.get('totalfunding'), src=r.get('fundingsource'), liaison=r.get('projectliaison'), park=r.get('name'), pid=r.get('parkid'),
            upd=(r.get('lastupdated') or '')[:10],
            dates={k[:-len('completion')] if k.endswith('completion') else k: (r.get(k) or '')[:10] for k in r if re.search(r'(start|completion)$', k) and r.get(k)}))

# inspections (PIP) in the last 12 published months
PIP = [r for r in L('pip') if r.get('inspectiontype') == 'PIP']
win = (min(r['date'] for r in PIP)[:10], max(r['date'] for r in PIP)[:10])
pip_cd = C.defaultdict(lambda: [0, 0, 0]); pip_boro = C.defaultdict(lambda: [0, 0, 0]); pip_prop = C.defaultdict(list)
for r in PIP:
    o, c = r.get('overall_condition'), r.get('cleanliness')
    if o not in ('A', 'U'): continue
    pr = prop(r['prop_id'])
    pip_prop[(pr or {}).get('id') or r['prop_id']].append(r)
    cdl = set()
    if pr:
        for k in tree_cd.query(pr['g']) if pr['g'] is not None else []:
            if parks_cd and pr['id'] in parks_cd.get(cdkeys[k], ()): cdl.add(cdkeys[k])
    for k in cdl:
        pip_cd[k][0] += 1; pip_cd[k][1] += o == 'A'; pip_cd[k][2] += c == 'A'
    b = (pr or {}).get('boro') or BL.get(r['prop_id'][0])
    pip_boro[b][0] += 1; pip_boro[b][1] += o == 'A'; pip_boro[b][2] += c == 'A'
    pip_boro['NYC'][0] += 1; pip_boro['NYC'][1] += o == 'A'; pip_boro['NYC'][2] += c == 'A'

# trees
pl = L('planting')
tree_cd2 = C.Counter(); empty_cd = C.Counter(); tree_boro = C.Counter(); empty_boro = C.Counter()
for r in pl:
    if not r.get('communityboard') or r.get('pssite') != 'Street': continue
    bc = str(int(float(r['communityboard']))); n = int(r['n'])
    if r.get('psstatus') == 'Populated': tree_cd2[bc] += n; tree_boro[BOROS.get(bc[0])] += n
    elif r.get('psstatus') == 'Empty': empty_cd[bc] += n; empty_boro[BOROS.get(bc[0])] += n
# forestry service requests and 311 Parks complaints, last 12 months
fsr_cd = C.Counter(); fsr_boro = C.Counter()
for r in L('fsr'):
    if not r.get('communityboard'): continue
    bc = str(int(float(r['communityboard']))); n = int(r['n']); fsr_cd[bc] += n; fsr_boro[BOROS.get(bc[0])] += n
c311_cd = C.Counter(); c311_boro = C.Counter(); c311_type_cd = C.defaultdict(C.Counter)
BN = {'MANHATTAN': '1', 'BRONX': '2', 'BROOKLYN': '3', 'QUEENS': '4', 'STATEN ISLAND': '5'}
for r in L('c311'):
    m = re.match(r'(\d\d) (.+)', r.get('community_board') or '')
    n = int(r['n'])
    if m and m.group(2) in BN:
        bc = BN[m.group(2)] + m.group(1); c311_cd[bc] += n; c311_type_cd[bc][r['complaint_type']] += n
        c311_boro[BOROS[bc[0]]] += n
    else:
        b = (r.get('community_board') or '').split(' ', 1)[-1].title()
        if b in BOROPOP: c311_boro[b] += n

# ---------- per-district table ----------
def r1(x, d=1): return None if x is None else round(x, d)
D = {}
for b, pop in POP.items():
    bc = [k for k in CDG if is59(k) and code(k) == b]
    bc = bc[0] if bc else None
    pc = pip_cd.get(bc, [0, 0, 0])
    tr, em = tree_cd2.get(bc, 0), empty_cd.get(bc, 0)
    D[b] = dict(pop=pop, acres=r1(acres_cd.get(bc, 0)), acresPer1k=r1(1000 * acres_cd.get(bc, 0) / pop, 2), parks=len(parks_cd.get(bc, ())),
        pipN=pc[0], pipOverall=r1(100 * pc[1] / pc[0]) if pc[0] else None, pipClean=r1(100 * pc[2] / pc[0]) if pc[0] else None,
        trees=tr, treesPer1k=r1(1000 * tr / pop), planted=r1(100 * tr / (tr + em)) if tr + em else None, emptySpaces=em,
        fsr=fsr_cd.get(bc, 0), fsrPer1k=r1(1000 * fsr_cd.get(bc, 0) / pop, 2), c311=c311_cd.get(bc, 0), c311Per1k=r1(1000 * c311_cd.get(bc, 0) / pop, 2),
        **{k: counts[k].get(bc, 0) for k in ['fountains', 'spray', 'play', 'dogs', 'pools', 'skate', 'athletic', 'gardens', 'monuments', 'restrooms', 'capital']})
    D[b]['playPer10k'] = r1(10000 * D[b]['play'] / pop, 2)
BO = {}
for b, pop in list(BOROPOP.items()) + [('NYC', NYCPOP)]:
    ac = sum(acres_boro.values()) if b == 'NYC' else acres_boro[b]
    pc = pip_boro[b]
    tr = sum(tree_boro.values()) if b == 'NYC' else tree_boro[b]; em = sum(empty_boro.values()) if b == 'NYC' else empty_boro[b]
    g = (lambda k: sum(boro_counts[k][x] for x in BOROPOP)) if b == 'NYC' else (lambda k: boro_counts[k][b])
    fs = sum(fsr_boro[x] for x in BOROPOP) if b == 'NYC' else fsr_boro[b]
    c3 = sum(c311_boro[x] for x in BOROPOP) if b == 'NYC' else c311_boro[b]
    BO[b] = dict(pop=pop, acres=r1(ac), acresPer1k=r1(1000 * ac / pop, 2), parks=sum(n_boro.values()) if b == 'NYC' else n_boro[b],
        pipN=pc[0], pipOverall=r1(100 * pc[1] / pc[0]) if pc[0] else None, pipClean=r1(100 * pc[2] / pc[0]) if pc[0] else None,
        trees=tr, treesPer1k=r1(1000 * tr / pop), planted=r1(100 * tr / (tr + em)) if tr + em else None, emptySpaces=em,
        fsr=fs, fsrPer1k=r1(1000 * fs / pop, 2), c311=c3, c311Per1k=r1(1000 * c3 / pop, 2),
        **{k: g(k) for k in ['fountains', 'spray', 'play', 'dogs', 'pools', 'skate', 'athletic', 'gardens', 'monuments', 'restrooms', 'capital']})
    BO[b]['playPer10k'] = r1(10000 * BO[b]['play'] / pop, 2)

# ranks
def rank(key, hi, within=None):
    items = [(k, v[key]) for k, v in D.items() if v[key] is not None and (within is None or DIST[k]['boro'] == within)]
    items.sort(key=lambda x: -x[1] if hi else x[1])
    out = {}; r = 0; prev = object()
    for i, (k, v) in enumerate(items):
        if v != prev: r = i + 1; prev = v
        out[k] = [r, len(items)]
    return out
CATS = [
 ('acresPer1k', 'Park acres per 1,000 residents', 'acres per 1,000', True, 'Acres of Parks Department property inside each district, measured on the map, per 1,000 residents. Prospect Park, Central Park and the other big parks that the City counts as their own districts are left out of every district.'),
 ('acres', 'Park acres', 'acres', True, 'Acres of Parks Department property inside each district, measured on the map.'),
 ('parks', 'Parks, playgrounds and green spaces', 'properties', True, 'Parks Department properties in or touching each district: parks, playgrounds, triangles, malls, gardens and more.'),
 ('pipOverall', 'Park inspections rated acceptable overall', '%', True, 'Parks Inspection Program, every inspection in the last 12 months published.'),
 ('pipClean', 'Park inspections rated clean', '%', True, 'Parks Inspection Program, every inspection in the last 12 months published.'),
 ('play', "Children's play areas", 'play areas', True, "Playgrounds with dedicated children's areas, Parks Department."),
 ('playPer10k', "Children's play areas per 10,000 residents", 'per 10,000', True, "Playgrounds with dedicated children's areas, per 10,000 residents."),
 ('restrooms', 'Public restrooms in parks', 'restrooms', True, 'Comfort stations the Parks Inspection Program inspects.'),
 ('fountains', 'Drinking fountains', 'fountains', True, 'Active drinking fountains in parks.'),
 ('spray', 'Spray showers', 'spray showers', True, 'Spray showers in parks.'),
 ('athletic', 'Athletic fields and courts', 'fields and courts', True, 'Active athletic facilities: courts, fields and tracks.'),
 ('dogs', 'Dog runs and off-leash areas', 'dog areas', True, 'Active dog runs and off-leash areas.'),
 ('gardens', 'Community gardens', 'gardens', True, 'Active GreenThumb community gardens.'),
 ('trees', 'Street trees', 'trees', True, 'Living street trees, Parks Department forestry inventory.'),
 ('treesPer1k', 'Street trees per 1,000 residents', 'per 1,000', True, 'Living street trees per 1,000 residents.'),
 ('planted', 'Street tree spaces with a tree', '%', True, 'Share of street tree planting spaces that have a living tree, against those that are empty and plantable.'),
 ('capital', 'Park capital projects underway', 'projects', True, 'Parks capital projects proposed, in design, in procurement or in construction.'),
 ('c311Per1k', '311 complaints to the Parks Department per 1,000 residents', 'per 1,000', False, '311 Service Requests to the Parks Department in the last 12 months, mostly street trees.'),
 ('fsrPer1k', 'Tree service requests per 1,000 residents', 'per 1,000', False, 'Forestry service requests in the last 12 months: hazards, pruning, removals, sidewalk damage and new trees.'),
]
R = dict(cats=[], districts={k: dict(boro=DIST[k]['boro'], num=DIST[k]['num'], st=DIST[k]['st'][0] if DIST[k]['st'] else '') for k in D}, boros=list(BOROPOP),
    source='NYC Parks Department via NYC Open Data: Parks Properties enfh-gkve, Parks Inspection Program yg3y-7juh and 9byw-znpj, Playgrounds with Dedicated Children\'s Areas j55h-3upk, Drinking Fountains qnv7-p7a2, Spray Showers ckaz-6gaa, Athletic Facilities qnem-b8re, Dog Runs hxx3-bwgv, GreenThumb Garden Info p78i-pat6, Forestry Planting Spaces 82zj-84is, Forestry Service Requests mu46-p9is, Capital Project Tracker 4hcv-tc5r; 311 Service Requests erm2-nwe9; Community Districts 5crt-au7u; population, American Community Survey 2024')
for key, label, unit, hi, note in CATS:
    R['cats'].append(dict(id=key, label=label, unit=unit, first='highest first' if hi else 'lowest first', note=note, nyc=BO['NYC'][key],
        boros=[dict(b=b, v=BO[b][key]) for b in BOROPOP], districts=[dict(d=k, v=D[k][key]) for k in D]))
RK = {key: dict(bk=rank(key, hi, 'Brooklyn'), nyc=rank(key, hi)) for key, _, _, hi, _ in CATS}
json.dump(R, open(OUT + 'rankings.json', 'w'), separators=(',', ':'))
json.dump(dict(D=D, BO=BO, RK=RK, win=win), open(OUT + 'all.json', 'w'), separators=(',', ':'))
print('window', win)
for k in ['BK06']: print(k, D[k]); print({key: RK[key]['bk'][k] for key in RK if k in RK[key]['bk']})
print('BK', BO['Brooklyn']); print('NYC', BO['NYC'])
json.dump({k: v for k, v in cb6pins.items()}, open(OUT + 'pins306.json', 'w'))
json.dump(cap_cd['306'], open(OUT + 'cap306.json', 'w'))
import pickle
pickle.dump(dict(parks_cd={k: sorted(v) for k, v in parks_cd.items()}, pip_prop=dict(pip_prop), win=win), open(OUT + 'mid.pkl', 'wb'))
