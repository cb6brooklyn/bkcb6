#!/usr/bin/env python3
"""Every NYC Parks property with something to play (courts, fields, tracks, pools, dog runs, skate parks) in the apps'
Directory, each with its profile, so the Directory can be browsed by activity: Tennis, then a borough, then a
neighborhood. From data/nyc-recreation.json (the data behind bkcb6.app/parks.html: one row per court or field, with
its park, activity codes, spot, borough and community district). A park already in the Directory under the same
name keeps its profile and gains the activities ("acts"). Rerunnable: its own entries (slug park-...) are replaced.
Run before app_directory_tiles.py."""
import json, os, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
ACT = {'BKB': 'Basketball', 'HDB': 'Handball', 'TNS': 'Tennis', 'PKB': 'Pickleball', 'VLB': 'Volleyball', 'BOC': 'Bocce', 'HKY': 'Hockey',
       'BSB': 'Baseball', 'SFB': 'Softball', 'SCR': 'Soccer', 'FTB': 'Football', 'CRK': 'Cricket', 'RGB': 'Rugby', 'LAX': 'Lacrosse',
       'KCK': 'Kickball', 'NET': 'Netball', 'FRS': 'Frisbee', 'TRK': 'Running track', 'MPP': 'Multi-purpose play', 'SWM': 'Lap swimming',
       'WAD': 'Wading pool', 'SKT': 'Skateboarding', 'DOG': 'Dog run'}
BORO = {'B': 'Brooklyn', 'Q': 'Queens', 'M': 'Manhattan', 'X': 'Bronx', 'R': 'Staten Island'}
BCD = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
sl = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('park-')]
for p in D['profiles']: p.pop('acts', None)
byname = {}
for p in D['profiles']:
    if p.get('group') in ('Schools, parks and facilities', 'Culture'): byname.setdefault(p['name'].lower().strip(), p)
parks = collections.OrderedDict()
for r in json.load(open(P('data/nyc-recreation.json'))):
    k = r.get('g') or r['n']
    q = parks.setdefault(k, {'n': r['n'], 'g': r.get('g', ''), 'b': r.get('b'), 'c': r.get('c', ''), 'ad': r.get('ad', ''), 'pts': [], 'acts': collections.Counter()})
    q['pts'].append((r['y'], r['x']))
    for a in r['a']:
        if a in ACT: q['acts'][a] += 1
    if not q['ad'] and r.get('ad'): q['ad'] = r['ad']
made = shared = 0
used = set()
for k, q in parks.items():
    if not q['acts']: continue
    acts = [a for a, _ in q['acts'].most_common()]
    have = byname.get(q['n'].lower().strip())
    if have and str(have.get('cd') or q['c']) == str(q['c'] or have.get('cd')):
        have['acts'] = sorted(set(have.get('acts', [])) | set(acts)); shared += 1; continue
    boro = BORO.get(q['b']) or BCD.get(str(q['c'])[:1], '')
    lat = sum(y for y, _ in q['pts']) / len(q['pts']); lng = sum(x for _, x in q['pts']) / len(q['pts'])
    slug = 'park-' + sl(q['g'] or q['n'])
    if slug in used: slug += '-' + sl(q['n'])
    used.add(slug)
    what = ['%s (%d)' % (ACT[a], n) if n > 1 else ACT[a] for a, n in q['acts'].most_common()]
    cdn = int(str(q['c'])[1:]) if str(q['c']).isdigit() and len(str(q['c'])) == 3 and 0 < int(str(q['c'])[1:]) <= 18 else 0
    board = '%s Community Board %d' % (boro, cdn) if cdn and boro else ''
    intro = ['%s is an NYC Parks property in %s.' % (q['n'], boro) if boro else '%s is an NYC Parks property.' % q['n'],
             'What you can do here: %s.' % ', '.join(what)]
    kv = ([['Address', q['ad'].title() if q['ad'].isupper() else q['ad']]] if q['ad'] else []) + ([['Borough', boro]] if boro else []) + \
         ([['Community board', board]] if board else []) + [['Courts, fields and more', ', '.join(what)]]
    D['profiles'].append({'slug': slug, 'type': 'park', 'kind': 'org', 'official': '', 'name': q['n'], 'seat': 'NYC Parks · ' + (boro or 'New York City'),
        'desc': ' '.join(intro), 'lat': round(lat, 6), 'lng': round(lng, 6), 'addr': q['ad'].title() if q['ad'].isupper() else q['ad'], 'zip': '', 'addr_note': '',
        'phone': '', 'email': '', 'web': '', 'weburl': '', 'since': '', 'intro': intro, 'does': [], 'kv': kv,
        'links': [['Courts and fields on bkcb6.app', 'https://bkcb6.app/parks.html']], 'logo': '', 'cal': '', 'n': 0, 'going': [],
        'group': 'Parks', 'topic': 'Parks', 'sort': 0, 'where': boro, 'cd': str(q['c'] or ''), 'kvdest': {}, 'scope': '', 'acts': acts})
    made += 1
if not any(g['name'] == 'Parks' for g in D['groups']): D['groups'].append({'name': 'Parks', 'topics': ['Parks']})
json.dump({a: ACT[a] for a in ACT}, open(P('data/park-activities.json'), 'w'), indent=1)
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('park profiles made:', made, '| already in the Directory, activities added:', shared)
