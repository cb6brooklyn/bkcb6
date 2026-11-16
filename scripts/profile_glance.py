#!/usr/bin/env python3
"""Mike's guide (Google Doc "NYC Agencies and Precincts: What They Do and Why You May Need to Know", Nov 15, 2026, updated Nov 16,
saved as data/guide/what-it-does-2026-11-16.md) at the top of every matching Directory profile, in the apps and on the
site. Agencies: what it does and why you may need to know. Precincts and precinct councils: neighborhoods and when the
council meets. School districts and CECs, community boards, and every elected official in the guide.
Writes 'glance' on each profile in orgs-profiles.json (and puts it first in the profile's intro, for the apps) and
profiles/glance.json (site path -> rows), which assets/site-bar.js shows at the top of the page. Rerunnable."""
import json, os, re, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
import directory_grid as G
src = open(P('data/guide/what-it-does-2026-11-16.md'), encoding='utf-8').read()
def cells(l): return [re.sub(r'\\([\[\]])', r'\1', c.strip()) for c in l.strip().strip('|').split('|')]
S = {}; sec = None
for l in src.split('\n'):
    if l.startswith('#'): sec = l.strip('# *'); S[sec] = []
    elif l.startswith('| ') and not l.startswith('| :') and sec:
        c = cells(l)
        if any(c): S[sec].append(c)
S = {k: v[1:] for k, v in S.items() if v}
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8')); PR = D['profiles']
OFF = {o['slug']: o for o in json.load(open(P('app/data/civic/officials.json'), encoding='utf-8'))}
LABELS = ['What this agency does', 'What it does', 'You may need to know this if', 'Neighborhoods', 'Community council meets',
          'Council meets', 'Full board meets', 'Chairs', 'Committees', 'Community boards', 'Elected by']
G_ = {}
def put(p, rows, title):
    rows = [[a, b] for a, b in rows if b]
    if p and rows: G_[p['slug']] = (title, rows)
norm = lambda s: re.sub(r'[^a-z0-9]+', ' ', re.sub(r'\(.*?\)', '', s.lower()).replace('&', 'and')).replace(' nyc ', ' ').strip()
def strip_city(s): return re.sub(r'^(nyc|new york city|the|city of new york)\s+', '', s).strip()
city = [p for p in PR if p.get('group') == 'Government agencies' and not p['slug'].startswith('nys-')]
byname = collections.defaultdict(list)
for p in city: byname[strip_city(norm(p['name']))].append(p)
CBG = None
ALIAS = {'department of housing preservation and development': 'housing preservation and development', 'department of parks and recreation': 'parks',
         'fire department pension fund': 'fire department pension fund and related funds', 'queens county public administrator': 'public administrator of queens county',
         'bronx borough president': 'office of the borough president of the bronx', 'brooklyn borough president': 'office of the borough president of brooklyn',
         'manhattan borough president': 'office of the borough president of manhattan', 'queens borough president': 'office of the borough president of queens',
         'staten island borough president': 'office of the borough president of staten island'}
miss = []
for k in [k for k in S if k.startswith('City agencies')]:
    for r in S[k]:
        name, does, need = r[0], r[1], r[2]
        ab = (re.search(r'\(([^)]+)\)\s*$', name) or [None, ''])[1]
        cand = byname.get(strip_city(norm(name)), []) or byname.get(ALIAS.get(strip_city(norm(name)), '-'), [])
        if name.startswith('Community Boards (CB)'): CBG = r; continue
        if not cand and name.startswith('Brooklyn Public Library'): cand = [p for p in PR if p['slug'] == 'brooklyn-public-library-cb6']
        if not cand and ab:
            cand = [p for p in city if p['slug'] == ab.lower() or (p.get('seat') or '').endswith('· ' + ab)]
        if not cand: miss.append(name); continue
        for p in cand: put(p, [['What this agency does', does], ['You may need to know this if', need]], 'What it does')
# precincts and precinct community councils
for k in [k for k in S if k.endswith('precincts')]:
    for r in S[k]:
        n = {'Midtown South': '14', 'Midtown North': '18', 'Central Park': '22'}.get(r[0]) or re.match(r'(\d+)', r[0]).group(1)
        rows = [['Neighborhoods', r[1]], ['Community council meets', r[2]]]
        for p in PR:
            if re.match(r'^(%s(st|nd|rd|th)-precinct|nypd-%s(st|nd|rd|th)?-precinct|(cbo-)?%s(st|nd|rd|th)?-(police-)?precinct-community-council(-board)?)$' % (n, n, n), p['slug']):
                put(p, rows, r[0] if not r[0][0].isdigit() else 'The %s Precinct' % r[0])
# school districts and CECs
gen = {r[0]: r for r in S.get('School districts and Community Education Councils', [])}
sd, cecg = gen.get('Community school district (32 of them)'), gen.get('Community Education Council (one per district)')
meets = {re.sub(r'\D', '', r[0]): r[2] for r in S.get('When each council meets', []) if r[0].startswith('CEC')}
for p in PR:
    m = re.match(r'^school-district-(\d+)$', p['slug'])
    if m and sd: put(p, [['What it does', sd[1]], ['You may need to know this if', sd[2]]], 'What it does')
    m = re.match(r'^cec-district-(\d+)$', p['slug'])
    if m and cecg:
        mt = meets.get(m.group(1), '')
        put(p, [['What it does', cecg[1]], ['You may need to know this if', cecg[2]]] + ([['Council meets', mt]] if mt and not mt.startswith('No schedule') else []), 'What it does')
for nm in ('Citywide Council on High Schools', 'Citywide Council on Special Education', 'Citywide Council on English Language Learners', 'Citywide Council for District 75'):
    r = next((x for x in gen.values() if x[0].startswith(nm)), None)
    p = next((x for x in PR if norm(x['name']) == norm(nm)), None)
    if r and p: put(p, [['What it does', r[1]], ['You may need to know this if', r[2]]], 'What it does')
# elected officials
byoff = collections.defaultdict(list)
for p in PR:
    if p.get('kind') == 'official' and p.get('official') in OFF: byoff[p['official']].append(p)
def offs(ch, d): return [p for s, o in OFF.items() if o.get('chamber') == ch and str(o.get('district')) == str(d) for p in byoff.get(s, [])]
for r in S.get('City Council members', []): [put(p, [['Neighborhoods', r[3]], ['Chairs', r[4]]], 'Council District %s' % r[0]) for p in offs('council', r[0])]
for r in S.get('U.S. House members', []): [put(p, [['Community boards', r[2]], ['Committees', r[3]]], 'Congressional District NY-%s' % r[0]) for p in offs('congress', r[0])]
for r in S.get('State Senators', []): [put(p, [['Community boards', r[2]], ['Chairs', r[3]]], 'State Senate District %s' % r[0]) for p in offs('senate', r[0])]
for r in S.get('State Assembly members', []): [put(p, [['Community boards', r[2]], ['Chairs', r[3]]], 'Assembly District %s' % r[0]) for p in offs('assembly', r[0])]
for r in S.get('Citywide, borough, statewide and U.S. Senate', []):
    for s, o in OFF.items():
        if not o.get('chamber') and norm(o.get('name', '')) == norm(r[1]):
            for p in byoff.get(s, []): put(p, [['Elected by', r[2]]], r[0])
# community boards
BN = {'Bronx': 2, 'Brooklyn': 3, 'Manhattan': 1, 'Queens': 4, 'Staten Island': 5}
for r in S.get('Community boards', []):
    m = re.match(r'(Bronx|Brooklyn|Manhattan|Queens|Staten Island) (\d+)', r[0])
    if not m: continue
    cd = str(BN[m.group(1)] * 100 + int(m.group(2)))
    for p in PR:
        if p.get('group') == 'Community boards' and str(p.get('cd')) == cd: put(p, ([['What it does', CBG[1]], ['You may need to know this if', CBG[2]]] if CBG else []) + [['Neighborhoods', r[1]], ['Full board meets', r[2]]], r[0])
# write: profiles (glance, and first in intro for the apps), and the site's path map
BOARDS = {b['borocd']: b for b in json.load(open(P('app/data/civic/boards.json'), encoding='utf-8'))}
site = {}
for p in PR:
    p['intro'] = [x for x in p.get('intro', []) if not any(x.startswith(l + ': ') for l in LABELS)]
    p.pop('glance', None)
    if p['slug'] not in G_: continue
    t, rows = G_[p['slug']]
    p['glance'] = rows
    p['intro'] = ['%s: %s' % (a, b) for a, b in rows] + p['intro']
    if p.get('kind') == 'official' and p.get('official') in OFF: paths = ['/%s/' % p['official']]
    elif p.get('group') == 'Community boards' and str(p.get('cd')) in BOARDS: paths = ['/%s.html' % BOARDS[str(p['cd'])]['slug']]
    else: paths = [G.site_page(p) or '']
    if p['slug'] == 'brooklyn-community-board-6': paths += ['/cb-bk-6.html']
    for u in paths:
        if u and not u.startswith('http'): site[u] = rows
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
json.dump(site, open(P('profiles/glance.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('profiles with the guide at the top:', len(G_), '| site pages:', len(site))
print('guide agencies with no profile:', len(miss), miss)
print(collections.Counter(t if not re.match(r'(The \d|Council District|State Senate|Assembly District|Congressional|Brooklyn \d|Bronx \d|Manhattan \d|Queens \d|Staten Island \d)', t) else re.match(r'(The \d+\w* Precinct|Council District|State Senate|Assembly District|Congressional|Brooklyn|Bronx|Manhattan|Queens|Staten Island)', t).group(1)[:12] for t, r in G_.values()).most_common(20))
