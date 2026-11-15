#!/usr/bin/env python3
"""All 59 community boards in the apps' Directory, each with its profile (BKCB6's own profile stays as it is).
From app/data/civic/boards.json (name, borough, chair, district manager, website, who represents it) and
board-offices.json (the board office's spot). Each board's seal is app/data/Logos/cb<cd>.png, read through the
profile's logo path. Rerunnable: its own entries (slug cb-<boro>-<n>) are replaced. Then run app_directory_tiles.py."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
B = json.load(open(P('app/data/civic/boards.json')))
OFF = json.load(open(P('app/data/civic/board-offices.json')))['boards']
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not re.match(r'^cb-(bk|bx|mn|qn|si)-\d+$', p['slug'])]
cb6 = next(p for p in D['profiles'] if p['slug'] == 'brooklyn-community-board-6')
cb6.update({'group': 'Community boards', 'topic': 'Brooklyn', 'where': 'Brooklyn', 'cd': '306'})
n = 0
for b in B:
    cd = b['borocd']
    if cd == '306': continue
    ll = OFF.get(cd) or [None, None]
    num = int(cd[1:])
    kv = [['Borough', b['borough']], ['Community district', '%s %d' % (b['borough'], num)]]
    if b.get('chair'): kv.append(['Chair', b['chair']])
    if b.get('dm'): kv.append(['District manager', b['dm']])
    for r in b.get('reps') or []:
        kv.append([r['district'], r['rep']])
    page = 'https://bkcb6.app/%s.html' % b['slug']
    intro = ['%s is the community board for %s Community District %d, one of the 59 community boards of New York City.' % (b['name'], b['borough'], num)]
    who = [x for x in (('its chair is ' + b['chair']) if b.get('chair') else '', ('its district manager is ' + b['dm']) if b.get('dm') else '') if x]
    if who: intro.append(' and '.join(who).capitalize() + '.')
    D['profiles'].append({'slug': b['slug'], 'type': 'board', 'kind': 'agency', 'official': '', 'name': b['name'],
        'seat': 'Community board · ' + b['borough'], 'desc': intro[0], 'lat': ll[0], 'lng': ll[1], 'addr': '', 'zip': '', 'addr_note': '',
        'phone': '', 'email': '', 'web': re.sub(r'^https?://(www\.)?', '', b.get('website') or '').rstrip('/'), 'weburl': b.get('website') or '', 'since': '',
        'intro': intro, 'does': [], 'kv': kv, 'links': [['Its page on bkcb6.app', page]] + ([['Its website', b['website']]] if b.get('website') else []),
        'logo': '../../../Logos/cb%s.png' % cd, 'cal': '', 'n': 0, 'going': [], 'group': 'Community boards', 'topic': b['borough'], 'sort': num,
        'where': b['borough'], 'cd': cd, 'kvdest': {}, 'scope': ' '.join(x for x, ok in (('bk', b['borough'] == 'Brooklyn'),) if ok)})
    n += 1
if not any(g['name'] == 'Community boards' for g in D['groups']):
    D['groups'].insert(0, {'name': 'Community boards', 'topics': ['Manhattan', 'Bronx', 'Brooklyn', 'Queens', 'Staten Island']})
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('community board profiles:', n, '+ BKCB6')
