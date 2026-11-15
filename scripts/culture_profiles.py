#!/usr/bin/env python3
"""Broadway theatres, museums, movie theaters and stadiums in the apps' Directory, each with its profile.
From data/culture-places.json (the site's culture places: name, address, borough, community board, logo, the site's
/c/ page) and stadiums_final.json (the stadium pages). A place that already has a Directory profile under the same
name keeps it and is listed under Culture too (its "culture" field). Logos: the theatre's Playbill cover, the place's
own logo, assets/stadium-logos/<stadium>.png. Rerunnable: its own entries (slug cul-...) are replaced.
Run after board_profiles.py, then app_directory_tiles.py."""
import json, os, re, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sl = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('cul-')]
for p in D['profiles']:
    for k in ('culture', 'culture_where', 'culture_cd'): p.pop(k, None)
byname = {}
for p in D['profiles']: byname.setdefault(p['name'].lower().strip(), p)
LOGOS = P('app/data/civic/orgs/logos')
TOPIC = {'theatre': 'Broadway theatres', 'museum': 'Museums', 'film': 'Movie theaters'}
KIND = {'theatre': 'a Broadway theatre', 'museum': 'a museum', 'film': 'a movie theater'}
BORO = {'MN': 'Manhattan', 'BX': 'Bronx', 'BK': 'Brooklyn', 'QN': 'Queens', 'SI': 'Staten Island'}
BN = {'BKCB': 'Brooklyn', 'MNCB': 'Manhattan', 'BXCB': 'Bronx', 'QNCB': 'Queens', 'SICB': 'Staten Island'}
def board_name(cb):
    m = re.match(r'^(BKCB|MNCB|BXCB|QNCB|SICB)(\d+)$', cb or '')
    return '%s Community Board %s' % (BN[m.group(1)], m.group(2)) if m else ''
def logo_for(slug, srcs):
    for s in srcs:
        if s and os.path.exists(P(s.lstrip('/'))):
            out = 'cul-%s.png' % slug
            shutil.copyfile(P(s.lstrip('/')), os.path.join(LOGOS, out)); return out
    return ''
def entry(slug, name, topic, where, lat, lng, addr, intro, kv, links, logo, cd):
    return {'slug': 'cul-' + slug, 'type': 'culture', 'kind': 'org', 'official': '', 'name': name, 'seat': topic[:-1] + ' · ' + where if topic != 'Stadiums and arenas' else 'Stadium · ' + where,
            'desc': intro[0], 'lat': lat, 'lng': lng, 'addr': addr, 'zip': '', 'addr_note': '', 'phone': '', 'email': '', 'web': '', 'weburl': '',
            'since': '', 'intro': intro, 'does': [], 'kv': kv, 'links': links, 'logo': logo, 'cal': '', 'n': 0, 'going': [],
            'group': 'Culture', 'topic': topic, 'sort': 0, 'where': where, 'cd': cd, 'kvdest': {}, 'scope': ''}
made = shared = 0
for x in json.load(open(P('data/culture-places.json'))):
    t = x.get('type')
    if t not in TOPIC: continue
    topic, where = TOPIC[t], x.get('boro_name') or BORO.get(x.get('boro'), '')
    have = byname.get(x['name'].lower().strip())
    if have:
        have.update({'culture': topic, 'culture_where': where, 'culture_cd': str(x.get('cd') or '')}); shared += 1; continue
    s = sl(x['name'])
    logo = logo_for(s, (['/site-icons/playbill-%s.png' % s] if t == 'theatre' else []) + [x.get('logo_sq'), x.get('logo')])
    addr = x.get('address', '')
    intro = ['%s is %s at %s.' % (x['name'], KIND[t], addr) if addr else '%s is %s in %s.' % (x['name'], KIND[t], where)]
    if x.get('year_built'): intro.append('Its building dates from %s.' % x['year_built'])
    kv = [['Address', addr]] if addr else []
    kv += [['Borough', where]] + ([['Community board', board_name(x.get('cb'))]] if board_name(x.get('cb')) else [])
    if x.get('year_built'): kv.append(['Built', str(x['year_built'])])
    if x.get('zoning'): kv.append(['Zoning', x['zoning']])
    if x.get('tel'): kv.append(['Phone', x['tel']])
    links = ([['Its website', x['url']]] if x.get('url') else []) + ([['Its page on bkcb6.app', 'https://bkcb6.app' + x['profile']]] if x.get('profile') else [])
    cd = ''
    if x.get('cd'): cd = str(x['cd'])
    D['profiles'].append(entry(s, x['name'], topic, where, x.get('lat'), x.get('lng'), addr, intro, kv, links, logo, cd))
    made += 1
for x in json.load(open(P('stadiums_final.json'))):
    s = x['slug'][len('stadium-'):]
    have = byname.get(x['name'].lower().strip())
    if have: have.update({'culture': 'Stadiums and arenas', 'culture_where': x['boro'], 'culture_cd': ''}); shared += 1; continue
    logo = logo_for(s, ['assets/stadium-logos/%s.png' % s])
    teams = x.get('teams') or []
    intro = ['%s is a stadium at %s.' % (x['name'], x['addr'])]
    if teams: intro.append('Home of the %s.' % (', '.join(teams[:-1]) + ' and ' + teams[-1] if len(teams) > 1 else teams[0]))
    kv = [['Address', x['addr']], ['Borough', x['boro']]] + ([['Community board', x['board']]] if x.get('board') else []) + ([['Zoning', x['zoning']]] if x.get('zoning') else [])
    if teams: kv.append(['Home of', ', '.join(teams)])
    links = [['Its page on bkcb6.app', 'https://bkcb6.app/' + x['slug']]]
    D['profiles'].append(entry(s, x['name'], 'Stadiums and arenas', x['boro'], x.get('lat'), x.get('lng'), x['addr'], intro, kv, links, logo, ''))
    made += 1
if not any(g['name'] == 'Culture' for g in D['groups']):
    D['groups'].append({'name': 'Culture', 'topics': ['Broadway theatres', 'Stadiums and arenas', 'Museums', 'Movie theaters']})
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('culture profiles made:', made, '| already in the Directory, listed under Culture too:', shared)
