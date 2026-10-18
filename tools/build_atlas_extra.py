#!/usr/bin/env python3
"""The Census Atlas charts that do not come from the American Community Survey, for every community district, Census
neighborhood, bkcb6.app neighborhood, borough and the city. Writes data/atlas/extra.json in the same shape as
data/atlas/charts.json (charts, then units), with each chart's "mode":
  rate  values are percentages already (CDC PLACES, Opportunity Atlas), averaged over tracts weighted by population
  share categories are counts; the page shows each as a share of the chart's total
Sources, each tract placed in a district and neighborhood as in tools/build_acs_atlas.py (data/atlas/tracts.json):
  - CDC PLACES 2025 release (data.cdc.gov cwsq-ngmh), census tracts, model-based crude prevalence among adults,
    weighted by each tract's adult population
  - LEHD Origin-Destination Employment Statistics (LODES 8), 2023, New York: jobs located in each place (workplace area
    characteristics) and where the people who live in each place work (origin-destination, jobs in New York State)
  - Opportunity Insights, The Opportunity Atlas (tract_outcomes_simple.csv), 2010 census tracts placed by the Census
    Bureau's 2010 tract center point (2019 Gazetteer), weighted by the number of children in each tract's estimate
python3 tools/build_atlas_extra.py <scratch dir>"""
import csv, gzip, json, os, sys
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = sys.argv[1]
COUNTY = {'005': '2', '047': '3', '061': '1', '081': '4', '085': '5'}
tr = json.load(open(os.path.join(ROOT, 'data/atlas/tracts.json')))


def keys_for(g):
    cd, nta, b = tr[g]['cd'], tr[g]['nta'], COUNTY[g[2:5]]
    return ['nta:' + nta, 'boro:' + b, 'nyc'] + (['cb:' + cd] if int(cd[1:]) <= 18 else [])


# bkcb6.app neighborhoods: each tract's share of land in each neighborhood (as in build_acs_atlas.py)
feats = json.load(open(os.path.join(ROOT, 'data/atlas/tracts.geojson')))['features']
shapes = {f['properties']['g']: shape(f['geometry']).buffer(0) for f in feats}
nbs = [('nb:' + f['properties']['boro'] + '|' + f['properties']['nb'], shape(f['geometry']).buffer(0))
       for f in json.load(open(os.path.join(ROOT, 'data/city-neighborhoods.geojson')))['features']]
nbt = STRtree([g for _, g in nbs])
NBW = {}
for g, geom in shapes.items():
    if geom.area <= 0:
        continue
    for i in nbt.query(geom):
        k, ng = nbs[i]
        a = geom.intersection(ng).area / geom.area
        if a >= 0.01:
            NBW.setdefault(g, []).append((k, a))


def weights(g):
    """(place key, weight) for every place a 2020 tract counts toward"""
    return [(k, 1.0) for k in keys_for(g)] + NBW.get(g, [])


CHARTS, UNITS = [], {}


def chart(cid, sec, title, universe, cats, mode, note=''):
    CHARTS.append({'id': cid, 'sec': sec, 'title': title, 'universe': universe, 'cats': cats, 'mode': mode, 'note': note})


def add(cid, key, vals, w=1.0):
    u = UNITS.setdefault(key, {})
    a = u.setdefault(cid, [0.0] * len(vals))
    for i, v in enumerate(vals):
        a[i] += v * w


# ---- CDC PLACES ----
rows = json.load(open(os.path.join(SCR, 'places.json')))
by = {}
for r in rows:
    if r['locationid'] in tr and r.get('data_value') not in (None, ''):
        by.setdefault(r['locationid'], {})[r['measureid']] = (float(r['data_value']), float(r.get('totalpop18plus') or 0), r['measure'], r['category'])
meas = {}
for g, m in by.items():
    for mid, (v, w, name, cat) in m.items():
        meas.setdefault(cat, {})[mid] = name
GROUPS = [('Health-Related Social Needs', 'Material hardship and social needs'), ('Health Outcomes', 'Health problems'),
          ('Health Risk Behaviors', 'Health risk behaviors'), ('Health Status', 'Overall health status'),
          ('Prevention', 'Preventive care'), ('Disability', 'Disability by type')]
for cat, title in GROUPS:
    mids = sorted(meas[cat], key=lambda x: meas[cat][x])
    cid = 'places_' + ''.join(ch for ch in cat.lower() if ch.isalpha())
    names = [meas[cat][m][0].upper() + meas[cat][m][1:] for m in mids]
    chart(cid, 'Material hardship' if cat.startswith('Health-Related') else 'Health', title, 'Adults (CDC model-based estimates)', names, 'rate',
          'CDC PLACES 2025 release, model-based estimates from the 2023 Behavioral Risk Factor Surveillance System, by census tract, weighted by adults.')
    for g, m in by.items():
        for k, wt in weights(g):
            num = [m[x][0] * m[x][1] if x in m else 0.0 for x in mids]
            den = [m[x][1] if x in m else 0.0 for x in mids]
            add(cid, k, num, wt); add('_d_' + cid, k, den, wt)
n_places = len(by)

# ---- LODES: jobs located here ----
WAC = {}
with gzip.open(os.path.join(SCR, 'ny_wac_S000_JT00_2023.csv.gz'), 'rt') as f:
    for r in csv.DictReader(f):
        g = r['w_geocode'][:11]
        if g in tr:
            a = WAC.setdefault(g, {})
            for k, v in r.items():
                if k not in ('w_geocode', 'createdate'):
                    a[k] = a.get(k, 0) + int(v)
WAC2 = {}  # firm age and size are published only for private-sector jobs (JT02)
with gzip.open(os.path.join(SCR, 'ny_wac_S000_JT02_2023.csv.gz'), 'rt') as f:
    for r in csv.DictReader(f):
        g = r['w_geocode'][:11]
        if g in tr:
            a = WAC2.setdefault(g, {})
            for k, v in r.items():
                if k.startswith('CF'):
                    a[k] = a.get(k, 0) + int(v)
SECT = ['Agriculture, forestry, fishing and hunting', 'Mining, quarrying, and oil and gas extraction', 'Utilities', 'Construction', 'Manufacturing',
        'Wholesale trade', 'Retail trade', 'Transportation and warehousing', 'Information', 'Finance and insurance', 'Real estate and rental and leasing',
        'Professional, scientific, and technical services', 'Management of companies and enterprises', 'Administrative and support and waste management',
        'Educational services', 'Health care and social assistance', 'Arts, entertainment, and recreation', 'Accommodation and food services',
        'Other services (except public administration)', 'Public administration']
J = [('jobs_ind', 'Industry of jobs located here', ['CNS%02d' % i for i in range(1, 21)], SECT),
     ('jobs_earn', 'Monthly earnings of jobs located here', ['CE01', 'CE02', 'CE03'], ['$1,250 a month or less', '$1,251 to $3,333 a month', 'More than $3,333 a month']),
     ('jobs_age', 'Age of workers in jobs located here', ['CA01', 'CA02', 'CA03'], ['29 or younger', '30 to 54', '55 or older']),
     ('jobs_firmage', 'Private-sector jobs by age of the firm', ['CFA01', 'CFA02', 'CFA03', 'CFA04', 'CFA05'], ['0 to 1 year', '2 to 3 years', '4 to 5 years', '6 to 10 years', '11 years or more']),
     ('jobs_firmsize', 'Private-sector jobs by size of the firm', ['CFS01', 'CFS02', 'CFS03', 'CFS04', 'CFS05'], ['0 to 19 employees', '20 to 49', '50 to 249', '250 to 499', '500 or more'])]
for cid, title, cols, names in J:
    chart(cid, 'Local businesses', title, 'Jobs located in the place, 2023', names, 'share',
          'U.S. Census Bureau LEHD Origin-Destination Employment Statistics (LODES 8), 2023, all jobs; firm age and size cover private-sector jobs only.' if 'firm' in cid else 'U.S. Census Bureau LEHD Origin-Destination Employment Statistics (LODES 8), 2023, all jobs.')
    for g, a in (WAC2 if 'firm' in cid else WAC).items():
        for k, wt in weights(g):
            add(cid, k, [a.get(c, 0) for c in cols], wt)
for g, a in WAC.items():
    for k, wt in weights(g):
        add('_jobs', k, [a['C000']], wt)

# ---- LODES: where residents work, where workers live ----
BN = {'1': 'Manhattan', '2': 'the Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
WORK = ['In their own community district', 'Elsewhere in Manhattan', 'Elsewhere in the Bronx', 'Elsewhere in Brooklyn', 'Elsewhere in Queens', 'Elsewhere in Staten Island', 'Elsewhere in New York State']
chart('work_where', 'Transportation and commuting', 'Where residents work', 'Residents with a job in New York State, 2023', WORK, 'share',
      'LODES 8 origin-destination, 2023: jobs held by residents, by where the job is. Jobs in other states are not in the New York file.')
chart('work_from', 'Local businesses', 'Where people who work here live', 'Jobs located in the place held by New York State residents, 2023', ['Lives in their own community district'] + [w.replace('Elsewhere', 'Lives elsewhere') for w in WORK[1:]], 'share',
      'LODES 8 origin-destination, 2023: jobs located in the place, by where the worker lives. Workers from other states are not in the New York main file.')


def cdof(g):
    return tr[g]['cd'] if g in tr else None


with gzip.open(os.path.join(SCR, 'ny_od_main_JT00_2023.csv.gz'), 'rt') as f:
    rd = csv.reader(f); next(rd)
    for w, h, s, *_ in rd:
        wg, hg, n = w[:11], h[:11], int(s)
        hin, win = hg in tr, wg in tr
        if not (hin or win):
            continue
        if hin:
            hcd = tr[hg]['cd']
            if win:
                wcd = tr[wg]['cd']
                cat = 0 if wcd == hcd else int(COUNTY[wg[2:5]])
            else:
                cat = 6
            v = [0] * 7; v[cat] = n
            for k, wt in weights(hg):
                add('work_where', k, v, wt)
        if win:
            wcd = tr[wg]['cd']
            if hin:
                cat = 0 if tr[hg]['cd'] == wcd else int(COUNTY[hg[2:5]])
            else:
                cat = 6
            v = [0] * 7; v[cat] = n
            for k, wt in weights(wg):
                add('work_from', k, v, wt)

# ---- Opportunity Atlas (2010 tracts, placed by their 2010 center point) ----
gz = {}
for r in csv.DictReader(open(os.path.join(SCR, '2019_gaz_tracts_36.txt')), delimiter='\t'):
    r = {k.strip(): v.strip() for k, v in r.items()}
    if r['GEOID'][2:5] in COUNTY:
        gz[r['GEOID']] = (float(r['INTPTLONG']), float(r['INTPTLAT']))
cds = [(f['properties']['boro_cd'], shape(f['geometry']).buffer(0)) for f in json.load(open(os.path.join(ROOT, 'data/community-districts.geojson')))['features']]
ntas = [(f['properties']['id'], shape(f['geometry']).buffer(0)) for f in json.load(open(os.path.join(ROOT, 'data/nta-boundaries.geojson')))['features']]
cdt, ntt = STRtree([g for _, g in cds]), STRtree([g for _, g in ntas])


def find(tree, items, pt, nearest=True):
    for i in tree.query(pt):
        if items[i][1].contains(pt):
            return items[i][0]
    return items[tree.nearest(pt)][0] if nearest else None


OI = [('kfr_pooled_pooled_p25', 'pooled_pooled_count', 'All children'), ('kfr_black_pooled_p25', 'black_pooled_count', 'Black children'),
      ('kfr_hisp_pooled_p25', 'hisp_pooled_count', 'Hispanic children'), ('kfr_white_pooled_p25', 'white_pooled_count', 'White children')]
JAIL = [('jail_pooled_pooled_p25', 'pooled_pooled_count', 'All children'), ('jail_black_pooled_p25', 'black_pooled_count', 'Black children'),
        ('jail_hisp_pooled_p25', 'hisp_pooled_count', 'Hispanic children'), ('jail_white_pooled_p25', 'white_pooled_count', 'White children')]
chart('mob_rank', 'Economic mobility', 'Where children from lower-income families end up: household income rank at age 35', 'Children who grew up here with parents at the 25th percentile of income (born 1978 to 1983)',
      [x[2] for x in OI], 'rate', 'Opportunity Insights, The Opportunity Atlas: mean national household income percentile (0 to 100) at about age 35, for children whose parents were at the 25th percentile. Higher is better.')
chart('mob_jail', 'Economic mobility', 'Incarcerated on April 1, 2010', 'The same children, at age 27 to 32', [x[2] for x in JAIL], 'rate',
      'Opportunity Insights, The Opportunity Atlas: share incarcerated on April 1, 2010, for children whose parents were at the 25th percentile.')
n_oi = 0
nb_items = [(k, g) for k, g in nbs]
for r in csv.DictReader(open(os.path.join(SCR, 'tract_outcomes_simple.csv'))):
    if r['state'] != '36' or ('%03d' % int(r['county'])) not in COUNTY:
        continue
    g = '36%03d%06d' % (int(r['county']), int(r['tract']))
    if g not in gz:
        continue
    pt = Point(*gz[g])
    cd = find(cdt, cds, pt); nta = find(ntt, ntas, pt); b = COUNTY[g[2:5]]
    ks = ['nta:' + nta, 'boro:' + b, 'nyc'] + (['cb:' + cd] if int(cd[1:]) <= 18 else [])
    nbk = [k for k, ng in nb_items if ng.contains(pt)]
    ks += nbk[:1]
    n_oi += 1
    for cid, spec, mult in (('mob_rank', OI, 100.0), ('mob_jail', JAIL, 100.0)):
        num, den = [], []
        for col, cnt, _ in spec:
            try:
                v, c = float(r[col]), float(r[cnt])
            except (ValueError, KeyError):
                v, c = None, 0.0
            if v is None or c <= 0:
                num.append(0.0); den.append(0.0)
            else:
                num.append(v * mult * c); den.append(c)
        for k in ks:
            add(cid, k, num); add('_d_' + cid, k, den)

# ---- finish: rates = weighted sum / weight ----
out_units = {}
for k, u in UNITS.items():
    o = {}
    for cid, xs in u.items():
        if cid.startswith('_d_'):
            continue
        if cid.startswith('_'):
            o[cid] = [round(x) for x in xs]; continue
        mode = [c for c in CHARTS if c['id'] == cid][0]['mode']
        if mode == 'rate':
            d = u.get('_d_' + cid, [0] * len(xs))
            o[cid] = [round(x / w, 1) if w > 0 else None for x, w in zip(xs, d)]
        else:
            o[cid] = [round(x) for x in xs]
    out_units[k] = o
json.dump({'source': 'CDC PLACES 2025; LEHD LODES 8 2023; Opportunity Insights Opportunity Atlas', 'charts': CHARTS, 'units': out_units},
          open(os.path.join(ROOT, 'data/atlas/extra.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
c6 = out_units['cb:306']
print('PLACES tracts', n_places, '| LODES workplace tracts', len(WAC), '| Opportunity Atlas tracts', n_oi, '| places', len(out_units))
print('CB6 jobs', c6['_jobs'], 'work_where', c6['work_where'], 'mob_rank', c6['mob_rank'], 'food insecurity etc', c6['places_healthrelatedsocialneeds'])
print('NYC jobs', out_units['nyc']['_jobs'])
