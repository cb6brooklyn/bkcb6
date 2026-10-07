#!/usr/bin/env python3
"""The apps' Organizations tab, Government agencies: every agency in the site's directory (data/agencies.json,
the nyc.gov agency directory feed behind bkcb6.app/agencies) becomes a profile in
app/data/civic/orgs/orgs-profiles.json, with the site's logo (assets/agency-logos) downsized into
app/data/civic/orgs/logos/agency-<slug>.png and its location from data/agency-locations.json.

The twenty hand-written local profiles (CB6, the precincts, the DSNY garage, the DOT/DEP/HPD/Parks/DCP/LPC/
NYCHA/RGB/Council/schools entries) stay as they are; the site's generic entry for the same agency is skipped.
No build: the apps read the file from the pack. Run after editing data/agencies.json or data/agency-locations.json.
"""
import json, os, re
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES = os.path.join(ROOT, 'app/data/civic/orgs/orgs-profiles.json')
LOGOS = os.path.join(ROOT, 'app/data/civic/orgs/logos')
SITE_LOGOS = os.path.join(ROOT, 'assets/agency-logos')

SINGULAR = {'Mayoral Agency': 'Mayoral agency', 'Mayoral Office': 'Mayoral office', 'Elected Office': 'Elected office',
            'Advisory or Regulatory Organization': 'Board or commission', 'Division': 'Division',
            'Public Benefit or Development Organization': 'Public benefit corporation', 'Pension Fund': 'Pension fund',
            'Nonprofit Organization': 'Affiliated nonprofit', 'State Government Agency': 'State agency listed by the city'}
# Site slugs the apps already carry as hand-written local profiles (by the profile's type key) or community groups.
ALREADY = {'cb', 'dsny', 'nyc-dot', 'dep', 'hpd', 'dpr', 'dcp', 'lpc', 'rgb', 'nycha', 'nycc', 'nycps', 'bpl'}
MAX = 256

site = json.load(open(os.path.join(ROOT, 'data/agencies.json')))['agencies']
loc = json.load(open(os.path.join(ROOT, 'data/agency-locations.json')))['agencies']
doc = json.load(open(PROFILES))

kept = [p for p in doc['profiles'] if not p.get('from') == 'agencies.json']
local_max = max([p.get('sort', 0) for p in kept if p.get('kind') == 'agency'] + [0])
os.makedirs(LOGOS, exist_ok=True)

def host(u):
    u = re.sub(r'^https?://(www1?\.)?', '', u or '')
    return re.sub(r'/(index\.page)?$', '', u)

def logo_for(slug):
    src = os.path.join(SITE_LOGOS, slug + '.png')
    if not os.path.exists(src): return ''
    name = 'agency-%s.png' % slug
    im = Image.open(src).convert('RGBA')
    w, h = im.size
    if max(w, h) > MAX:
        s = MAX / max(w, h); im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    im.save(os.path.join(LOGOS, name), optimize=True)
    return name

added = []
for i, a in enumerate(sorted(site, key=lambda x: x['sort'].lower())):
    if a['slug'] in ALREADY: continue
    L = loc.get(a['slug'], {})
    kind_label = SINGULAR.get(a['type'], a['type'])
    seat = kind_label + (' · ' + a['acronym'] if a['acronym'] else '')
    intro = []
    if a.get('desc'): intro.append(a['desc'])
    lead = ''
    if a.get('officer'):
        lead = '%s is led by %s, %s.' % (a['acronym'] or a['name'], a['officer'], a['title']) if a.get('title') else '%s is led by %s.' % (a['acronym'] or a['name'], a['officer'])
    if a.get('reports_to'):
        lead = (lead + ' ' if lead else '') + 'It reports to the %s.' % a['reports_to'].replace(';', ' and the ')
    if lead: intro.append(lead)
    if not intro: intro.append('%s, %s of the City of New York.' % (a['name'], kind_label.lower()))
    kv = [x for x in [['Acronym', a['acronym']], ['Type', kind_label], ['Head', (a['officer'] + (', ' + a['title'] if a.get('title') else '')) if a.get('officer') else ''],
                      ['Reports to', a['reports_to'].replace(';', '; ')]] if x[1]]
    links = [x for x in [['Website', a['url']], ['Contact', a['contact']], ['On bkcb6.app', 'https://bkcb6.app/agencies/%s/' % a['slug']]] if x[1]]
    addr = L.get('addr', '')
    # The apps add ", Brooklyn, NY <zip>" when zip is set, so only Brooklyn addresses carry a zip.
    m = re.match(r'^(.*), Brooklyn, NY (\d{5})$', addr)
    if m: addr, zipc = m.group(1), m.group(2)
    else: zipc = ''
    p = {'slug': a['slug'], 'type': a['slug'], 'kind': 'agency', 'official': '', 'name': a['name'], 'seat': seat,
         'desc': '%s, %s. %s' % (a['name'], seat, a.get('desc') or ''), 'lat': L.get('lat', 0), 'lng': L.get('lng', 0),
         'addr': addr, 'zip': zipc, 'addr_note': L.get('note', ''), 'phone': L.get('phone', ''), 'email': '',
         'web': host(a['url']), 'weburl': a['url'], 'since': '', 'intro': intro, 'does': [], 'kv': kv, 'links': links,
         'logo': logo_for(a['slug']), 'cal': '', 'n': 0, 'going': [], 'group': 'Government agencies', 'topic': '',
         'sort': local_max + 1 + i, 'from': 'agencies.json'}
    added.append(p)

doc['profiles'] = kept + added
doc['about'] = re.sub(r'\s*Government agencies beyond the local ones come from.*$', '', doc['about'].strip())
doc['about'] += (' Government agencies beyond the local ones come from data/agencies.json (the nyc.gov agency directory, as on '
                 'bkcb6.app/agencies) with locations from data/agency-locations.json, written by scripts/build_orgs_agencies.py; '
                 'they carry from: agencies.json and are rewritten each run.')
json.dump(doc, open(PROFILES, 'w'), ensure_ascii=False, indent=1)
print('agencies from the site', len(added), '| profiles now', len(doc['profiles']), '| with logo', sum(1 for p in added if p['logo']),
      '| with address', sum(1 for p in added if p['addr']))
