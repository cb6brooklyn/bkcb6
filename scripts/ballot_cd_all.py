#!/usr/bin/env python3
"""Every ballot question that can be counted by community district, in one file: ballotmeasures/cdall.json.

A question can be counted by community district only where the NYC Board of Elections publishes its votes election district
by election district: 2014 onward. Every year comes from ballotmeasures/cd/<cd>.json (built by scripts/ballot_ed_split.py, which
says where each year's district files come from and which district lines it uses)."""
import json, os, re, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
M = json.load(open('ballotmeasures/data.json'))['measures']
CDS = [b + '%02d' % i for b, n in [('3', 18), ('1', 12), ('2', 12), ('4', 14), ('5', 3)] for i in range(1, n + 1)]
def ok_cd(c): c = str(c); return len(c) == 3 and c[0] in '12345' and 1 <= int(c[1:]) <= 18
def num(label): return int(re.sub(r'\D', '', label or '') or 0)
def measure(y, n, level=None):
    ms = [m for m in M if m['year'] == y and num(m.get('label')) == n and (level is None or m['level'] == level)]
    return ms[0] if ms else None

out = []   # each: year, n, level, title, result, cds {cd: [yes, no, edsYes, eds]}, boro {b: [yes,no]}, city [yes,no,edsYes,eds]
# 2014 to 2026 from the community district files
per = collections.defaultdict(dict)
for f in sorted(glob.glob('ballotmeasures/cd/[0-9][0-9][0-9].json')):
    D = json.load(open(f)); cd = os.path.basename(f)[:3]
    for o in D['years']:
        for i, q in enumerate(o['questions']):
            key = (o['year'], q['label'])
            if key not in per:
                per[key] = dict(year=o['year'], n=num(q['label']), level=q.get('level') or ('state' if q['label'].startswith('State') else 'city'),
                                title=q['title'], city=o['city'][i], boro={}, cds={}, unofficial=bool(o.get('unofficial')))
            ys = [r[i + 1] for r in o['eds'] if sum(r[i + 1]) > 0]
            per[key]['cds'][cd] = [o['cd'][i][0], o['cd'][i][1], sum(1 for r in ys if r[0] > r[1]), len(ys)]
            per[key]['boro'][cd[0]] = o['boro'][i][:2]
for key, q in per.items():
    m = measure(q['year'], q['n'])
    q['result'] = (m or {}).get('result', '')
    if m: q['title'] = m['title']
    out.append(q)
out.sort(key=lambda q: (q['year'], q['n']))
missing = []
json.dump(dict(cds=CDS, questions=out, missing=missing), open('ballotmeasures/cdall.json', 'w'), separators=(',', ':'))
print(len(out), 'questions;', collections.Counter(q['year'] for q in out))
for q in out: print(q['year'], q['n'], q['title'][:40], 'city', q['city'][:2], 'cds', len(q['cds']))
