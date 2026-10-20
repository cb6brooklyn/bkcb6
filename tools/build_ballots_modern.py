"""Per-election ballot index for 2000-2026 from data/edhistory: every contest with its candidates, party lines and
totals, and for each election district (or Assembly district, for AD-level elections) the contests on its ballot.
Output: data/ballots/e/<election id>.json"""
import json, glob, os
CAT = json.load(open('data/edhistory/catalog.json'))
os.makedirs('data/ballots/e', exist_ok=True)
summary = []
for el in CAT['elections']:
    eid = el['id']; d = 'data/edhistory/e/' + eid
    idx = json.load(open(d + '/index.json'))
    out = {'id': eid, 'date': el['date'], 'type': el['type'], 'label': el.get('label'), 'level': idx.get('level', 'ed'),
           'geo': idx.get('geo') or idx.get('adGeo'), 'contests': [], 'keys': {}}
    for c in idx['contests']:
        f = '%s/%s.json' % (d, c['id'])
        if not os.path.exists(f): continue
        x = json.load(open(f))
        n = len(out['contests'])
        cands = []
        for i, nm in enumerate(x.get('cands', [])):
            cands.append([nm, (x.get('parties') or [])[i] if i < len(x.get('parties') or []) else [], (x.get('total') or [None])[i + 1] if len(x.get('total') or []) > i + 1 else None])
        out['contests'].append({'t': x.get('title'), 'o': x.get('office'), 'd': x.get('district'), 'p': x.get('party') or '', 'vf': x.get('voteFor'), 'rcv': x.get('rcv'), 'c': cands, 'tot': (x.get('total') or [None])[0]})
        for k in (x.get('eds') or {}):
            out['keys'].setdefault(k, []).append(n)
        for k in (x.get('ads') or {}):
            out['keys'].setdefault('A' + str(int(k)), []).append(n)
    s = json.dumps(out, separators=(',', ':'))
    open('data/ballots/e/%s.json' % eid, 'w').write(s)
    summary.append((eid, len(out['contests']), len(out['keys']), len(s)))
for r in summary: print(*r)
print('total MB', sum(r[3] for r in summary) / 1e6)

# ---- index of every election with a ballot (modern + 2026 certified + historical files when present) ----
idx = [{'id': e['id'], 'date': e['date'], 'type': e['type'], 'label': e.get('label'), 'k': 'm'} for e in CAT['elections']]
idx.append({'id': '2026-11-03-general', 'date': '2026-11-03', 'type': 'general', 'label': 'General Election', 'k': 'g26'})
if os.path.exists('data/ballots/hist-index.json'):
    idx += json.load(open('data/ballots/hist-index.json'))
idx.sort(key=lambda e: (e['date'], e['id']))
json.dump(idx, open('data/ballots/index.json', 'w'), separators=(',', ':'))
print('index', len(idx))
