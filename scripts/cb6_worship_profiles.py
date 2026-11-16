#!/usr/bin/env python3
"""BKCB6 houses of worship. Every Directory profile that is one (worship.py) is filed under "Houses of worship".
The district's religious buildings (PLUTO building class M1 church/synagogue and M9 other religious, cd 306;
data/cb6-audit/worship-lots.json) were each checked for a house of worship listed within 70 m. Four had none. One was identified by web
search and is added here with its source (slugs worship-...). The others are not added: 38 Prospect Place (owned by the
Seventh-day Adventists' Greater New York Conference; no congregation found there), 141 Dwight Street and 72 Van Dyke Street
(held by LLCs) and 650 Sackett Street (offered for lease as commercial space).
The OpenStreetMap listing for St. Augustine (sasfx.org) had no address; it gets 116 6th Avenue and its phone from Discover Mass. Rerunnable.
Run after cb6_register_profiles.py and cb6_facility_profiles.py, before app_directory_tiles.py."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
import worship as W
from shapely.geometry import shape, Point
POLY = shape(json.load(open(P('data/cb6-audit/cd306.geojson'))))
ADD = [
    {'slug': 'worship-new-brown-memorial-baptist', 'name': 'New Brown Memorial Baptist Church', 'addr': '609 Clinton Street', 'zip': '11231', 'lat': 40.674507, 'lng': -74.00169,
     'nb': 'Red Hook', 'src': ['Red Hook WaterStories', 'https://redhookwaterstories.org/items/show/899'],
     'intro': 'New Brown Memorial Baptist Church is a Baptist church at 609 Clinton Street in Red Hook, founded in 1954 by Rev. Andrew Dennis McBride and his wife Ruth.'},
]
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('worship-')]
for a in ADD:
    D['profiles'].append({'slug': a['slug'], 'type': a['slug'], 'kind': 'org', 'official': '', 'name': a['name'], 'seat': 'House of worship · ' + a['nb'], 'desc': a['intro'],
        'lat': a['lat'], 'lng': a['lng'], 'addr': a['addr'], 'zip': a['zip'], 'addr_note': '', 'phone': a.get('phone', ''), 'email': '', 'weburl': a.get('weburl', ''),
        'web': a.get('weburl', '').replace('https://', ''), 'since': '', 'intro': [a['intro']], 'does': [],
        'kv': [['Category', 'Houses of worship'], ['Address', '%s, Brooklyn %s' % (a['addr'], a['zip'])], ['Community board', 'Brooklyn Community Board 6'], ['Source', a['src'][0]]],
        'links': [[a['src'][0], a['src'][1]]] + ([['Website', a['weburl']]] if a.get('weburl') else []), 'logo': '', 'cal': None, 'n': 0, 'going': [],
        'group': 'Schools, parks and facilities', 'topic': 'Houses of worship', 'sort': 0})
FIX = {'biz-f88aa014bc': {'name': 'St. Augustine Roman Catholic Church', 'addr': '116 6th Avenue', 'zip': '11217', 'phone': '(718) 638-1880',
                          'intro': ['St. Augustine is a Roman Catholic church at 116 6th Avenue in Park Slope, part of the parish of St. Augustine and St. Francis Xavier.'],
                          'src': ['Discover Mass', 'https://discovermass.com/church/st-augustine-brooklyn-ny']}}
for p in D['profiles']:
    x = FIX.get(p['slug'])
    if x:
        p.update({k: v for k, v in x.items() if k != 'src'}); p['desc'] = x['intro'][0]
        p['kv'] = [k for k in p['kv'] if k[0] not in ('Address',)] + [['Address', '%s, Brooklyn %s' % (x['addr'], x['zip'])], ['Address and phone from', x['src'][0]]]
        p['links'] = [l for l in p['links'] if l[0] != x['src'][0]] + [x['src']]
n = 0
for p in D['profiles']:
    if W.is_worship(p):
        p['worship'] = True
        if p['slug'].startswith(('reg-', 'biz-', 'worship-', 'map-')) and p.get('topic') != 'Houses of worship':
            p['topic'] = 'Houses of worship'
            p['kv'] = [['Category', 'Houses of worship'] if k[0] == 'Category' else k for k in p.get('kv', [])]
        if p.get('lat') and p.get('lng') and POLY.contains(Point(p['lng'], p['lat'])): n += 1
    else: p.pop('worship', None)
for g in D['groups']:
    if g['name'] == 'Schools, parks and facilities' and 'Houses of worship' not in g['topics']: g['topics'].append('Houses of worship')
import importlib.util as _iu
_sp = _iu.spec_from_file_location('bsp', P('scripts/biz_site_profiles.py')); BSP = _iu.module_from_spec(_sp); _sp.loader.exec_module(BSP)
os.chdir(ROOT)
for p in D['profiles']:
    if p['slug'].startswith('worship-'):
        path = '/biz/%s.html' % BSP.slugify(p['name'] + ' ' + p['addr'])
        p['links'] = [l for l in p['links'] if l[0] != 'Profile and map'] + [['Profile and map', 'https://bkcb6.app' + path]]
        open(path[1:], 'w').write(BSP.page(p, None, path))
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('houses of worship in BKCB6:', n, '| added from web search:', len(ADD))
