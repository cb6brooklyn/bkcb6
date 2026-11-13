#!/usr/bin/env python3
"""Every ballot question that can be counted by community district, in one file: ballotmeasures/cdall.json.

A question can be counted by community district only where the NYC Board of Elections publishes its votes election district
by election district. That is 2014 onward: 2014 and 2017 from the site's election district archive (data/edhistory), 2018 to
2026 from ballotmeasures/cd/<cd>.json (built by scripts/ballot_ed_split.py). Two questions have no district file on vote.nyc
(2014 Proposal 1 and 2017 Proposal 2; the links 404) and are listed in "missing". An election district is counted in the
community district most of it sits in, on the district lines in force that year."""
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
# 2014 and 2017 from the archive
ARCH = {2014: ('2014-11-04-general', '14c', {'electronic distribution': 2, 'smart schools': 3}),
        2017: ('2017-11-07-general', '17b', {'constitutional convention': 1, 'forest preserve': 3})}
for y, (eid, rel, keys) in ARCH.items():
    e2c = {k: str(v) for k, v in json.load(open('data/edhistory/geo/ed2cd%s.json' % rel)).items()}
    idx = json.load(open('data/edhistory/e/%s/index.json' % eid))
    for c in idx['contests']:
        d = json.load(open('data/edhistory/e/%s/%s.json' % (eid, c['id'])))
        names = [x.strip().lower() for x in d['cands']]
        if 'yes' not in names or 'no' not in names: continue
        n = next((v for k, v in keys.items() if k in d['title'].lower()), None)
        if not n: continue
        iy, ino = names.index('yes') + 1, names.index('no') + 1
        cds = collections.defaultdict(lambda: [0, 0, 0, 0]); city = [0, 0, 0, 0]; boro = collections.defaultdict(lambda: [0, 0])
        for ed, v in d['eds'].items():
            yv, nv = (v[iy] if iy < len(v) else 0), (v[ino] if ino < len(v) else 0)
            if yv + nv == 0: continue
            city[0] += yv; city[1] += nv; city[3] += 1; city[2] += yv > nv
            cd = e2c.get(ed)
            if cd and ok_cd(cd):
                r = cds[cd]; r[0] += yv; r[1] += nv; r[3] += 1; r[2] += yv > nv
                boro[cd[0]][0] += yv; boro[cd[0]][1] += nv
        m = measure(y, n, 'state')
        out.append(dict(year=y, n=n, level='state', title=m['title'], result=m.get('result', ''), cds=dict(cds), boro=dict(boro), city=city))
# 2018 to 2026 from the community district files
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
missing = [dict(year=2014, n=1, title=measure(2014, 1)['title']), dict(year=2017, n=2, title=measure(2017, 2)['title'])]
json.dump(dict(cds=CDS, questions=out, missing=missing), open('ballotmeasures/cdall.json', 'w'), separators=(',', ':'))
print(len(out), 'questions;', collections.Counter(q['year'] for q in out))
for q in out: print(q['year'], q['n'], q['title'][:40], 'city', q['city'][:2], 'cds', len(q['cds']))
