"""BKCB6 voter registration by party and election district, March 2008 to February 2026:
data/enrollment/cb6.json from data/enrollment/src/cb6-eds.txt.

Source: NYS Board of Elections, Enrollment by Election District, Kings County
(https://elections.ny.gov/enrollment-election-district; xlsx files from November 2018 on, PDFs before; the
November 1, 2011 page links to the wrong file). Each row is the TOTAL line for one election district
(active plus inactive voters) followed by the active count. An ED is in BKCB6 by the ED-to-community-district
file of the Board of Elections ED map in use at the date (data/edhistory/geo/ed2cd<map>.json; the map is the
latest one published on or within 30 days after the date, since the BOE renumbers EDs before the city's map file
follows). Before July 2012 there is no ED map file, so EDs are assigned by the 2010 Census voting districts for
Kings County (tl_2010_36047_vtd10), which are the EDs of about 2010.
Line format: #MM/DD/YYYY PARTY,...,TOTAL map=<map> absent=<EDs on the map with no voters listed>
             AADDD:n,n,...,total;active"""
import json, re
NAMES = {'DEM': 'Democratic', 'REP': 'Republican', 'CON': 'Conservative', 'WOR': 'Working Families', 'GRE': 'Green',
         'LBT': 'Libertarian', 'IND': 'Independence', 'SAM': 'SAM', 'WEP': "Women's Equality", 'REF': 'Reform',
         'RTH': 'Right to Life', 'SWP': 'Socialist Workers', 'OTH': 'Other', 'BLANK': 'No party (blank)'}
out = []
for b in open('data/enrollment/src/cb6-eds.txt').read().strip().split('\n#'):
    L = b.strip().lstrip('#').split('\n')
    h = L[0].split(' ')
    d = h[0]; cols = h[1].split(','); meta = dict(x.split('=') for x in h[2:])
    iso = d[6:] + '-' + d[:2] + '-' + d[3:5]
    eds = {}; tot = [0] * len(cols); act = 0
    for l in L[1:]:
        k, rest = l.split(':'); v, a = rest.split(';')
        v = [int(x) for x in v.split(',')]
        assert sum(v[:-1]) == v[-1], (d, k)
        eds[k] = v + [int(a)]
        tot = [x + y for x, y in zip(tot, v)]; act += int(a)
    out.append({'date': iso, 'map': meta['map'], 'parties': cols[:-1], 'eds': eds,
                'total': dict(zip(cols, tot)), 'active': act, 'absent': [x for x in meta.get('absent', '').split('.') if x]})
out.sort(key=lambda x: x['date'])
json.dump({'about': __doc__.strip(), 'board': '306', 'names': NAMES, 'dates': out},
          open('data/enrollment/cb6.json', 'w'), separators=(',', ':'))
for x in out[::5] + [out[-1]]:
    t = x['total']
    print(x['date'], x['map'], len(x['eds']), 'total', t['TOTAL'], 'DEM %.1f%% REP %.1f%% BLANK %.1f%%' % (100 * t['DEM'] / t['TOTAL'], 100 * t['REP'] / t['TOTAL'], 100 * t['BLANK'] / t['TOTAL']))
