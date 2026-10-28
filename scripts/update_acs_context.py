#!/usr/bin/env python3
"""Build data/acs-context.json: context for the housing-cost section, by community district (PUMA),
borough (county) and New York City (place), every year of the ACS 1-year estimates from 2010.

Usage: python3 scripts/update_acs_context.py [download folder]

Tables (U.S. Census Bureau, American Community Survey 1-year estimates, from data.census.gov):
  B20002  median earnings in the past 12 months, people 16 and over with earnings        -> earn
  B25070  gross rent as a percentage of household income, renter households
            share paying 30% or more = (_007+_008+_009+_010) / (_001 - _011)                 -> burden30
            share paying 50% or more = _010 / (_001 - _011)                                  -> burden50
            (_011 is "not computed": no income or no cash rent, left out of the share)
  B25003  tenure: owner-occupied share = _002 / _001; owners _002; renters _003              -> owner, owners, renters
  B01003  total population                                                                   -> pop
Community districts are PUMAs labelled by district from 2012; districts sharing a PUMA share its figures
(see "shared"). There are no standard 2020 1-year estimates.
"""
import datetime, json, os, re, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BORO = {'Manhattan': 'MN', 'Bronx': 'BX', 'Brooklyn': 'BK', 'Queens': 'QN', 'Staten Island': 'SI'}
COUNTY = {'36061': 'Manhattan', '36005': 'Bronx', '36047': 'Brooklyn', '36081': 'Queens', '36085': 'Staten Island'}
GEOS = {'puma': '040XX00US36$7950000', 'county': '040XX00US36$0500000', 'place': '1600000US3651000'}
TABLES = ['B20002', 'B25070', 'B25003', 'B01003']


def die(m): sys.exit('update_acs_context: ' + m)


def get(folder, y, t, k):
    p = os.path.join(folder, '%s_%d_%s.json' % (t, y, k))
    if not os.path.exists(p):
        for i in range(4):
            r = subprocess.run(['curl', '-s', '--max-time', '90', '-A', 'Mozilla/5.0',
                                'https://data.census.gov/api/access/data/table?id=ACSDT1Y%d.%s&g=%s' % (y, t, GEOS[k])], capture_output=True)
            if r.stdout.strip(): break
            time.sleep(3 + 3 * i)
        open(p, 'wb').write(r.stdout)
    try: d = json.load(open(p))
    except Exception: return None
    rows = (d.get('response') or {}).get('data') or []
    return [dict(zip(rows[0], r)) for r in rows[1:]] if rows else None


def num(v):
    try:
        x = float(v); return x if x >= 0 else None
    except (TypeError, ValueError): return None


def cds_of(name):
    m = re.search(r'NYC-(Manhattan|Bronx|Brooklyn|Queens|Staten Island) Community Districts? ([\d &]+)--', name)
    return ['%sCB%d' % (BORO[m.group(1)], int(n)) for n in re.findall(r'\d+', m.group(2))] if m else []


def measures(r, t):
    g = lambda c: num(r.get('%s_%sE' % (t, c)))
    out = {}
    if t == 'B20002' and g('001') is not None: out['earn'] = round(g('001'))
    if t == 'B25070':
        base = (g('001') or 0) - (g('011') or 0)
        if base > 0:
            out['burden30'] = round(100 * sum(g(c) or 0 for c in ['007', '008', '009', '010']) / base, 1)
            out['burden50'] = round(100 * (g('010') or 0) / base, 1)
    if t == 'B25003' and g('001'):
        out['owner'] = round(100 * g('002') / g('001'), 1); out['owners'] = round(g('002')); out['renters'] = round(g('003'))
    if t == 'B01003' and g('001') is not None: out['pop'] = round(g('001'))
    return out


def main(folder):
    cd, boro, nyc, shared, years = {}, {}, {}, {}, []
    def put(store, key, y, m):
        for k, v in m.items(): store.setdefault(key, {}).setdefault(k, {})[str(y)] = v
    for y in range(2010, datetime.date.today().year + 1):
        got = False
        for t in TABLES:
            p = get(folder, y, t, 'puma')
            if p is None: continue
            got = True
            for r in p:
                ks = cds_of(r.get('NAME', ''))
                for k in ks:
                    put(cd, k, y, measures(r, t))
                    if len(ks) > 1: shared.setdefault(k, {})[str(y)] = [x for x in ks if x != k]
            for r in get(folder, y, t, 'county') or []:
                b = COUNTY.get(r['GEO_ID'][-5:])
                if b: put(boro, b, y, measures(r, t))
            for r in get(folder, y, t, 'place') or []:
                if r['GEO_ID'].endswith('3651000'): put(nyc, 'NYC', y, measures(r, t))
        if got: years.append(y)
    if len(cd) != 59: die('expected 59 districts, got %d' % len(cd))
    out = {'built': datetime.date.today().isoformat(), 'years': years, 'cd': cd, 'boro': boro, 'nyc': nyc.get('NYC', {}), 'shared': shared,
           'source': 'U.S. Census Bureau, American Community Survey 1-year estimates: B20002 (median earnings), B25070 (gross rent as a share of income), B25003 (tenure), B01003 (population)',
           'url': 'https://data.census.gov'}
    json.dump(out, open(os.path.join(ROOT, 'data', 'acs-context.json'), 'w'), separators=(',', ':'))
    c = cd['BKCB6']
    print('years', years, '| CB6 2024:', {k: v.get('2024') for k, v in c.items()}, '| NYC 2024:', {k: v.get('2024') for k, v in out['nyc'].items()})


if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    os.makedirs(d, exist_ok=True)
    main(d)
