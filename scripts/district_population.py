#!/usr/bin/env python3
"""data/redistricting/population.json: each district's 2020 Census population exactly as the body that drew the lines
published it, read from their reports (kept in data/redistricting/):
  City Council   NYC Districting Commission, Final Plan data table (Oct 6, 2022): 2020 population; the race and
                 ethnicity counts there are of the voting-age population (18 and over), as published.
  State Assembly LATFOR / IRC 2024 Assembly population report: NYS adjusted population (people in state prisons
                 counted at their home address, as state law requires), by race and ethnicity.
  State Senate   LATFOR 2022 Senate population report (the lines still in use): NYS adjusted population, by race.
  Congress       LATFOR 2024 Congress population report: 2020 population, by race and ethnicity.
Nothing is estimated or apportioned. Requires pdftotext."""
import json, os, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'data/redistricting')
num = lambda t: float(t.replace(',', '').replace('%', '').replace('‐', '-').replace('−', '-'))

def lines(pdf):
    return subprocess.run(['pdftotext', '-layout', os.path.join(D, pdf), '-'], capture_output=True, text=True).stdout.splitlines()

def latfor(pdf, label, nfirst):
    out = {}
    for ln in lines(pdf):
        t = ln.split()
        if len(t) != 20 or not t[0].isdigit(): continue
        n = t[0]
        if n in out: continue
        v = [num(x) for x in t[1:]]
        c = v[3:11]
        out[n] = {'pop': int(v[0]), 'pop_label': label,
                  'race': {'White (non-Hispanic)': int(c[0]), 'Black (non-Hispanic)': int(c[1]), 'Hispanic or Latino': int(c[2]),
                           'Asian (non-Hispanic)': int(c[3]), 'Other or more than one race': int(c[4] + c[5] + c[6] + c[7])},
                  'race_of': 'all residents'}
    return out

def council():
    out = {}
    for ln in lines('nyc-council-2022-final-plan-data-table.pdf'):
        t = ln.split()
        if len(t) != 14 or not t[0].isdigit(): continue
        if t[0] in out: continue   # the first table is the Final Plan; later ones are other versions
        v = [num(x) for x in t[1:]]
        out[t[0]] = {'pop': int(v[0]), 'pop_label': '2020 Census population',
                     'race': {'Hispanic or Latino': int(v[5]), 'Asian': int(v[7]), 'Black': int(v[9]), 'White and all others': int(v[11])},
                     'race_of': 'residents 18 and over', 'vap': int(v[4])}
    return out

def main():
    data = {
        'council': council(),
        'assembly': latfor('nys-assembly-2024-population-report.pdf', '2020 Census population, NYS adjusted', 0),
        'senate': latfor('nys-senate-2022-population-report.pdf', '2020 Census population, NYS adjusted', 0),
        'congress': latfor('nys-congress-2024-population-report.pdf', '2020 Census population', 0),
        'sources': {
            'council': 'NYC Districting Commission, Final Plan for City Council, data table (Oct 6, 2022)',
            'assembly': 'NYS Independent Redistricting Commission / LATFOR, 2024 Assembly Population Report by District',
            'senate': 'LATFOR, 2022 Senate Population Report by District',
            'congress': 'NYS Independent Redistricting Commission / LATFOR, 2024 Congress Population Report by District'}}
    json.dump(data, open(os.path.join(D, 'population.json'), 'w'), indent=0)
    print({k: len(v) for k, v in data.items() if k != 'sources'})
    print(data['council'].get('39'), data['assembly'].get('44'), data['senate'].get('26'), data['congress'].get('10'), sep='\n')

if __name__ == '__main__':
    main()
