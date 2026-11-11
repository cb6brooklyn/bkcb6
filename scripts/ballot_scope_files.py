#!/usr/bin/env python3
"""Borough and citywide files for the Ballot Breakdown map, built from the 59 community district files.

ballotmeasures/cd/B<1-5>.json, ballotmeasures/cd/NYC.json            the same shape as a district file, for a borough or the city
ballotmeasures/cd/geo/B<1-5>-<year>.json, cd/geo/NYC-<year>.json      every election district shape in that borough or the city

The yes and no totals for a borough or the city are the ones the district files already carry (their "boro" and
"city" rows), so they include election districts that have no shape on the map. Run after scripts/ballot_ed_split.py
and scripts/ballot_ed_geo.py: python3 scripts/ballot_scope_files.py"""
import json, os, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
CD = {}
for f in sorted(glob.glob('ballotmeasures/cd/[1-5][0-9][0-9].json')):
    d = json.load(open(f)); CD[d['cd']] = d
def build(key, cds):
    years = []
    for y0 in CD[cds[0]]['years']:
        yr = y0['year']; rows = [next(y for y in CD[c]['years'] if y['year'] == yr) for c in cds]
        tot = y0['city'] if key == 'NYC' else y0['boro']
        eds = {}
        for r in rows:
            for e in r['eds']: eds.setdefault(e[0], e)
        o = {k: v for k, v in y0.items() if k not in ('cd', 'eds')}
        o['cd'] = [[t[0], t[1]] for t in tot]; o['eds'] = [eds[k] for k in sorted(eds)]
        years.append(o)
        geo = {}
        for c in cds:
            p = 'ballotmeasures/cd/geo/%s-%d.json' % (c, yr)
            if os.path.exists(p): geo.update(json.load(open(p)))
        json.dump(geo, open('ballotmeasures/cd/geo/%s-%d.json' % (key, yr), 'w'), separators=(',', ':'))
    json.dump({'cd': key, 'years': years}, open('ballotmeasures/cd/%s.json' % key, 'w'), separators=(',', ':'))
    return len(years[0]['eds'])
for b in '12345': print('B' + b, build('B' + b, [c for c in CD if c[0] == b]), 'election districts with shapes in', CD[[c for c in CD if c[0] == b][0]]['years'][0]['year'])
print('NYC', build('NYC', list(CD)))
