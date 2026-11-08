#!/usr/bin/env python3
"""The numbers behind each elected official's dashboard (assets/district-dash.js), one file per district:
data/dashboards/<council|assembly|senate|congress>-<n>.json. Nothing is estimated, smoothed or apportioned.

Population: the 2020 Census counts each body that drew the lines published for its districts
(data/redistricting/population.json, from scripts/district_population.py).

311: NYC Open Data 311 Service Requests (erm2-nwe9), counted by year and by the categories used across bkcb6.app
(build-cats.py). City Council: the council district the City records on each request. State Assembly and State
Senate: the existing counts of requests whose mapped location falls inside the district (data/assembly-311-*.json,
data/senate-311-*.json). Congress: the same, queried here (within_polygon on data/congress-311-polygons.json).

Community districts: the community boards the district shares election districts with (app/data/civic/officials.json),
each linked to its own board page, where the figures published only by community district live.
Usage: python3 scripts/district_dashboards.py [--skip-311-fetch]"""
import importlib.util, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TOKEN = 'HvFoIfzodzpRML7a1104Ca2tM'
OUT = 'data/dashboards'
YEARS = [str(y) for y in range(2020, time.gmtime().tm_year + 1)]

spec = importlib.util.spec_from_file_location('bc', os.path.join(ROOT, 'build-cats.py'))
_bc = importlib.util.module_from_spec(spec); _argv = sys.argv; sys.argv = ['x']; spec.loader.exec_module(_bc); sys.argv = _argv
categorize = _bc.categorize

def socrata(params, tries=10):
    params = dict(params, **{'$$app_token': TOKEN})
    url = 'https://data.cityofnewyork.us/resource/erm2-nwe9.json?' + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(url, timeout=900))
        except Exception as e:
            print('  retry', i + 1, str(e)[:80], flush=True); time.sleep(30 * (i + 1))
    raise RuntimeError('311 query failed')

def bucket(rows):
    out = {}
    for x in rows:
        c = categorize(x['ct']); out[c] = out.get(c, 0) + int(x['n'])
    top = max(rows, key=lambda x: int(x['n'])) if rows else None
    if top: out['_t'] = top['ct']; out['_tn'] = int(top['n'])
    return out

def fetch_311():
    c = {}
    for y in YEARS:
        print('council', y, flush=True)
        rows = socrata({'$select': 'council_district as d,complaint_type as ct,count(1) as n',
                        '$where': f"created_date>='{y}-01-01T00:00:00' AND created_date<'{int(y)+1}-01-01T00:00:00'",
                        '$group': 'd,ct', '$limit': '50000'})
        by = {}
        for x in rows:
            if x.get('d') and str(x['d']).strip().isdigit(): by.setdefault(str(int(x['d'])), []).append(x)
        for n, rs in by.items():
            k = f'council-{n}'
            c.setdefault(k, {}).setdefault('cats', {})[y] = bucket(rs)
            c[k].setdefault('years', {})[y] = sum(int(x['n']) for x in rs)
        time.sleep(10)
    for n, v in json.load(open('data/congress-311-polygons.json')).items():
        print('congress', n, flush=True)
        rows = socrata({'$select': 'date_extract_y(created_date) as y,complaint_type as ct,count(1) as n',
                        '$where': f"created_date>='{YEARS[0]}-01-01T00:00:00' AND within_polygon(location,'{v['wkt']}')",
                        '$group': 'y,ct', '$limit': '50000'})
        k = f'congress-{n}'
        for y in YEARS:
            rs = [x for x in rows if str(x.get('y')) == y]
            if rs:
                c.setdefault(k, {}).setdefault('cats', {})[y] = bucket(rs)
                c[k].setdefault('years', {})[y] = sum(int(x['n']) for x in rs)
        time.sleep(30)
    c['_built'] = time.strftime('%Y-%m-%d')
    json.dump(c, open(os.path.join(OUT, '_311.json'), 'w'))
    return c

def main():
    os.makedirs(OUT, exist_ok=True)
    pop = json.load(open('data/redistricting/population.json'))
    c311 = json.load(open(os.path.join(OUT, '_311.json'))) if '--skip-311-fetch' in sys.argv else fetch_311()
    for ch in ('assembly', 'senate'):
        rank = json.load(open(f'data/{ch}-311-rank.json')); cats = json.load(open(f'data/{ch}-311-cats.json'))
        for y in YEARS:
            for n, v in rank['years'].get(y, {}).items(): c311.setdefault(f'{ch}-{n}', {}).setdefault('years', {})[y] = v
            for n, v in cats['years'].get(y, {}).items(): c311.setdefault(f'{ch}-{n}', {}).setdefault('cats', {})[y] = v
        c311[f'_{ch}_built'] = rank.get('built')
    cbname = {b['borocd']: (b['name'], b['slug']) for b in json.load(open('app/data/civic/boards.json'))}
    city = json.load(open('data/311-city-cats.json'))['years']
    n = 0
    for o in json.load(open('app/data/civic/officials.json')):
        ch = o['type']
        if ch not in ('council', 'assembly', 'senate', 'congress'): continue
        k = f"{ch}-{o['district']}"
        d = {'district': k, 'population': pop[ch].get(str(o['district'])), 'population_source': pop['sources'][ch],
             '311': {kk: vv for kk, vv in c311.get(k, {}).items()},
             '311_source': {'council': 'NYC Open Data 311 Service Requests, by the council district the City records on each request',
                            'congress': 'NYC Open Data 311 Service Requests, by each request’s mapped location inside the district',
                            'assembly': 'NYC Open Data 311 Service Requests, by each request’s mapped location inside the district',
                            'senate': 'NYC Open Data 311 Service Requests, by each request’s mapped location inside the district'}[ch],
             '311_built': c311.get('_built') if ch in ('council', 'congress') else c311.get(f'_{ch}_built'),
             'city311': {y: {kk: vv for kk, vv in city[y]['NYC'].items() if not kk.startswith('_')} for y in YEARS if y in city},
             'boards': [{'cd': c['cd'], 'name': cbname.get(c['cd'], (c['label'], ''))[0], 'url': '/' + cbname[c['cd']][1] + '.html' if c['cd'] in cbname else '',
                         'eds': c['eds']} for c in sorted(o.get('cbs', []), key=lambda c: -c['eds']) if c.get('eds', 0) > 0],
             'eds': sum(c.get('eds', 0) for c in o.get('cbs', []))}
        json.dump(d, open(os.path.join(OUT, k + '.json'), 'w'), separators=(',', ':')); n += 1
    print(n, 'dashboards')

if __name__ == '__main__':
    main()
