#!/usr/bin/env python3
"""Build data/income-history.json: median household income history and 30-year mortgage rates,
for the rent / for-sale affordability views on /nycsales/.

Usage: python3 scripts/update_income.py [download folder]
  With no folder it downloads into a temp folder first.

Sources
  * U.S. Census Bureau, American Community Survey 1-year estimates, table B19013
    (median household income in the past 12 months, in that year's dollars), from
    data.census.gov: community districts (PUMAs), the five boroughs (counties) and
    New York City (place). 2010 onward. The Census Bureau did not release standard
    2020 1-year estimates, so 2020 is absent.
    PUMAs are labelled with their community district from 2012 on. 2010 and 2011 use
    the 2000 PUMA codes, which carry no community district name, so community
    district income starts in 2012.
    Some community districts share one PUMA (e.g. Manhattan 1 & 2); both get its figure.
  * U.S. Census Bureau, Small Area Income and Poverty Estimates (SAIPE), median household
    income by county, via FRED series MHINY<fips>A052NCEN: the five boroughs from 1989.
  * Freddie Mac Primary Mortgage Market Survey, 30-year fixed rate, via FRED MORTGAGE30US,
    weekly from 1971; averaged here by calendar month.
"""
import csv, io, json, os, re, statistics, subprocess, sys, tempfile, time, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
BORO = {'Manhattan': 'MN', 'Bronx': 'BX', 'Brooklyn': 'BK', 'Queens': 'QN', 'Staten Island': 'SI'}
COUNTY = {'36061': 'Manhattan', '36005': 'Bronx', '36047': 'Brooklyn', '36081': 'Queens', '36085': 'Staten Island'}
GEOS = {'puma': '040XX00US36$7950000', 'county': '040XX00US36$0500000', 'place': '1600000US3651000'}


def die(msg):
    sys.exit('update_income: ' + msg)


def curl(url):
    for i in range(4):
        r = subprocess.run(['curl', '-s', '--max-time', '90', '-A', 'Mozilla/5.0', url], capture_output=True)
        if r.stdout.strip(): return r.stdout.decode('utf-8')
        time.sleep(3 + 3 * i)
    die('no response from ' + url)


def download(folder):
    this_year = datetime.date.today().year
    for y in range(2010, this_year + 1):
        for k, g in GEOS.items():
            path = os.path.join(folder, 'acs_%d_%s.json' % (y, k))
            if not os.path.exists(path):
                open(path, 'w').write(curl('https://data.census.gov/api/access/data/table?id=ACSDT1Y%d.B19013&g=%s' % (y, g)))
    for fips in COUNTY:
        open(os.path.join(folder, 'saipe_%s.csv' % fips), 'w').write(
            curl('https://fred.stlouisfed.org/graph/fredgraph.csv?id=MHINY%sA052NCEN' % fips))
    open(os.path.join(folder, 'mortgage30.csv'), 'w').write(
        curl('https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US'))


def acs_rows(folder, y, k):
    path = os.path.join(folder, 'acs_%d_%s.json' % (y, k))
    if not os.path.exists(path): return None
    try: d = json.load(open(path))
    except Exception: return None
    rows = (d.get('response') or {}).get('data') or []
    if not rows: return None
    hdr = rows[0]
    return [dict(zip(hdr, r)) for r in rows[1:]]


def cds_of(name):
    m = re.search(r'NYC-(Manhattan|Bronx|Brooklyn|Queens|Staten Island) Community Districts? ([\d &]+)--', name)
    if not m: return []
    return ['%sCB%d' % (BORO[m.group(1)], int(n)) for n in re.findall(r'\d+', m.group(2))]


def val(v):
    try:
        x = float(v)
        return int(round(x)) if x > 0 else None
    except (TypeError, ValueError):
        return None


def main(folder):
    this_year = datetime.date.today().year
    cd, boro, nyc, shared, years = {}, {}, {}, {}, []
    for y in range(2010, this_year + 1):
        p = acs_rows(folder, y, 'puma')
        if p is None: continue
        years.append(y)
        for r in p:
            ks = cds_of(r.get('NAME', ''))
            v = val(r.get('B19013_001E'))
            for k in ks:
                if v is not None: cd.setdefault(k, {})[str(y)] = v
                if len(ks) > 1: shared.setdefault(k, {})[str(y)] = [x for x in ks if x != k]
        for r in acs_rows(folder, y, 'county') or []:
            b = COUNTY.get(r['GEO_ID'][-5:])
            if b and val(r.get('B19013_001E')) is not None: boro.setdefault(b, {})[str(y)] = val(r['B19013_001E'])
        for r in acs_rows(folder, y, 'place') or []:
            if r['GEO_ID'].endswith('3651000') and val(r.get('B19013_001E')) is not None: nyc[str(y)] = val(r['B19013_001E'])
    if len(cd) != 59: die('expected 59 community districts, got %d: missing %s' % (len(cd), sorted(set(
        '%sCB%d' % (b, n) for b, c in [('MN', 12), ('BX', 12), ('BK', 18), ('QN', 14), ('SI', 3)] for n in range(1, c + 1)) - set(cd))))
    if len(boro) != 5: die('expected 5 boroughs')

    saipe = {}
    for fips, b in COUNTY.items():
        for r in csv.DictReader(open(os.path.join(folder, 'saipe_%s.csv' % fips))):
            v = val(list(r.values())[1])
            if v is not None: saipe.setdefault(b, {})[r['observation_date'][:4]] = v

    weekly = {}
    for r in csv.DictReader(open(os.path.join(folder, 'mortgage30.csv'))):
        try: weekly.setdefault(r['observation_date'][:7], []).append(float(r['MORTGAGE30US']))
        except (ValueError, KeyError): pass
    mortgage = {m: round(statistics.mean(v), 2) for m, v in sorted(weekly.items())}

    # verify: every written ACS value against the raw rows
    checked = 0
    for y in years:
        for r in acs_rows(folder, y, 'puma'):
            for k in cds_of(r.get('NAME', '')):
                if cd.get(k, {}).get(str(y)) != val(r.get('B19013_001E')): die('CD %s %d mismatch' % (k, y))
                checked += 1

    out = {
        'built': datetime.date.today().isoformat(),
        'acs': {'years': years, 'cd': cd, 'boro': boro, 'nyc': nyc, 'shared': shared,
                'source': 'U.S. Census Bureau, American Community Survey 1-year estimates, table B19013, median household income (dollars of each year)',
                'note': 'Community districts are Census PUMAs, labelled by district from 2012. Districts that share a PUMA share its figure. No standard 1-year estimates were released for 2020.'},
        'saipe': {'boro': saipe,
                  'source': 'U.S. Census Bureau, Small Area Income and Poverty Estimates, median household income by county (FRED series MHINY<county>A052NCEN)'},
        'mortgage': {'monthly': mortgage,
                     'source': 'Freddie Mac Primary Mortgage Market Survey, 30-year fixed rate (FRED MORTGAGE30US), monthly average of weekly rates'},
    }
    path = os.path.join(DATA, 'income-history.json')
    json.dump(out, open(path, 'w'), separators=(',', ':'))
    print('wrote %s: ACS years %s; %d CDs; SAIPE %s-%s; mortgage %s to %s; verified %d CD values'
          % (path, years, len(cd), min(saipe['Brooklyn']), max(saipe['Brooklyn']), min(mortgage), max(mortgage), checked))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        d = tempfile.mkdtemp()
        download(d)
        main(d)
