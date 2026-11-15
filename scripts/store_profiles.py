#!/usr/bin/env python3
"""Every pharmacy and supermarket in the city in the apps' and the site's Directory, each with its profile.
From data/directory-sources/pharmacies-supermarkets.json (Mike's logo collection, Nov 15, 2026):
  pharmacies: NYS Medicaid Enrolled Provider Listing (health.data.ny.gov keti-qx5t), PHARMACY, five NYC counties
  supermarkets: NYS Ag & Markets Retail Food Stores (data.ny.gov 9a8c-vfzj), NYC stores of 10,000+ sq ft or named
                as a supermarket chain or "supermarket", "superstore", "fresh market", "food center", "food mart"
Chain stores carry the chain's logo (assets/store-logos/<brand>.png); independents without a logo get the kind tile.
Pharmacies are under Health > Pharmacies, supermarkets under Food > Supermarkets, by borough.
Rerunnable: its own entries (slugs rx-... and mkt-...) are replaced. Run before app_directory_tiles.py."""
import json, os, re, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
KIND = {'pharmacy': ('rx-', 'Health', 'Pharmacies', 'Pharmacy', 'a pharmacy'),
        'supermarket': ('mkt-', 'Food', 'Supermarkets', 'Supermarket', 'a supermarket')}
SRC = {'pharmacy': ['NYS Medicaid Enrolled Provider Listing', 'https://health.data.ny.gov/d/keti-qx5t'],
       'supermarket': ['NYS Ag & Markets Retail Food Stores', 'https://data.ny.gov/d/9a8c-vfzj']}
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith(('rx-', 'mkt-'))]
rows = json.load(open(P('data/directory-sources/pharmacies-supermarkets.json'), encoding='utf-8'))
def street_of(a): return re.sub(r'\s*#+\s*', ' ', a.split(',')[0]).strip()
def clean_addr(a): return re.sub(r'\s+', ' ', re.sub(r'\s*#{2,}\s*', ' ', a)).replace(' ,', ',').strip()
seen = set(); made = dup = withlogo = 0
for r in sorted(rows, key=lambda r: (r['kind'], r['boro'], r['chain'] or r['name'], r['address'])):
    pre, group, topic, label, a_kind = KIND[r['kind']]
    street = street_of(r['address'])
    name = '%s, %s' % (r['chain'], street) if r['chain'] else r['name']
    key = (r['kind'], name.lower(), r['zip'])
    if key in seen: dup += 1; continue     # one tile per store: some stores hold more than one license at one address
    seen.add(key)
    addr = clean_addr(r['address'])
    logo = ''
    if r['logo'] and os.path.exists(P('assets/store-logos', r['logo'] + '.png')):
        logo = '%s%s.png' % (pre, r['logo'])
        dst = P('app/data/civic/orgs/logos', logo)
        if not os.path.exists(dst): shutil.copyfile(P('assets/store-logos', r['logo'] + '.png'), dst)
        withlogo += 1
    ph = re.sub(r'\D', '', r.get('phone') or '')
    phone = '(%s) %s-%s' % (ph[:3], ph[3:6], ph[6:]) if len(ph) == 10 else ''
    intro = ['%s is %s at %s.' % (r['chain'] or r['name'], a_kind, addr)]
    if r['chain'] and r['chain'].lower() not in r['name'].lower(): intro.append('Licensed as %s.' % r['name'])
    kv = [['Address', addr], ['Borough', r['boro']]] + ([['Chain', r['chain']]] if r['chain'] else []) + ([['Phone', phone]] if phone else []) \
         + ([['Size', '{:,} sq ft'.format(int(r['sqft']))]] if r.get('sqft') else []) + [['Source record', r['source']]]
    links = ([['Its website', r['web']]] if r['web'] else []) + [[SRC[r['kind']][0], SRC[r['kind']][1]]]
    D['profiles'].append({'slug': pre + r['id'], 'type': r['kind'], 'kind': 'org', 'official': '', 'name': name, 'seat': '%s · %s' % (label, r['boro']),
        'desc': ' '.join(intro), 'lat': r['lat'], 'lng': r['lng'], 'addr': addr, 'zip': r['zip'], 'addr_note': '', 'phone': phone, 'email': '',
        'web': re.sub(r'^https?://(www\.)?', '', r['web']).rstrip('/') if r['web'] else '', 'weburl': r['web'], 'since': '', 'intro': intro, 'does': [],
        'kv': kv, 'links': links, 'logo': logo, 'cal': '', 'n': 0, 'going': [], 'group': group, 'topic': topic, 'sort': 0, 'where': r['boro'],
        'cd': '', 'kvdest': {}, 'scope': ''})
    made += 1
for g, t in (('Health', 'Pharmacies'), ('Food', 'Supermarkets')):
    G = next((x for x in D['groups'] if x['name'] == g), None)
    if not G: G = {'name': g, 'topics': []}; D['groups'].append(G)
    if t not in G['topics']: G['topics'].append(t)
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('pharmacy and supermarket profiles made:', made, '| with a logo:', withlogo, '| second license at the same store, not repeated:', dup)
