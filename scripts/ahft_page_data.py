#!/usr/bin/env python3
"""Data for bkcb6.app/ballotmeasures/fasttrack/: every community district's rate of affordable housing development for
the first Affordable Housing Fast Track cycle (DCP, Oct 1, 2026: data/ahft/cd-summary-2021-2026.xlsx), how it voted on
2025 Question 2 (ballotmeasures/cdall.json) and its Fair Housing Growth Strategy 2030 targets (fhgs/report.json)."""
import json, os, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
x = pd.read_excel(P('data/ahft/cd-summary-2021-2026.xlsx'))
x.columns = ['cd', 'h2020', 'net', 'den', 'num', 'rate', 'rank']
B = {'MN': 1, 'BX': 2, 'BK': 3, 'QN': 4, 'SI': 5}
votes = json.load(open(P('ballotmeasures/cdall.json')))
q2 = next(q for q in votes['questions'] if q['year'] == 2025 and q['n'] == 2)
fh = json.load(open(P('fhgs/report.json')))
BC = {'mn': 1, 'bx': 2, 'bk': 3, 'qn': 4, 'si': 5}
FH = {str(BC[r['b']] * 100 + r['n']): r for r in fh['rows']}
rows = []
for _, r in x.iterrows():
    cd = str(B[r['cd'][:2]] * 100 + int(r['cd'][2:]))
    v = q2['cds'].get(cd); f = FH.get(cd, {})
    rows.append({'cd': cd, 'code': r['cd'], 'nb': f.get('nb', ''), 'homes': int(r['den']), 'aff': int(r['num']), 'rate': float(r['rate']),
                 'rank': int(r['rank']), 'ft': int(r['rank']) <= 12, 'q2': v[:2] if v else None,
                 'fh': {'t': f.get('t'), 'a': f.get('a')} if f else None})
assert len(rows) == 59 and sum(r['ft'] for r in rows) == 12
out = {'q2': {'title': q2['title'], 'city': q2['city'][:2]}, 'total_aff': int(x['num'].sum()), 'ft_aff': int(x[x['rank'] <= 12]['num'].sum()), 'rows': rows}
json.dump(out, open(P('ballotmeasures/fasttrack/data.json'), 'w'), separators=(',', ':'))
print(len(rows), 'districts; affordable homes', out['total_aff'], 'in the 12:', out['ft_aff'])
print(sorted((r['rank'], r['code'], r['nb']) for r in rows if r['ft']))
print('CB6', [r for r in rows if r['cd'] == '306'])
