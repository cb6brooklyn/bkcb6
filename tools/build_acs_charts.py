#!/usr/bin/env python3
"""Distribution charts for /atlas/: every category count for every chart, for every community district, Census
neighborhood, bkcb6.app neighborhood, borough and the city, from the same tracts as tools/build_acs_atlas.py
(ACS 2020-2024 5-year, table-based summary files). Categories come from the Census Bureau's own line labels
(api.census.gov/data/2024/acs/acs5/variables.json), cut at a level of each table or grouped where a table has
dozens of brackets; every grouping is listed in CHARTS below. Writes data/atlas/charts.json.
python3 tools/build_acs_charts.py <scratch dir>  (the scratch dir of build_acs_atlas.py)"""
import csv, json, os, re, subprocess, sys
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = sys.argv[1]
BASE = 'https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-%s.dat'
COUNTY = {'005': '2', '047': '3', '061': '1', '081': '4', '085': '5'}
BORON = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
VARS = os.path.join(SCR, 'vars.json')
if not os.path.exists(VARS):
    subprocess.run(['curl', '-s', '-m', '600', '-o', VARS, 'https://api.census.gov/data/2024/acs/acs5/variables.json'], check=True)
V = json.load(open(VARS))['variables']


def labels(t):
    out = {}
    for k, x in V.items():
        if k.startswith(t + '_') and k.endswith('E') and not k.endswith('PE'):
            path = [p.rstrip(':') for p in x['label'].split('!!')[2:]]  # drop "Estimate", "Total:"
            if path:
                out['%03d' % int(k[len(t) + 1:-1])] = path
    return out


def money(s):
    m = re.findall(r'\$([\d,]+)', s)
    return [int(x.replace(',', '')) for x in m]


def age_first(s):
    m = re.search(r'(\d+)', s)
    return 0 if 'Under' in s else int(m.group(1))


def bucket(edges, names):
    def f(v):
        for e, n in zip(edges, names):
            if v < e:
                return n
        return names[-1]
    return f


# (id, section, title, universe, table, rule)
# rules: ('cut', depth, skip, keep) categories = nodes at that depth (leaves above it count as categories too), path
#        segments at the 'skip' positions dropped first (sex, tenure, age), 'keep' a prefix filter on the first segment
#        ('lines', [(name, [line, ...]), ...]) explicit sums of lines, for tables whose rows overlap
#        ('map', depth, skip, fn) categories = fn(category label at that depth), for grouping long bracket lists
CHARTS = [
 ('age', 'Basic demographics', 'Age distribution', 'Residents', 'B01001', ('map', 0, [0], lambda s: bucket([5, 18, 25, 35, 45, 55, 65, 75, 85, 999], ['Under 5', '5 to 17', '18 to 24', '25 to 34', '35 to 44', '45 to 54', '55 to 64', '65 to 74', '75 to 84', '85 and over'])(age_first(s)))),
 ('race', 'Basic demographics', 'Race and ethnicity', 'Residents', 'B03002', ('lines', [('White', ['003']), ('Black', ['004']), ('Asian', ['006']), ('Hispanic or Latino', ['012']), ('American Indian, Pacific Islander or other', ['005', '007', '008']), ('Two or more races', ['009'])])),
 ('edu', 'Basic demographics', 'Educational attainment', 'Residents 25 and over', 'B15003', ('lines', [('No high school diploma', ['%03d' % i for i in range(2, 17)]), ('High school diploma or GED', ['017', '018']), ('Some college, no degree', ['019', '020']), ('Associate’s degree', ['021']), ('Bachelor’s degree', ['022']), ('Master’s degree', ['023']), ('Professional degree', ['024']), ('Doctorate', ['025'])])),
 ('hhsize', 'Basic demographics', 'Household size', 'Households', 'B11016', ('cut', 0, [0], None)),
 ('marital', 'Basic demographics', 'Marital status', 'Residents 15 and over', 'B12001', ('cut', 0, [0], None)),
 ('lang', 'Basic demographics', 'Language spoken at home', 'Residents 5 and over', 'C16001', ('cut', 0, [], None)),
 ('english', 'Basic demographics', 'English proficiency', 'Residents 5 and over', 'C16001', ('leaflast', None)),
 ('hhtype', 'Basic demographics', 'Household composition', 'Households', 'B11001', ('cut', 1, [], None)),
 ('kids', 'Basic demographics', 'Children by household type', 'Children under 18 in households', 'B09005', ('cut', 0, [], None)),
 ('vets', 'Basic demographics', 'Veteran status', 'Residents 18 and over', 'B21001', ('lines', [('Veteran', ['002']), ('Not a veteran', ['003'])])),
 ('citizen', 'Immigration', 'Place of birth and citizenship', 'Residents', 'B05001', ('cut', 0, [], None)),
 ('region', 'Immigration', 'Foreign-born residents by region of birth', 'Foreign-born residents', 'B05006', ('cut', 0, [], None)),
 ('country', 'Immigration', 'Foreign-born residents by country of birth (top 15 citywide)', 'Foreign-born residents', 'B05006', ('leaves', 15)),
 ('entry', 'Immigration', 'Year of entry to the U.S.', 'Residents born outside the U.S.', 'B05005', ('cut', 0, [], None)),
 ('income', 'Income and poverty', 'Household income', 'Households', 'B19001', ('cut', 0, [], None)),
 ('poverty', 'Income and poverty', 'Income compared with the poverty line', 'Residents whose poverty status is known', 'C17002', ('cut', 0, [], None)),
 ('hours', 'Work', 'Full-time and part-time work', 'Residents 16 to 64', 'B23022', ('cut', 1, [0], None)),
 ('occ', 'Work', 'Occupation', 'Employed residents 16 and over', 'C24010', ('cut', 0, [0], None)),
 ('ind', 'Work', 'Industry of employment', 'Employed residents 16 and over', 'C24030', ('cut', 0, [0], None)),
 ('cls', 'Work', 'Class of worker', 'Employed residents 16 and over', 'B24080', ('cut', 0, [0], None)),
 ('earn', 'Work', 'Earnings of full-time, year-round workers', 'Full-time, year-round workers with earnings', 'B20005', ('earnings', None)),
 ('school', 'Students', 'School enrollment', 'Residents 3 and over', 'B14001', ('cut', 1, [], None)),
 ('tenure', 'Housing stock and stability', 'Owner and renter households', 'Households', 'B25003', ('cut', 0, [], None)),
 ('moved', 'Housing stock and stability', 'Year moved into current home', 'Households', 'B25038', ('cut', 0, [0], None)),
 ('vacancy', 'Housing stock and stability', 'Vacant homes by status', 'Vacant homes', 'B25004', ('cut', 0, [], None)),
 ('built', 'Housing stock and stability', 'Year built', 'Homes', 'B25034', ('cut', 0, [], None)),
 ('units', 'Housing stock and stability', 'Homes by size of building', 'Homes', 'B25024', ('cut', 0, [], None)),
 ('beds', 'Housing stock and stability', 'Homes by number of bedrooms', 'Homes', 'B25041', ('cut', 0, [], None)),
 ('rooms', 'Housing stock and stability', 'People per room', 'Households', 'B25014', ('cut', 0, [0], None)),
 ('heat', 'Housing stock and stability', 'Main home heating fuel', 'Households', 'B25040', ('cut', 0, [], None)),
 ('burden', 'Housing costs and affordability', 'Rent as a share of household income', 'Renter households', 'B25070', ('cut', 0, [], None)),
 ('oburden', 'Housing costs and affordability', 'Owner costs as a share of household income', 'Owner households', 'B25091', ('cut', 0, [0], None)),
 ('rent', 'Housing costs and affordability', 'Monthly gross rent', 'Renter households', 'B25063', ('rent', None)),
 ('value', 'Housing costs and affordability', 'Home values', 'Owner-occupied homes', 'B25075', ('value', None)),
 ('means', 'Transportation and commuting', 'How workers commute', 'Workers 16 and over', 'B08301', ('cut', 0, [], None)),
 ('time', 'Transportation and commuting', 'Commute time', 'Workers 16 and over who do not work from home', 'B08303', ('cut', 0, [], None)),
 ('cars', 'Transportation and commuting', 'Vehicles available', 'Households', 'B08201', ('lines', [('No vehicle', ['002']), ('1 vehicle', ['003']), ('2 vehicles', ['004']), ('3 or more', ['005', '006'])])),
 ('computer', 'Technology access', 'Computers in the household (a household can have several)', 'Households', 'B28001', ('lines', [('Desktop or laptop', ['003']), ('Smartphone', ['005']), ('Tablet', ['007']), ('Smartphone only', ['006']), ('No computer', ['011'])])),
 ('internet', 'Technology access', 'Internet in the household (a household can have several)', 'Households', 'B28002', ('lines', [('Broadband of any type', ['004']), ('Cable, fiber or DSL', ['007']), ('Cellular data plan', ['005']), ('Cellular data only', ['006']), ('Satellite', ['009']), ('Access without a subscription', ['012']), ('No internet access', ['013'])])),
 ('insure', 'Health', 'Health insurance coverage', 'Residents', 'B27010', ('insure', None)),
 ('disab', 'Health', 'Disability', 'Residents', 'B18101', ('disab', None)),
]


def cats_for(t, rule):
    """[(category name, [lines])] for a chart"""
    L = labels(t)
    kind = rule[0]
    if kind == 'lines':
        return [(n, ls) for n, ls in rule[1]]
    lines = sorted(L)
    paths = {l: L[l] for l in lines}
    leaf = {l: not any(m != l and len(paths[m]) > len(p) and paths[m][:len(p)] == p for m in lines) for l, p in paths.items()}
    out = {}
    order = []

    def put(name, l):
        if name not in out:
            out[name] = []; order.append(name)
        out[name].append(l)
    if kind in ('cut', 'map'):
        depth, skip = rule[1], rule[2]
        for l, p in paths.items():
            q = [s for i, s in enumerate(p) if i not in skip]
            if not q:
                continue
            if len(q) == depth + 1 or (len(q) < depth + 1 and leaf[l]):
                name = q[-1]
                if kind == 'map':
                    name = rule[3](name)
                put(name, l)
    elif kind == 'leaflast':
        for l, p in paths.items():
            if leaf[l]:
                put(p[-1], l)
    elif kind == 'leaves':
        for l, p in paths.items():
            if leaf[l] and not re.search(r'(?i)other|n\.e\.c', p[-1]) and len(p) >= 2:
                put(p[-1], l)
    elif kind == 'earnings':
        for l, p in paths.items():
            q = p[1:]
            if q and q[0].startswith('Worked full-time') and len(q) == 3 and q[1] == 'With earnings':
                v = money(q[2]) or [0]
                put(bucket([25000, 50000, 75000, 100000, 10 ** 9], ['Under $25,000', '$25,000 to $49,999', '$50,000 to $74,999', '$75,000 to $99,999', '$100,000 or more'])(v[0]), l)  # the table's top bracket is $100,000 or more
    elif kind == 'rent':
        for l, p in paths.items():
            if len(p) == 2 and p[0] == 'With cash rent':
                v = money(p[1])[0]
                put(bucket([1000, 1500, 2000, 2500, 3000, 3500, 10 ** 9], ['Under $1,000', '$1,000 to $1,499', '$1,500 to $1,999', '$2,000 to $2,499', '$2,500 to $2,999', '$3,000 to $3,499', '$3,500 or more'])(v), l)
            elif p == ['No cash rent']:
                put('No cash rent', l)
    elif kind == 'value':
        for l, p in paths.items():
            v = money(p[0])[0]
            put(bucket([300000, 500000, 750000, 1000000, 1500000, 2000000, 10 ** 10], ['Under $300,000', '$300,000 to $499,999', '$500,000 to $749,999', '$750,000 to $999,999', '$1 million to $1.49 million', '$1.5 million to $1.99 million', '$2 million or more'])(v), l)
    elif kind == 'insure':
        for l, p in paths.items():
            q = p[1:]
            if len(q) == 2 and q[0] == 'With one type of health insurance coverage':
                n = re.sub(r'^With | only$|health insurance coverage|coverage', '', q[1]).strip()
                n = {'employer-based': 'Employer-based only', 'direct-purchase': 'Bought directly only', 'Medicare': 'Medicare only',
                     'Medicaid/means-tested public': 'Medicaid or other means-tested only', 'TRICARE/military': 'TRICARE or military only',
                     'VA Health Care': 'VA health care only'}.get(n, n)
                put(n, l)
            elif len(q) == 1 and q[0] == 'With two or more types of health insurance coverage':
                put('Two or more types', l)
            elif len(q) == 1 and q[0] == 'No health insurance coverage':
                put('No health insurance', l)
    elif kind == 'disab':
        for l, p in paths.items():
            if p[-1] == 'With a disability':
                put('With a disability', l)
            elif p[-1] == 'No disability':
                put('No disability', l)
    res = [(n, out[n]) for n in order]
    if kind in ('map', 'earnings', 'rent', 'value'):
        pass
    return res


TABLES = sorted({c[4] for c in CHARTS})
cache_tab = {}


def table(t):
    path = os.path.join(SCR, t + '.psv')
    if not os.path.exists(path):
        cmd = "curl -s -m 1800 '%s' | awk 'NR==1 || /^1400000US36(005|047|061|081|085)/' > '%s'" % (BASE % t.lower(), path)
        subprocess.run(cmd, shell=True, check=True)
    rows = list(csv.reader(open(path), delimiter='|'))
    head = rows[0]
    out = {}
    for r in rows[1:]:
        g = r[0].split('US')[1]
        out[g] = {h.split('_')[1][1:]: (float(v) if v not in ('', None) and float(v) > -999999 else 0.0) for h, v in zip(head[1:], r[1:]) if h.split('_')[1].startswith('E')}
    assert len(out) == 2327, (t, len(out))
    return out


DEF = []
for cid, sec, title, uni, t, rule in CHARTS:
    cats = cats_for(t, rule)
    assert cats, cid
    DEF.append({'id': cid, 'sec': sec, 'title': title, 'universe': uni, 'table': t, 'cats': [c for c, _ in cats], '_lines': [ls for _, ls in cats]})
T = {t: table(t) for t in TABLES}

# the same placement as build_acs_atlas.py, read back from its outputs
tr = json.load(open(os.path.join(ROOT, 'data/atlas/tracts.json')))
tracts = sorted(T['B01001'])
assert set(tracts) == set(tr)


OVER = {'computer', 'internet', 'country'}
def vec(g):
    v = {d['id']: [sum(T[d['table']][g].get(l, 0.0) for l in ls) for ls in d['_lines']] for d in DEF}
    for d in DEF:
        if d['id'] in OVER:
            v['_u_' + d['id']] = [T[d['table']][g].get('001', 0.0)]
    return v


def addv(a, b, w=1.0):
    for k, xs in b.items():
        a.setdefault(k, [0.0] * len(xs))
        for i, x in enumerate(xs):
            a[k][i] += x * w


U = {}
for g in tracts:
    v = vec(g)
    cd, nta, b = tr[g]['cd'], tr[g]['nta'], COUNTY[g[2:5]]
    keys = ['nta:' + nta, 'boro:' + b, 'nyc'] + (['cb:' + cd] if int(cd[1:]) <= 18 else [])
    for k in keys:
        addv(U.setdefault(k, {}), v)

# bkcb6.app neighborhoods: the tract's counts split by land area, as in build_acs_atlas.py
feats = json.load(open(os.path.join(ROOT, 'data/atlas/tracts.geojson')))['features']
shapes = {f['properties']['g']: shape(f['geometry']).buffer(0) for f in feats}
nbs = [(f['properties']['boro'] + '|' + f['properties']['nb'], shape(f['geometry']).buffer(0)) for f in json.load(open(os.path.join(ROOT, 'data/city-neighborhoods.geojson')))['features']]
nbt = STRtree([g for _, g in nbs])
for g, geom in shapes.items():
    if geom.area <= 0:
        continue
    v = vec(g)
    for i in nbt.query(geom):
        k, ng = nbs[i]
        a = geom.intersection(ng).area / geom.area
        if a >= 0.01:
            addv(U.setdefault('nb:' + k, {}), v, a)

# check: the categories of every chart that splits a whole universe add up to the city's universe line
for d in DEF:
    tot = sum(T[d['table']][g].get('001', 0.0) for g in tracts)
    s = sum(U['nyc'][d['id']])
    d['_check'] = (round(s), round(tot))
for d in DEF:
    print('%-9s %-60s %3d cats  city sum %s / universe %s' % (d['id'], d['title'][:60], len(d['cats']), d['_check'][0], d['_check'][1]))

# the country chart: keep the 15 largest countries citywide, plus "All other countries"
for d in DEF:
    if d['id'] == 'country':
        order = sorted(range(len(d['cats'])), key=lambda i: -U['nyc']['country'][i])
        keep = order[:15]
        for k, u in U.items():
            xs = u['country']; tot = sum(T['B05006'][g]['001'] for g in tracts) if k == 'nyc' else None
            u['country'] = [xs[i] for i in keep] + [u['_u_country'][0] - sum(xs[i] for i in keep)]
        d['cats'] = [d['cats'][i] for i in keep] + ['All other countries']

out = {'source': 'U.S. Census Bureau, American Community Survey 2020-2024 5-year estimates, table-based summary files; categories from the Census Bureau’s line labels',
       'charts': [dict({k: v for k, v in d.items() if not k.startswith('_')}, **({'share_of': 'universe'} if d['id'] in ('computer', 'internet') else {})) for d in DEF],
       'units': {k: {cid: [round(x) for x in xs] for cid, xs in u.items() if cid != '_u_country'} for k, u in U.items()}}
json.dump(out, open(os.path.join(ROOT, 'data/atlas/charts.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
print(len(DEF), 'charts;', len(U), 'places;', os.path.getsize(os.path.join(ROOT, 'data/atlas/charts.json')) // 1024, 'KB')
