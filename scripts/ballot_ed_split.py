#!/usr/bin/env python3
"""How each election district treated the questions on its ballot, year by year.

data/ballots/ed/<year>.json   yes and no in every election district for every question that year
ballotmeasures/edsplit.json   per year: the questions, how many districts approved all, some or none, and the most
                              common combinations

Sources: the NYC Board of Elections' EDLevel.csv for each question (2018 to 2024; 2014 and 2017 from data/edhistory and data/ballots/archive; pass the folder of downloaded files
named <year>-<nn>.csv as the first argument to rebuild those years), the site's election district archive for 2025
(data/edhistory), and the election night count for 2026 (data/results). A year is only included when every question on
its ballot has a district file. Usage: python3 scripts/ballot_ed_split.py [folder of BOE csv files]"""
import json, os, sys, csv, re, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
M = json.load(open('ballotmeasures/data.json'))['measures']
def num(label): return int(re.sub(r'\D', '', label) or 0)
def measures(y): return sorted([m for m in M if m['year'] == y and (m.get('nyc') or m['level'] == 'city')], key=lambda m: num(m['label']))

# 1. BOE csv files -> data/ballots/ed/<year>.json
if len(sys.argv) > 1:
    by = collections.defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.csv'))):
        y, q = re.match(r'(\d{4})-(\d\d)\.csv', os.path.basename(f)).groups()
        if int(y) < 2018: continue   # 2014 and 2017 each have a question whose file link on vote.nyc is broken
        eds = collections.defaultdict(lambda: [0, 0]); title = ''
        for r in csv.reader(open(f, encoding='latin-1')):
            if len(r) < 22: continue
            ad, ed, unit, tally = r[11].strip(), r[12].strip(), r[20].strip().upper(), r[21].strip().replace(',', '')
            title = r[17].strip() or title
            if unit in ('YES', 'NO') and ad.isdigit() and ed.isdigit():
                eds['%02d%03d' % (int(ad), int(ed))][0 if unit == 'YES' else 1] += int(tally or 0)
        by[int(y)][int(q)] = {'title': title, 'eds': dict(eds)}
    for y, qs in by.items():
        json.dump({'year': y, 'source': 'NYC Board of Elections, EDLevel.csv for each question', 'questions': {str(q): v for q, v in sorted(qs.items())}},
                  open('data/ballots/ed/%d.json' % y, 'w'), separators=(',', ':'))
# 2. 2025 from the archive, 2026 from the election night count
def from_archive(eid):
    idx = json.load(open('data/edhistory/e/%s/index.json' % eid)); qs = {}
    for c in idx['contests']:
        d = json.load(open('data/edhistory/e/%s/%s.json' % (eid, c['id'])))
        names = [x.strip().lower() for x in d['cands']]
        if 'yes' not in names or 'no' not in names: continue
        iy, in_ = names.index('yes') + 1, names.index('no') + 1
        qs[d['title']] = {k: [v[iy] if iy < len(v) else 0, v[in_] if in_ < len(v) else 0] for k, v in d['eds'].items()}
    return qs
a25 = from_archive('2025-11-04-general')
# 2014 and 2017: the site's election district archive, plus the two questions whose files are gone from vote.nyc, copied
# from the Internet Archive (data/ballots/archive/<year>-<nn>.csv: AD, ED, County, EDAD Status, Event, Party, Office,
# District Key, VoteFor, Unit Name, Tally)
def old_csv(f):
    eds = collections.defaultdict(lambda: [0, 0])
    rd = csv.reader(open(f, encoding='utf-8-sig', errors='replace')); next(rd, None)
    for r in rd:
        if len(r) < 11: continue
        u = r[9].strip().lower()
        if u in ('yes', 'no') and r[0].strip().isdigit() and r[1].strip().isdigit():
            eds['%02d%03d' % (int(r[0]), int(r[1]))][0 if u == 'yes' else 1] += int(r[10].strip().replace(',', '') or 0)
    return dict(eds)
OLD = {2014: ('2014-11-04-general', {2: 'electronic distribution', 3: 'smart schools'}),
       2017: ('2017-11-07-general', {1: 'constitutional convention', 3: 'forest preserve'})}
def pick_old(y, m):
    n = num(m['label']); f = 'data/ballots/archive/%d-%02d.csv' % (y, n)
    if os.path.exists(f): return old_csv(f)
    a = from_archive(OLD[y][0]); key = OLD[y][1].get(n)
    t = [k for k in a if key and key in k.lower()]
    return a[t[0]] if len(t) == 1 else None
def pick25(m):
    key = {'state': 'olympic', 2: 'fast track', 3: 'simplify', 4: 'appeals board', 5: 'digital city map', 6: 'move local elections'}[('state' if m['level'] == 'state' else num(m['label']))]
    t = [k for k in a25 if key in k.lower()]; assert len(t) == 1, (key, t); return a25[t[0]]
R = json.load(open('data/results/2026-general.json'))
r26 = {int(c['k'][1:]): {k: e['v'][:2] for k, e in c['ed'].items()} for c in R['contests'] if re.match(r'q\d+$', c['k'])}

# election district -> community district, from the district lines in force at each election
PARKS = json.load(open('data/edhistory/geo/ed2cd-parks.json'))
CAT = {e['id']: e for e in json.load(open('data/edhistory/catalog.json'))['elections']}
X26 = json.load(open('app/data/civic/ed-crosswalk.json'))
def ed2cd(y):
    if y == 2026: rel = '26c'  # DCP's latest release before the 2026 general (Aug 2026); same assignments as 26a1
    elif y == 2017: rel = '17c'  # DCP's latest release before the 2017 general (Aug 2017); every district with votes is on it
    else: rel = [v for k, v in CAT.items() if k.startswith(str(y) + '-11-') and k.endswith('general')][0]['release']
    m = json.load(open('data/edhistory/geo/ed2cd%s.json' % rel))
    # an election district that sits mostly in a park, airport or other non-residential area is counted in the
    # community district it overlaps most (or the nearest one), so its voters are not left out of every district
    m.update(PARKS.get(rel, {}))
    global RAW
    RAW = {k: str(c) for k, c in m.items()}
    return {k: c for k, c in m.items() if len(str(c)) == 3 and str(c)[0] in '12345' and 1 <= int(str(c)[1:]) <= 18}
RAW = {}
def boro_of(k):
    # the borough of the election district's community district (Assembly District 64 is in two boroughs), else by Assembly District
    c = RAW.get(k, '')
    if len(c) == 3 and c[0] in '12345': return c[0]
    ad = int(k[:2]); return '4' if ad <= 40 else '3' if ad <= 60 else '5' if ad <= 64 else '1' if ad <= 76 else '2'
out = {'years': []}
PER = collections.defaultdict(list)   # community district -> its election districts' votes, year by year (ballotmeasures/cd/<cd>.json)
for y in range(2014, 2027):
    ms = measures(y)
    if not ms: continue
    qs = []
    if y in OLD: qs = [(m, e) for m in ms for e in [pick_old(y, m)] if e]
    elif y == 2025: qs = [(m, pick25(m)) for m in ms]
    elif y == 2026: qs = [(m, r26[num(m['label'])]) for m in ms if num(m['label']) in r26]
    elif os.path.exists('data/ballots/ed/%d.json' % y):
        d = json.load(open('data/ballots/ed/%d.json' % y))['questions']
        qs = [(m, d[str(num(m['label']))]['eds']) for m in ms if str(num(m['label'])) in d]
    if len(qs) != len(ms) or len(qs) < 2:
        print(y, 'left out:', len(qs), 'of', len(ms), 'questions have a district file'); continue
    # the district counts must add up to the citywide count on file
    for m, e in qs:
        ty, tn = sum(v[0] for v in e.values()), sum(v[1] for v in e.values())
        if m.get('nyc') and m['nyc'].get('yes') and abs(ty - m['nyc']['yes']) > max(50, 0.002 * m['nyc']['yes']):
            print('  CHECK', y, m['label'], 'districts add to', ty, tn, 'citywide on file', m['nyc']['yes'], m['nyc']['no'])
    eds = sorted(set.intersection(*[set(e) for _, e in qs]))
    n = len(qs); pat = collections.Counter(); combo = collections.Counter(); skipped = 0
    for k in eds:
        r = [e[k] for _, e in qs]
        if any(a + b == 0 for a, b in r): skipped += 1; continue
        bits = tuple(1 if a > b else 0 for a, b in r); pat[sum(bits)] += 1; combo[bits] += 1
    counted = sum(pat.values())
    # by community district
    x = ed2cd(y); cd = collections.defaultdict(lambda: [[0, 0] for _ in qs]); outside = [0, 0]
    for i, (_, e) in enumerate(qs):
        for k, v in e.items():
            c = x.get(k)
            if c: cd[c][i][0] += v[0]; cd[c][i][1] += v[1]
            elif i == 0: outside[0] += v[0] + v[1]; outside[1] += 1 if v[0] + v[1] else 0
    cdyes = {c: sum(1 for a, b in v if a > b) for c, v in cd.items()}
    bo = collections.defaultdict(lambda: [[0, 0, 0, 0] for _ in qs]); city = [[0, 0, 0, 0] for _ in qs]
    for i, (_, e) in enumerate(qs):
        for k, v in e.items():
            if v[0] + v[1] == 0: continue
            for t in (bo[boro_of(k)][i], city[i]):
                t[0] += v[0]; t[1] += v[1]; t[2] += 1 if v[0] > v[1] else 0; t[3] += 1
    edsby = collections.defaultdict(list)
    for k in sorted(set.union(*[set(e) for _, e in qs])):
        c = x.get(k)
        if c and any(sum(e.get(k, [0, 0])) for _, e in qs): edsby[c].append([k] + [e.get(k, [0, 0]) for _, e in qs])
    for c, rows in edsby.items():
        PER[c].append({'year': y, 'unofficial': y == 2026 and not R.get('final'),
                       'questions': [{'label': ('State ' if m['level'] == 'state' else 'City ') + str(num(m['label'])), 'title': m['title'], 'level': m['level']} for m, _ in qs],
                       'cd': cd[c], 'boro': [t[:] for t in bo[c[0]]], 'city': [t[:] for t in city], 'eds': rows})
    out['years'].append({'year': y, 'n': n, 'unofficial': y == 2026 and not R.get('final'),
        'questions': [{'label': ('State ' if m['level'] == 'state' else 'City ') + str(num(m['label'])), 'title': m['title'],
                       'yes': sum(v[0] for v in e.values()), 'no': sum(v[1] for v in e.values()),
                       'edsYes': sum(1 for k in eds if e[k][0] > e[k][1]), 'edsNo': sum(1 for k in eds if e[k][1] > e[k][0])} for m, e in qs],
        'eds': counted, 'noVotes': skipped, 'all': pat.get(n, 0), 'none': pat.get(0, 0), 'split': counted - pat.get(n, 0) - pat.get(0, 0),
        'byCount': {str(i): pat.get(i, 0) for i in range(n, -1, -1)},
        'combos': [[''.join('Y' if b else 'N' for b in bits), c] for bits, c in combo.most_common(6)],
        'cds': {c: v for c, v in sorted(cd.items())}, 'cdAll': sum(1 for v in cdyes.values() if v == n), 'cdNone': sum(1 for v in cdyes.values() if v == 0),
        'cdSplit': sum(1 for v in cdyes.values() if 0 < v < n), 'outsideVotes': outside[0], 'outsideEDs': outside[1]})
    o = out['years'][-1]; print(y, n, 'questions', counted, 'districts: all', o['all'], 'split', o['split'], 'none', o['none'], '(%d%% split)' % round(100 * o['split'] / counted), '| CDs', len(o['cds']), 'all', o['cdAll'], 'split', o['cdSplit'], 'none', o['cdNone'], 'votes outside a CD', o['outsideVotes'])
json.dump(out, open('ballotmeasures/edsplit.json', 'w'), ensure_ascii=False, separators=(',', ':'))
os.makedirs('ballotmeasures/cd', exist_ok=True)
for c, yrs in PER.items():
    json.dump({'cd': c, 'years': sorted(yrs, key=lambda o: -o['year'])}, open('ballotmeasures/cd/%s.json' % c, 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(PER), 'community district files')
