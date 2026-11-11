"""Builds ballotmeasures/data.json from data/ballots/measures.json plus community district results
from data/edhistory (2014 on) and the 2026 election night results by election district."""
import json, os, re
D = json.load(open('data/ballots/measures.json'))
M = D['measures']
CAT = json.load(open('data/edhistory/catalog.json'))['elections']
AB = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
code = lambda c: AB[str(c)[0]] + str(c)[1:].zfill(2)
def norm(s): return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()
# every yes/no contest with community district results
YN = []
for e in CAT:
    d = 'data/edhistory/e/' + e['id']
    for c in json.load(open(d + '/index.json'))['contests']:
        f = '%s/%s.json' % (d, c['id'])
        if not os.path.exists(f): continue
        x = json.load(open(f))
        cs = [s.lower() for s in (x.get('cands') or [])]
        if sorted(cs[:2]) != ['no', 'yes'] or len(cs) != 2: continue
        iy, ino = cs.index('yes') + 1, cs.index('no') + 1
        cd = {code(k): [v[iy], v[ino]] for k, v in (x.get('cd') or {}).items() if int(str(k)[1:]) <= 18}
        YN.append(dict(year=int(e['date'][:4]), title=x.get('title'), yes=x['total'][iy], no=x['total'][ino], cd=cd))
used = set()
for m in M:
    if not m.get('nyc'): continue
    for i, y in enumerate(YN):
        if i in used or y['year'] != m['year']: continue
        if y['yes'] == m['nyc']['yes'] and y['no'] == m['nyc']['no']:
            used.add(i)
            if y['cd']: m['cd'] = y['cd']
            break
# 2005 city questions found in the BOE history files
for i, y in enumerate(YN):
    if y['year'] == 2005 and y['title'].startswith(('Q3', 'Q4')):
        lab = 'Question ' + y['title'][1]
        t = re.sub(r'^Q\d\.?\s*', '', y['title']).replace(' (nyc)', '')
        if not any(m['year'] == 2005 and m['label'] == lab for m in M):
            M.append(dict(year=2005, date='2005-11-08', level='city', label=lab, title=t[:1] + t[1:].lower(), type='City charter question',
                          result='Approved' if y['yes'] > y['no'] else 'Defeated', nyc=dict(yes=y['yes'], no=y['no'], pctYes=round(100 * y['yes'] / (y['yes'] + y['no']), 1)),
                          src=['NYC Board of Elections results, November 8, 2005 general election', '2005 Charter Revision Commission, ballot questions and abstracts: https://www.nyc.gov/assets/charter/downloads/pdf/crc_ballot_questions.pdf'],
                          what={'Question 3': 'Required the Mayor and the Chief Administrative Law Judge to issue a conduct code for the City\u2019s administrative law judges and hearing officers, who can be disciplined for breaking it.',
                                'Question 4': 'Made permanent the rules from a 1975 state law that was set to expire: a budget balanced each year, a four-year financial plan, limits on short-term borrowing and a yearly audit.'}[lab]))
# 2026 by community district from election night results
eds = {f['properties']['id']: f['properties'] for f in json.load(open('electionexplainer/map/eds.geojson'))['features']}
R26 = json.load(open('data/results/2026-general.json'))
for c in R26['contests']:
    if not c.get('k', '').startswith('q'): continue
    n = int(c['k'][1:])
    cd = {}
    for e, v in c['ed'].items():
        p = eds.get(e)
        if not p or not p.get('cb') or int(p['cb'][1:]) > 18: continue
        k = code(p['cb']); a = cd.setdefault(k, [0, 0]); a[0] += v['v'][0]; a[1] += v['v'][1]
    for m in M:
        if m['year'] == 2026 and m['label'] == 'Question %d' % n: m['cd'] = cd; m['asof'] = R26['updated']
M.sort(key=lambda m: (m['date'] or str(m['year']), m['level'] != 'state', m['label']))
for i, m in enumerate(M): m['id'] = '%d-%s-%s' % (m['year'], m['level'], re.sub(r'[^a-z0-9]+', '-', (m['label'] or m['title']).lower()).strip('-'))
ids = {}
for m in M:
    if m['id'] in ids: ids[m['id']] += 1; m['id'] += '-%d' % ids[m['id']]
    else: ids[m['id']] = 1
json.dump(dict(about=D['about'], since=D.get('since'), measures=M), open('ballotmeasures/data.json', 'w'), separators=(',', ':'), ensure_ascii=False)
print(len(M), 'with district results', sum(1 for m in M if m.get('cd')), os.path.getsize('ballotmeasures/data.json') // 1024, 'KB')
