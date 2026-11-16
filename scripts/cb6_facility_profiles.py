#!/usr/bin/env python3
"""BKCB6: the community-facing places and programs in the city's Facilities Database (DCP FacDB, ji82-xba5, cd 306;
data/cb6-audit/facdb-all.json) that the Directory did not have: senior centers, NYCHA community centers, food
pantries, compost and textile drop-off sites, day camps, after-school and youth programs, organizations with
City Council funding, community services and State and National Register historic places.
Left out: infrastructure with nothing for the public (rail yards, substations, pumping stations, agency storage and
garages, bus depots, marine terminals, bridge houses), summer meal sites, garages (already in from DCWP licenses), and the Department of Cultural Affairs list of cultural
organizations, which carries organizations that have closed and cannot be checked from the record.
Records of one organization at one address make one profile listing each program. Slugs fac-...; rerunnable.
Run after cb6_register_profiles.py and before app_directory_tiles.py."""
import json, os, re, sys, hashlib, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
import cb6_audit as A, directory_dedupe as dd
from cb6_register_profiles_lib import tc, addr_tc
TOPIC = {'SENIOR SERVICES': 'Senior centers and services', 'COMMUNITY CENTERS AND COMMUNITY PROGRAMS': 'NYCHA community centers', 'SOUP KITCHENS AND FOOD PANTRIES': 'Food pantries',
         'DSNY DROP-OFF FACILITY': 'Compost and textile drop-off sites', 'SOLID WASTE PROCESSING': 'Compost and textile drop-off sites', 'CAMPS': 'Day camps',
         'AFTER-SCHOOL PROGRAMS': 'After-school and youth programs', 'YOUTH CENTERS, LITERACY PROGRAMS, AND JOB TRAINING SERVICES': 'After-school and youth programs',
         'HISTORICAL SITES': 'Historic places',
         'LEGAL AND INTERVENTION SERVICES': 'Community services', 'ADULT AND IMMIGRANT LITERACY': 'Community services', 'MENTAL HEALTH': 'Community services',
         'OTHER HEALTH CARE': 'Community services', 'NON-RESIDENTIAL HOUSING AND HOMELESS SERVICES': 'Community services', 'OTHER EMERGENCY SERVICES': 'Community services'}
DS = {'dcla_culturalinstitutions': 'NYC Department of Cultural Affairs', 'moeo_socialservicesitelocations': "Mayor's Office for Economic Opportunity social service sites", 'dfta_contracts': 'NYC Aging contracts',
      'nycha_communitycenters': 'NYCHA community centers', 'foodbankny_foodbanks': 'Food Bank For New York City', 'dsny_donatenycdirectory': 'DSNY donateNYC', 'dsny_fooddrop': 'DSNY food scrap drop-off sites',
      'dsny_leafdrop': 'DSNY leaf drop-off sites', 'dohmh_daycare': 'NYC Health Department permits', 'dycd_service_sites': 'DYCD service sites', 'nysparks_historicplaces': 'State and National Registers of Historic Places',
      'nysed_activeinstitutions': 'NYS Education Department', 'nysdec_solidwaste': 'NYS DEC', 'dcp_colp': 'City Owned and Leased Properties'}
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('fac-')]
F = [x for x in json.load(open(P('data/cb6-audit/facdb-all.json'))) if x.get('facsubgrp') in TOPIC and x.get('latitude')]
F = [x for x in F if x.get('factype') != 'SUPPORTED SRO-OMH']
R = [{'id': x['uid'], 'name': x['facname'], 'alt': x.get('opname', ''), 'addr': x.get('address', ''), 'zip': x.get('zipcode', ''), 'lat': float(x['latitude']), 'lng': float(x['longitude']), 'x': x} for x in F]
got, miss = A.match(R, D['profiles'])
def clean(n):
    n = re.sub(r'\s*:\s*.*$', '', n); n = re.sub(r'\s+-\s+(PRE-TEEN|TEEN|ELEMENTARY).*$', '', n, flags=re.I)
    n = re.sub(r'^(.*), (.*)$', lambda m: '%s %s' % (m.group(2), m.group(1)) if m.group(2).isupper() and len(m.group(2).split()) <= 2 and TOPIC.get('HISTORICAL SITES') and False else m.group(0), n)
    return tc(n)
def fix(n): return re.sub(r'\bEms\b', 'EMS', re.sub(r'\bAeh\b', 'AEH', re.sub(r'\(Ind\)', '(IND)', _fix(n))))
def _fix(n): return re.sub(r'\bYmca\b', 'YMCA', re.sub(r'\bNycha\b', 'NYCHA', re.sub(r'\bSonyc\b', 'SONYC', re.sub(r'\bDsny\b', 'DSNY', n))))
cl = collections.OrderedDict()
for r in miss:
    k = (A.nn(clean(r['name'])), dd._ak({'addr': r['addr']}) or (round(r['lat'], 4), round(r['lng'], 4)))
    cl.setdefault(k, []).append(r)
made = collections.Counter(); new = []
for rows in cl.values():
    x0 = rows[0]['x']; t = TOPIC[x0['facsubgrp']]; name = clean(rows[0]['name'])
    if all(r['x'].get('factype') == 'CITY COUNCIL AWARDS' for r in rows): t = 'Community organizations'
    name = fix(name)
    if t == 'NYCHA community centers': name = '%s Houses Community Center' % name
    if t == 'Historic places':
        m = re.match(r'^([^,]+), ([^,]+), (House|Building)$', name)
        if m: name = '%s %s %s' % (m.group(2), m.group(1), m.group(3))
    addr = re.sub(r'\b(\d+)([a-z])\b', lambda m: m.group(1) + m.group(2).upper(), addr_tc(re.sub(r',\s*BROOKLYN.*$', '', rows[0]['addr'], flags=re.I))); zip_ = rows[0]['zip']
    progs = []
    for r in rows:
        ft = fix(tc(r['x'].get('factype') or '')).replace('City Council Awards', 'City Council discretionary funding')
        if ft and ft not in progs: progs.append(ft)
    srcs = sorted({DS.get(r['x'].get('datasource'), 'NYC Facilities Database') for r in rows})
    what = {'Senior centers and services': 'serves older adults', 'NYCHA community centers': 'is a NYCHA community center', 'Food pantries': 'is a food pantry',
            'Compost and textile drop-off sites': 'is a drop-off site', 'Day camps': 'is a day camp', 'After-school and youth programs': 'runs youth programs',
            'Arts and cultural organizations': 'is an arts and cultural organization', 'Historic places': 'is on the State and National Registers of Historic Places',
            'Community services': 'provides community services', 'Community organizations': 'is a community organization'}[t]
    intro = ['%s %s%s in Brooklyn Community District 6.' % (name, what, ' at ' + addr if addr else '')]
    kv = [['Category', t]] + ([['Programs', '; '.join(progs)]] if progs and t != 'Historic places' else []) + ([['Address', '%s, Brooklyn %s' % (addr, zip_)]] if addr else []) \
         + ([['Run by', tc(x0['opname'])]] if x0.get('opname') and A.nn(x0['opname']) != A.nn(rows[0]['name']) and x0['opname'] != 'Non-public' else []) \
         + [['Community board', 'Brooklyn Community Board 6'], ['Source', 'NYC Facilities Database (%s)' % '; '.join(srcs)]]
    slug = 'fac-' + hashlib.md5('|'.join(sorted(r['id'] for r in rows)).encode()).hexdigest()[:10]
    p = {'slug': slug, 'type': slug, 'kind': 'org', 'official': '', 'name': name, 'seat': '%s · Brooklyn' % t, 'desc': intro[0], 'lat': rows[0]['lat'], 'lng': rows[0]['lng'], 'addr': addr, 'zip': zip_,
         'addr_note': '', 'phone': '', 'email': '', 'web': '', 'weburl': '', 'since': '', 'intro': intro, 'does': [], 'kv': kv, 'links': [], 'logo': '', 'cal': None, 'n': 0, 'going': [],
         'group': 'Schools, parks and facilities', 'topic': t, 'sort': 0, 'facdb': sorted(r['id'] for r in rows)}
    new.append(p); made[t] += 1
D['profiles'] += new
G = next((g for g in D['groups'] if g['name'] == 'Schools, parks and facilities'), None)
if G:
    for t in list(dict.fromkeys(TOPIC.values())) + ['Community organizations']:
        if t not in G['topics'] and made.get(t): G['topics'].append(t)
import importlib.util as _iu
_sp = _iu.spec_from_file_location('bsp', P('scripts/biz_site_profiles.py')); BSP = _iu.module_from_spec(_sp); _sp.loader.exec_module(BSP)
os.chdir(ROOT)
OLD_F = P('data/cb6-audit/fac-pages.json'); OLD = json.load(open(OLD_F)) if os.path.exists(OLD_F) else {}
for u in OLD.values():
    if os.path.exists(u[1:]): os.remove(u[1:])
pages = {}
for p in new:
    s_ = BSP.slugify(p['name'] + ' ' + (p.get('addr') or '')); k_ = 2; base = s_
    while os.path.exists('biz/%s.html' % s_) or '/biz/%s.html' % s_ in pages.values(): s_ = '%s-%d' % (base, k_); k_ += 1
    path = '/biz/%s.html' % s_; open(path[1:], 'w').write(BSP.page(p, None, path)); pages[p['slug']] = path
    p['links'] = [['Profile and map', 'https://bkcb6.app' + path]]
json.dump(pages, open(OLD_F, 'w'), indent=0)
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('facility records considered:', len(R), '| already in the Directory:', len(got), '| profiles made:', sum(made.values()), dict(made))
