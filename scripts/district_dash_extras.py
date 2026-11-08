#!/usr/bin/env python3
"""Two shared files for the district dashboards (assets/district-dash.js), each kept to the geography it is published by:

data/dashboards/_cd.json, by community district (59), each value as published for that community district:
  - NYC Health Department, 2026 Community Health Profiles (data/health/chp.json): population (Health Department
    estimate, 2024), life expectancy, adult flu vaccination, poverty, rent burden, with each measure's years and source;
  - DSNY Monthly Tonnage Data (NYC Open Data ebb7-mvp5): refuse, paper, metal/glass/plastic and organics collected,
    the last 12 months published, and the share of it that was recycling or organics.
data/dashboards/_resp.json, by borough and citywide: weekly COVID-19 and influenza cases, from the Health Department's
  respiratory illness data (github.com/nychealth/respiratory-illness-data, Case_data_*_by_group.csv), last 26 weeks.
Usage: python3 scripts/district_dash_extras.py [path to a respiratory-illness-data clone]"""
import csv, json, os, sys, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
RESP = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/nychealth/respiratory-illness-data'
CHP = ['Overall_Pop', 'Life_Expectancy', 'Flu_Vaccination', 'Poverty', 'Rent_Burden']
BORO = {'Manhattan': '1', 'Bronx': '2', 'Brooklyn': '3', 'Queens': '4', 'Staten Island': '5'}

def main():
    chp = json.load(open('data/health/chp.json'))
    CHP = list(chp['meta'])
    out = {'chp': {k: {'label': chp['meta'][k]['label'], 'def': chp['meta'][k].get('def', ''), 'years': chp['meta'][k].get('years', ''),
                       'unit': chp['meta'][k].get('unit', ''), 'src': chp['meta'][k].get('src', '')} for k in CHP},
           'chp_source': chp['source'], 'chp_url': chp['url'], 'cd': {}}
    for k in CHP:
        for cd, v in chp['values'][k].items():
            if len(cd) == 3 and cd.isdigit(): out['cd'].setdefault(cd, {})[k] = v
        out.setdefault('city', {})[k] = chp['values'][k].get('city')
    # DSNY tonnage, last 12 months published
    url = 'https://data.cityofnewyork.us/resource/ebb7-mvp5.json?' + urllib.parse.urlencode({'$select': 'distinct month', '$order': 'month DESC', '$limit': '12'})
    months = [r['month'] for r in json.load(urllib.request.urlopen(url, timeout=120))]
    q = {'$where': 'month in(' + ','.join("'" + m + "'" for m in months) + ')', '$limit': '50000'}
    rows = json.load(urllib.request.urlopen('https://data.cityofnewyork.us/resource/ebb7-mvp5.json?' + urllib.parse.urlencode(q), timeout=300))
    f = lambda r, k: float(r.get(k) or 0)
    seen = set()
    for r in rows:
        b = BORO.get(r['borough']); cdn = r.get('communitydistrict', '')
        if not b or not cdn.isdigit(): continue
        cd = b + cdn.zfill(2)
        key = (cd, r['month'])
        if key in seen: continue
        seen.add(key)
        t = out['cd'].setdefault(cd, {}).setdefault('dsny', {'refuse': 0, 'paper': 0, 'mgp': 0, 'organics': 0, 'months': 0})
        t['refuse'] += f(r, 'refusetonscollected'); t['paper'] += f(r, 'papertonscollected'); t['mgp'] += f(r, 'mgptonscollected')
        t['organics'] += f(r, 'resorganicstons') + f(r, 'schoolorganictons') + f(r, 'leavesorganictons') + f(r, 'xmastreetons'); t['months'] += 1
    for cd, v in out['cd'].items():
        t = v.get('dsny')
        if not t: continue
        tot = t['refuse'] + t['paper'] + t['mgp'] + t['organics']
        for k in ('refuse', 'paper', 'mgp', 'organics'): t[k] = round(t[k])
        t['diversion'] = round((t['paper'] + t['mgp'] + t['organics']) / tot * 100, 1) if tot else None
    out['dsny_months'] = [months[-1], months[0]]
    out['dsny_source'] = 'DSNY Monthly Tonnage Data, NYC Open Data (ebb7-mvp5)'
    json.dump(out, open('data/dashboards/_cd.json', 'w'), separators=(',', ':'))
    # respiratory illness, by borough
    resp = {'source': 'NYC Health Department respiratory illness data (github.com/nychealth/respiratory-illness-data), weekly cases by borough',
            'url': 'https://www.nyc.gov/assets/doh/respiratory-illness-data/', 'weeks': [], 'covid': {}, 'flu': {}}
    for key, fn, pre in (('covid', 'Case_data_COVID-19_by_group.csv', 'COVID-19 cases'), ('flu', 'Case_data_influenza_by_group.csv', 'Influenza cases')):
        rows = list(csv.DictReader(open(os.path.join(RESP, 'data', fn))))[-26:]
        if key == 'covid': resp['weeks'] = [r['date'] for r in rows]
        for area in ('overall', 'Bronx', 'Brooklyn', 'Manhattan', 'Queens', 'Staten Island'):
            col = f'{pre} {area}'
            resp[key]['NYC' if area == 'overall' else area] = [int(r[col]) if r.get(col, '').strip() else None for r in rows]
        resp[key + '_weeks'] = [r['date'] for r in rows]
    json.dump(resp, open('data/dashboards/_resp.json', 'w'), separators=(',', ':'))
    print(len(out['cd']), 'community districts;', out['dsny_months'], '; weeks', resp['weeks'][0], 'to', resp['weeks'][-1])

if __name__ == '__main__':
    main()
