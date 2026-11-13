#!/usr/bin/env python3
"""ballotmeasures/2026.json: the five 2026 city questions dug out of the Board of Elections' results by election
district (data/results/2026-general.json): citywide, by borough, by community district, how many election districts
said yes to all five, to some, or to none, and how many people who voted for Governor also voted on each question.
Re-run whenever the results file changes. Usage: python3 scripts/ballot_2026_dig.py"""
import json, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, 'data/results/2026-general.json')))
X = json.load(open(os.path.join(ROOT, 'app/data/civic/ed-crosswalk.json')))
M = json.load(open(os.path.join(ROOT, 'ballotmeasures/data.json')))['measures']
TITLES = {m['label'].split()[-1]: m['title'] for m in M if m['year'] == 2026 and m['level'] == 'city'}
Q = sorted([c for c in R['contests'] if c['k'].startswith('q')], key=lambda c: c['k'])
G = [c for c in R['contests'] if c['k'] == 'gov'][0]
eds = sorted(Q[0]['ed'])
BORO = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
M26 = json.load(open(os.path.join(ROOT, 'data/edhistory/geo/ed2cd26c.json')))
M26.update(json.load(open(os.path.join(ROOT, 'data/edhistory/geo/ed2cd-parks.json')))['26c'])
def cd(k):
    c = str(M26.get(k, ''))  # community district from the 2026 district lines
    return c if len(c) == 3 and c[0] in BORO and 1 <= int(c[1:]) <= 18 else ''
def boro(k):
    x = X.get(k)
    if x and len(x) > 4 and x[4]: return x[4]
    ad = int(k[:2]); return 'Queens' if ad <= 40 else 'Brooklyn' if ad <= 60 else 'Staten Island' if ad <= 64 else 'Manhattan' if ad <= 76 else 'Bronx'
z = lambda: [[0, 0] for _ in Q]
city = z(); bb = collections.defaultdict(z); cc = collections.defaultdict(z); nocd = 0
pat = collections.Counter(); bpat = collections.defaultdict(collections.Counter)
for k in eds:
    ys = []; c = cd(k); b = boro(k)
    if not c: nocd += 1
    for i, q in enumerate(Q):
        v = q['ed'][k]['v']
        for t in (city, bb[b]) + ((cc[c],) if c else ()):
            t[i][0] += v[0]; t[i][1] += v[1]
        if v[0] + v[1] > 0: ys.append(1 if v[0] > v[1] else 0)
    key = 'none' if len(ys) < len(Q) else str(sum(ys))
    pat[key] += 1; bpat[b][key] += 1
gov = sum(sum(e['v']) for e in G['ed'].values())
pc = lambda a: round(100 * a[0] / (a[0] + a[1]), 1) if a[0] + a[1] else None
out = {'asof': R['updated'], 'final': R['final'], 'source': R['source'], 'eds': len(eds),
       'questions': [{'n': i + 1, 'title': TITLES.get(str(i + 1), q['name']), 'yes': city[i][0], 'no': city[i][1], 'pctYes': pc(city[i]),
                      'votes': sum(city[i]), 'ofGovernor': round(100 * sum(city[i]) / gov, 1),
                      'edsNo': sum(1 for k in eds if q['ed'][k]['v'][1] > q['ed'][k]['v'][0]),
                      'edsYes': sum(1 for k in eds if q['ed'][k]['v'][0] > q['ed'][k]['v'][1])} for i, q in enumerate(Q)],
       'governorVotes': gov,
       'boroughs': {b: [{'yes': a[0], 'no': a[1], 'pctYes': pc(a)} for a in v] for b, v in sorted(bb.items())},
       'cds': {c: [pc(a) for a in v] for c, v in sorted(cc.items())},
       'cdVotes': {c: [a[0] + a[1] for a in v] for c, v in sorted(cc.items())},
       'edPattern': {k: pat.get(k, 0) for k in ('5', '4', '3', '2', '1', '0', 'none')},
       'edPatternBoro': {b: {k: v.get(k, 0) for k in ('5', '4', '3', '2', '1', '0', 'none')} for b, v in sorted(bpat.items())},
       'edsOutsideCD': nocd}
json.dump(out, open(os.path.join(ROOT, 'ballotmeasures/2026.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print(out['asof'], [q['pctYes'] for q in out['questions']], out['edPattern'], len(out['cds']), 'cds', nocd, 'EDs outside a community district')
for b, v in out['boroughs'].items(): print(b, [a['pctYes'] for a in v])
no = {c: v for c, v in out['cds'].items() if any(p is not None and p < 50 for p in v)}
print(len(no), 'CDs with a no', no)
lo = sorted(out['cds'].items(), key=lambda kv: min(kv[1])); print(lo[:3], lo[-3:])
