#!/usr/bin/env python3
"""data/dashboards/_zip.json: COVID-19 cases, deaths and vaccination for each Council, Assembly, State Senate and
Congressional district and each community district, apportioned from the ZIP codes the Health Department publishes
them by. These are estimates, and the dashboards mark them with an asterisk.

How: the Health Department publishes these by modified ZIP code area (MODZCTA). Each ZIP code area's counts and
population are split by the share of its land inside the district (area of the ZIP inside the district / area of the
ZIP, land only), and the shares are added up. A rate is the apportioned count over the apportioned population. This
assumes people and cases are spread evenly across each ZIP code area, which they are not, so the figures point in the
right direction but are not exact.

Sources (github.com/nychealth): coronavirus-data/totals/data-by-modzcta.csv (cumulative since Feb 29, 2020; the
date is in totals/summary.csv), covid-vaccine-data/people/coverage-by-modzcta-allages.csv (at least one dose, as of the
file's date), coronavirus-data/Geography-resources/MODZCTA_2010_WGS1984.geo.json (ZIP code area shapes).
Usage: python3 scripts/district_zip_health.py [folder holding the nychealth clones]"""
import csv, glob, json, os, sys, warnings
warnings.filterwarnings('ignore')
from shapely.geometry import shape
from shapely.ops import transform
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
NYCH = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/nychealth'
M = lambda x, y, z=None: (x * 84300.0, y * 111000.0)

import sys as _s; _s.path.insert(0, os.path.join(ROOT, 'scripts'))
from district_overlaps import clean

def geom(gj):
    g = shape(clean(gj))
    return transform(M, g if g.is_valid else g.buffer(0))

def main():
    land = geom({'type': 'GeometryCollection', 'geometries': [f['geometry'] for f in json.load(open('data/districts/city-nyc.geojson'))['features']]})
    land = land.buffer(0)
    zips = {}
    for f in json.load(open(os.path.join(NYCH, 'coronavirus-data/Geography-resources/MODZCTA_2010_WGS1984.geo.json')))['features']:
        g = geom(f['geometry']).intersection(land)
        if not g.is_empty: zips[f['properties']['MODZCTA']] = g
    case = {r['MODIFIED_ZCTA']: r for r in csv.DictReader(open(os.path.join(NYCH, 'coronavirus-data/totals/data-by-modzcta.csv')))}
    vax = {r['MODZCTA']: r for r in csv.DictReader(open(os.path.join(NYCH, 'covid-vaccine-data/people/coverage-by-modzcta-allages.csv')))}
    asof_cases = next((r['NUMBER_OF_NYC_RESIDENTS'] for r in csv.DictReader(open(os.path.join(NYCH, 'coronavirus-data/totals/summary.csv'))) if r['MEASURE'] == 'DATE_UPDATED'), '')
    asof_vax = next(iter(vax.values()))['DATE'] if vax else ''
    # childhood vaccination by ZIP code area (github.com/nychealth/immunization-data), latest quarter published
    IM = os.path.join(NYCH, 'immunization-data')
    geo = list(csv.DictReader(open(os.path.join(IM, 'geo/Main_Routine_Vaccine_Geo.csv'))))
    yq = max((r['YEAR_COVERAGE'], r['QUARTER']) for r in geo)
    KIDS = {'series': ('4313314', '24 - 35 months', None, 'Two-year-olds with the full 7-vaccine series'),
            'mmr': ('MMR', '24 - 35 months', None, 'Two-year-olds with the measles (MMR) vaccine'),
            'hpv': ('HPV', '13 - 17 years', '2 or 3', 'Teens 13 to 17 who finished the HPV vaccine series')}
    kid = {k: {} for k in KIDS}
    for r in geo:
        if (r['YEAR_COVERAGE'], r['QUARTER']) != yq: continue
        for k, (g, a, dz, _) in KIDS.items():
            if r['VACCINE_GROUP'] == g and r['AGE_GROUP'] == a and (dz is None or r['DOSES'] == dz):
                kid[k][r['MODZCTA']] = (float(r['COUNT_PEOPLE_VAC'] or 0), float(r['POP_DENOMINATOR'] or 0))
    fl = sorted(glob.glob(os.path.join(IM, 'visualizations/Flu_geo_all_*.csv')))[-1]
    fr = list(csv.DictReader(open(fl)))
    kid['flu'] = {str(r['MODZCTA']): (float(r['COUNT_PEOPLE_VAC'] or 0), float(r['POP_DENOMINATOR'] or 0)) for r in fr}
    KIDS['flu'] = (None, None, None, 'Children 6 months to 17 who got a flu shot, ' + fr[0]['YEAR_COVERAGE'].replace(' ', '') + ' season')
    kids_asof = '%s %s' % (yq[1], yq[0])
    keys = list(zips)
    tree = STRtree([zips[k] for k in keys])
    targets = []
    for ch in ('council', 'assembly', 'senate', 'congress', 'cb'):
        for p in sorted(glob.glob(f'data/districts/{ch}-*.geojson')):
            n = p.rsplit('-', 1)[1][:-8]
            if ch == 'cb' and not (len(n) == 3 and n.isdigit()): continue
            gj = json.load(open(p))
            targets.append((f'{ch}-{n}', geom({'type': 'GeometryCollection', 'geometries': [f['geometry'] for f in gj['features']]}).buffer(0).intersection(land)))
    out = {'about': 'Apportioned from ZIP code areas by the share of each ZIP code area’s land inside the district; an estimate.',
           'cases_asof': asof_cases, 'vax_asof': asof_vax,
           'sources': 'NYC Health Department, github.com/nychealth/coronavirus-data (totals/data-by-modzcta.csv) and covid-vaccine-data (people/coverage-by-modzcta-allages.csv)',
           'd': {}}
    for name, g in targets:
        acc = {'cases': 0.0, 'deaths': 0.0, 'pop_c': 0.0, 'vax': 0.0, 'pop_v': 0.0}
        parts = []
        for i in tree.query(g):
            z = keys[i]; zg = zips[z]
            share = zg.intersection(g).area / zg.area if zg.area else 0
            if share < 0.005: continue
            c = case.get(z); v = vax.get(z)
            if c:
                acc['cases'] += share * float(c['COVID_CASE_COUNT']); acc['deaths'] += share * float(c['COVID_DEATH_COUNT']); acc['pop_c'] += share * float(c['POP_DENOMINATOR'])
            if v:
                acc['vax'] += share * float(v['COUNT_1PLUS_CUMULATIVE']); acc['pop_v'] += share * float(v['POP_DENOMINATOR'])
            for k in kid:
                kv = kid[k].get(z)
                if kv: acc.setdefault('k_' + k, [0.0, 0.0]); acc['k_' + k][0] += share * kv[0]; acc['k_' + k][1] += share * kv[1]
            parts.append([z, round(share * 100, 1)])
        if not parts: continue
        out['d'][name] = {'cases': round(acc['cases']), 'deaths': round(acc['deaths']), 'pop': round(acc['pop_c']),
                          'case_rate': round(acc['cases'] / acc['pop_c'] * 100000) if acc['pop_c'] else None,
                          'death_rate': round(acc['deaths'] / acc['pop_c'] * 100000, 1) if acc['pop_c'] else None,
                          'vax_1plus': round(acc['vax']), 'vax_pct': round(acc['vax'] / acc['pop_v'] * 100, 1) if acc['pop_v'] else None,
                          'kids': {k: round(acc['k_' + k][0] / acc['k_' + k][1] * 100, 1) for k in kid if acc.get('k_' + k) and acc['k_' + k][1]},
                          'zips': sorted(parts, key=lambda x: -x[1])}
    cs = [case[z] for z in case]
    out['city'] = {'cases': sum(int(r['COVID_CASE_COUNT']) for r in cs), 'deaths': sum(int(r['COVID_DEATH_COUNT']) for r in cs),
                   'pop': round(sum(float(r['POP_DENOMINATOR']) for r in cs))}
    out['city']['case_rate'] = round(out['city']['cases'] / out['city']['pop'] * 100000)
    out['city']['death_rate'] = round(out['city']['deaths'] / out['city']['pop'] * 100000, 1)
    vs = list(vax.values())
    out['city']['vax_pct'] = round(sum(float(r['COUNT_1PLUS_CUMULATIVE']) for r in vs) / sum(float(r['POP_DENOMINATOR']) for r in vs) * 100, 1)
    out['kids_labels'] = {k: v[3] for k, v in KIDS.items()}
    out['kids_asof'] = kids_asof
    # citywide as the Health Department publishes it (borough files, 'Citywide' row)
    out['city']['kids'] = {}
    for r in (r for f in glob.glob(os.path.join(IM, 'visualizations/*borough*.csv')) for r in csv.DictReader(open(f))):
        if r.get('BOROUGH') != 'Citywide': continue
        y, q = r['YEAR_COVERAGE'], r['QUARTER']
        for k, (g, a, dz, _) in KIDS.items():
            if k == 'flu': hit = r['VACCINE_GROUP'] == 'Flu' and r['AGE_GROUP'] == '6 months - 17 years' and y.replace(' ', '') == fr[0]['YEAR_COVERAGE'].replace(' ', '') and q == fr[0]['QUARTER']
            else: hit = (y, q) == yq and r['VACCINE_GROUP'] == g and r['AGE_GROUP'] == a and (dz is None or r['DOSES'] == dz)
            if hit and k not in out['city']['kids']: out['city']['kids'][k] = float(r['PERC_VAC'])
    out['sources'] += '; childhood vaccination: immunization-data (geo/Main_Routine_Vaccine_Geo.csv, visualizations/' + os.path.basename(fl) + ')'
    json.dump(out, open('data/dashboards/_zip.json', 'w'), separators=(',', ':'))
    print(out['kids_asof'], out['city']['kids']); print(len(out['d']), 'areas;', out['cases_asof'], out['vax_asof'], json.dumps(out['d'].get('cb-306')), json.dumps(out['city']))

if __name__ == '__main__':
    main()
