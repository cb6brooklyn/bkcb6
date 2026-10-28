#!/usr/bin/env python3
"""Rebuild data/hpd-affordable.json from NYC HPD "Affordable Housing Production by Building"
(NYC Open Data hg8x-zxpr): every building in a Housing New York / Housing Our Neighbors project since 2014.

Units are all_counted_units (rental plus homeownership units counted toward the plan). Years are the
project completion year (projects not yet complete have no year and are left out of by_year only).
Run from the repo root:  python3 tools/build_hpd_affordable.py
"""
import collections, datetime, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'https://data.cityofnewyork.us/resource/hg8x-zxpr.json?$limit=50000&$$app_token=HvFoIfzodzpRML7a1104Ca2tM'
INC = [('Extremely low', 'extremely_low_income_units'), ('Very low', 'very_low_income_units'), ('Low', 'low_income_units'),
       ('Moderate', 'moderate_income_units'), ('Middle', 'middle_income_units'), ('Other', 'other_income_units')]
BED = [('Studio', 'studio_units'), ('1 BR', '_1_br_units'), ('2 BR', '_2_br_units'), ('3 BR', '_3_br_units'),
       ('4 BR', '_4_br_units'), ('5 BR', '_5_br_units'), ('6+ BR', '_6_br_units'), ('Unknown', 'unknown_br_units')]


def main():
    r = subprocess.run(['curl', '-s', '-m', '300', '-g', URL], capture_output=True)
    rows = json.loads(r.stdout or b'null')
    if not isinstance(rows, list) or len(rows) < 5000: sys.exit('build_hpd_affordable: unexpected response')
    n = lambda x, k: int(round(float(x.get(k) or 0)))
    tot = sum(n(x, 'all_counted_units') for x in rows)
    by_year, by_boro, by_type, by_cd = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    by_year_type = collections.defaultdict(collections.Counter); by_year_income = collections.defaultdict(collections.Counter)
    for x in rows:
        u = n(x, 'all_counted_units'); y = (x.get('project_completion_date') or '')[:4]
        by_boro[x.get('borough')] += u; by_type[x.get('reporting_construction_type')] += u
        if x.get('community_board'): by_cd[x['community_board']] += u
        if y:
            by_year[y] += u; by_year_type[y][x.get('reporting_construction_type')] += u
            for lab, k in INC: by_year_income[y][lab] += n(x, k)
    out = {'total_units': tot, 'buildings': len(rows),
           'by_year': dict(sorted(by_year.items(), reverse=True)), 'by_boro': dict(by_boro),
           'by_income': {lab: sum(n(x, k) for x in rows) for lab, k in INC},
           'by_bed': {lab: sum(n(x, k) for x in rows) for lab, k in BED},
           'by_type': dict(by_type),
           'tenure': {'Rental': sum(n(x, 'counted_rental_units') for x in rows), 'Homeownership': sum(n(x, 'counted_homeownership_units') for x in rows)},
           'by_cd': dict(by_cd), 'by_year_type': {y: dict(v) for y, v in sorted(by_year_type.items(), reverse=True)},
           'by_year_income': {y: dict(v) for y, v in sorted(by_year_income.items(), reverse=True)},
           'source': 'NYC HPD Affordable Housing Production by Building, extracted %s' % datetime.date.today().isoformat()}
    if sum(out['by_income'].values()) != tot: print('note: income bands sum to %d of %d units' % (sum(out['by_income'].values()), tot))
    json.dump(out, open(os.path.join(ROOT, 'data', 'hpd-affordable.json'), 'w'), separators=(',', ':'))
    print('wrote data/hpd-affordable.json:', tot, 'units in', len(rows), 'buildings')


if __name__ == '__main__':
    main()
