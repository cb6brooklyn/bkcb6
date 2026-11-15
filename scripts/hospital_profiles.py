#!/usr/bin/env python3
"""Every hospital in the city in the apps' and the site's Directory, each with its profile. From Mike's hospitals list
(data/directory-sources/hospitals.tsv: NYS DOH facility id, name, health system) and the NYS Department of Health
facility file (hospitals-doh.json: address, phone, spot). A hospital already in the Directory under the same name keeps
its profile and is listed under Hospitals too. Logos: the health system's, from assets/health-system-logos/<system>.png
when it is there. Rerunnable: its own entries (slug hosp-...) are replaced. Run before app_directory_tiles.py."""
import json, os, re, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
SYS = {'hh': ('NYC Health + Hospitals', 'https://www.nychealthandhospitals.org/'), 'msk': ('Memorial Sloan Kettering', 'https://www.mskcc.org/'),
       'hss': ('Hospital for Special Surgery', 'https://www.hss.edu/'), 'northwell': ('Northwell Health', 'https://www.northwell.edu/'),
       'sinai': ('Mount Sinai Health System', 'https://www.mountsinai.org/'), 'nyp': ('NewYork-Presbyterian', 'https://www.nyp.org/'),
       'nyu': ('NYU Langone Health', 'https://nyulangone.org/'), 'bronxcare': ('BronxCare Health System', 'https://www.bronxcare.org/'),
       'calvary': ('Calvary Hospital', 'https://www.calvaryhospital.org/'), 'montefiore': ('Montefiore Einstein', 'https://montefioreeinstein.org/'),
       'sbh': ('SBH Health System', 'https://www.sbhny.org/'), 'obh': ('One Brooklyn Health', 'https://onebrooklynhealth.org/'),
       'tbh': ('The Brooklyn Hospital Center', 'https://www.tbh.org/'), 'maimo': ('Maimonides Health', 'https://maimo.org/'),
       'downstate': ('SUNY Downstate Health Sciences University', 'https://www.downstate.edu/'), 'wyckoff': ('Wyckoff Heights Medical Center', 'https://whmcny.org/'),
       'flushing': ('Flushing Hospital Medical Center', 'https://flushinghospital.org/'), 'jamaica': ('Jamaica Hospital Medical Center', 'https://jamaicahospital.org/'),
       'ehs': ('Episcopal Health Services', 'https://ehs.org/'), 'rumc': ('Richmond University Medical Center', 'https://rumcsi.org/')}
# logos the repo already has, until the health system's own file is in assets/health-system-logos/
HAVE = {'hh': 'app/data/civic/orgs/logos/agency-h-plus-h.png', 'nyp': 'app/data/civic/orgs/logos/nyp.png', 'tbh': 'site-icons/brooklyn-hospital-center.png',
        'nyu': 'app/data/civic/orgs/logos/health-nyu-langone-hospital-joseph-s-and-diane-h-steinberg-ambulatory-care-center.png'}
BORO = [(21, 'Manhattan'), (33, 'Bronx'), (49, 'Brooklyn'), (58, 'Queens'), (62, 'Staten Island')]
doh = {}
for r in json.load(open(P('data/directory-sources/hospitals-doh.json'))):
    if r['fac_id'] not in doh or (r.get('latitude') and not doh[r['fac_id']].get('latitude')): doh[r['fac_id']] = r
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('hosp-')]
for p in D['profiles']:
    for k in ('hospital', 'hospital_where'): p.pop(k, None)
byname = {p['name'].lower().strip(): p for p in D['profiles'] if p.get('group') in ('Schools, parks and facilities',)}
made = shared = nologo = 0
for i, line in enumerate(open(P('data/directory-sources/hospitals.tsv'), encoding='utf-8').read().strip().split('\n')):
    fid, name, sk = line.split('\t')
    boro = next(b for n, b in BORO if i < n)
    have = byname.get(name.lower())
    if have: have.update({'hospital': 'Hospitals', 'hospital_where': boro}); shared += 1; continue
    r = doh.get(fid, {}); sysname, web = SYS[sk]
    addr = ', '.join(x for x in (r.get('address1', '').strip(), r.get('city', '').strip()) if x) + (' ' + r['fac_zip'] if r.get('fac_zip') else '')
    src = next((s for s in ('assets/health-system-logos/%s.png' % sk, HAVE.get(sk)) if s and os.path.exists(P(s))), None)
    logo = ''
    if src:
        logo = 'hosp-%s.png' % sk; shutil.copyfile(P(src), P('app/data/civic/orgs/logos', logo))
    else: nologo += 1
    ph = re.sub(r'\D', '', r.get('fac_phone', ''))
    phone = '(%s) %s-%s' % (ph[:3], ph[3:6], ph[6:]) if len(ph) == 10 else ''
    intro = ['%s is a hospital at %s.' % (name, addr) if addr else '%s is a hospital in %s.' % (name, boro)]
    if sysname != name: intro.append('It is part of %s.' % sysname)
    kv = ([['Address', addr]] if addr else []) + [['Borough', boro], ['Health system', sysname]] + ([['Phone', phone]] if phone else [])
    D['profiles'].append({'slug': 'hosp-' + fid, 'type': 'hospital', 'kind': 'org', 'official': '', 'name': name, 'seat': 'Hospital · ' + boro,
        'desc': ' '.join(intro), 'lat': float(r['latitude']) if r.get('latitude') else None, 'lng': float(r['longitude']) if r.get('longitude') else None,
        'addr': addr, 'zip': r.get('fac_zip', ''), 'addr_note': '', 'phone': phone, 'email': '', 'web': re.sub(r'^https?://(www\.)?', '', web).rstrip('/'), 'weburl': web,
        'since': '', 'intro': intro, 'does': [], 'kv': kv, 'links': [['Its website', web]], 'logo': logo, 'cal': '', 'n': 0, 'going': [],
        'group': 'Health', 'topic': 'Hospitals', 'sort': 0, 'where': boro, 'cd': '', 'kvdest': {}, 'scope': ''})
    made += 1
if not any(g['name'] == 'Health' for g in D['groups']): D['groups'].append({'name': 'Health', 'topics': ['Hospitals']})
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('hospital profiles made:', made, '| already in the Directory:', shared, '| waiting on a health system logo:', nologo)
