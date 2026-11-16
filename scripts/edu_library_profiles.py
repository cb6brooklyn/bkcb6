#!/usr/bin/env python3
"""Every library branch in the city (Brooklyn, New York and Queens Public Library) and every child care center and
Pre-K site, each with its profile, for the Directory and its school and child care finder.

  libraries      NYC Open Data feuq-due4 (Library locations)                data/directory-sources/libraries.json
  child care     DOHMH Child Care Centers, permitted (dsg6-ifza)             data/directory-sources/dohmh-childcare.json
                 placed by building (DCP Facilities Database, then Geoclient/GeoSearch: childcare-geo.json)
  Pre-K sites    DCP Facilities Database (ji82-xba5), DOE Universal Pre-K     data/directory-sources/facdb-daycare-prek.json
                 and NYSED preschools for students with disabilities
Pre-K sites that are already a school in the Directory (same name) are not repeated. Slugs lib-, cc-, pk-, swdpre-;
rerunnable (its own entries are replaced). Run before app_directory_tiles.py."""
import json, os, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
SRC = lambda f: json.load(open(P('data/directory-sources', f), encoding='utf-8'))
BORO = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island',
        'MANHATTAN': 'Manhattan', 'BRONX': 'Bronx', 'BROOKLYN': 'Brooklyn', 'QUEENS': 'Queens', 'STATEN ISLAND': 'Staten Island'}
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
SMALL = {'of', 'and', 'the', 'for', 'at', 'in', 'on', 'a', 'de', 'la'}
def tc(s):
    s = re.sub(r'\s+', ' ', (s or '').strip())
    out = []
    for i, w in enumerate(s.split(' ')):
        lw = w.lower()
        if re.fullmatch(r'(ps|is|ms|jhs|hs|pk|upk|llc|inc|ymca|ywca|nyc|ny|cdc|hsa|swd|ii|iii|iv)\.?,?', lw): out.append(w.upper())
        elif i and lw in SMALL: out.append(lw)
        else: out.append(re.sub(r"(^|[-/(])([a-z])", lambda m: m.group(1) + m.group(2).upper(), lw))
    return ' '.join(out).replace("'S ", "'s ").replace("’S ", "’s ")
def phone_of(s):
    d = re.sub(r'\D', '', s or '')
    return '(%s) %s-%s' % (d[:3], d[3:6], d[6:]) if len(d) == 10 else ''
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith(('lib-', 'cc-', 'pk-', 'swdpre-'))]
def add(**k):
    base = {'type': '', 'kind': 'org', 'official': '', 'addr_note': '', 'email': '', 'since': '', 'does': [], 'cal': '', 'n': 0, 'going': [],
            'sort': 0, 'cd': '', 'kvdest': {}, 'scope': '', 'web': '', 'weburl': '', 'phone': ''}
    base.update(k)
    if base['weburl']: base['web'] = re.sub(r'^https?://(www\.)?', '', base['weburl']).rstrip('/')
    D['profiles'].append(base)
made = collections.Counter()

# ---- libraries ----
SYS = {'BPL': ('Brooklyn Public Library', 'bpl.png'), 'NYPL': ('New York Public Library', 'agency-nypl.png'), 'QPL': ('Queens Public Library', 'agency-qpl.png')}
for r in SRC('libraries.json'):
    sysname, logo = SYS[r['system']]
    nm = r['name'].strip()
    name = nm if re.search(r'library', nm, re.I) else nm + ' Library'
    street = ' '.join(x for x in (r.get('housenum', '').strip(), r.get('streetname', '').strip()) if x)
    boro = BORO.get(r.get('borocode', ''), '')
    addr = '%s, %s %s' % (street, r.get('city', '').strip(), r.get('zip', '')) if street else ''
    c = (r.get('the_geom') or {}).get('coordinates') or [None, None]
    intro = ['%s is a branch of the %s at %s.' % (name, sysname, addr) if addr else '%s is a branch of the %s.' % (name, sysname)]
    add(slug='lib-%s-%s' % (r['system'].lower(), slug(nm)), type='library', name=name, seat='%s · %s' % (sysname, boro),
        desc=intro[0], intro=intro, lat=c[1], lng=c[0], addr=addr, zip=r.get('zip', ''), weburl=r.get('url', ''),
        kv=[['Library system', sysname], ['Address', addr], ['Borough', boro]], links=[['Branch page', r['url']]] if r.get('url') else [],
        logo=logo, group='Libraries', topic=sysname, where=boro)
    made['libraries'] += 1

# ---- child care centers (DOHMH permits) ----
GEO = SRC('childcare-geo.json')
def ages(s):
    m = re.match(r'(\d+) YEARS? - (\d+) YEARS?', s or '')
    return 'Ages %s to %s' % (m.group(1), m.group(2)) if m else ''
CCT = {'Child Care - Infants/Toddlers': 'Infants and toddlers', 'Child Care - Pre School': 'Preschool child care', 'Camp': 'Day camp'}
seen = set()
for r in SRC('dohmh-childcare.json'):
    if r['dc_id'] in seen: continue
    seen.add(r['dc_id'])
    kind = CCT.get(r.get('childcaretype', ''), 'Child care')
    name = tc(r.get('centername', ''))
    street = tc(' '.join(x for x in (r.get('building', ''), r.get('street', '')) if x))
    boro = BORO.get((r.get('borough') or '').upper(), '')
    addr = '%s, %s %s' % (street, boro, r.get('zipcode', '')) if street else ''
    g = GEO.get(r.get('bin') or '') or GEO.get('dc:' + r['dc_id'])
    a = ages(r.get('agerange'))
    intro = ['%s is a %s at %s, permitted by the NYC Health Department.' % (name, kind.lower() + (' center' if kind != 'Day camp' else ''), addr)]
    if a: intro.append('%s.' % a)
    kv = [['Type', kind], ['Ages', a.replace('Ages ', '')] if a else None, ['Capacity', r['maximumcapacity'] + ' children'] if r.get('maximumcapacity') else None,
          ['Address', addr], ['Borough', boro], ['Permit', 'NYC Health Department, ' + r['dc_id']]]
    add(slug='cc-' + r['dc_id'].lower(), type='childcare', name=name, seat='%s · %s' % (kind, boro), desc=' '.join(intro), intro=intro,
        lat=g[0] if g else None, lng=g[1] if g else None, addr=addr, zip=r.get('zipcode', ''), phone=phone_of(r.get('phone')),
        kv=[x for x in kv if x], links=[['Child care inspections (NYC Health)', 'https://a816-healthpsi.nyc.gov/ChildCare/SearchAction2.do']],
        logo='nyc-child-care.png', group='Child care', topic=kind, where=boro,
        ages=a, cckind=kind)
    made['child care centers'] += 1

# ---- Pre-K sites and preschools for students with disabilities (FacDB) ----
schools = {re.sub(r'[^a-z0-9]', '', p['name'].lower()) for p in D['profiles'] if p.get('group') == 'Schools'}
for r in SRC('facdb-daycare-prek.json'):
    ds = r.get('datasource')
    if ds == 'doe_universalprek': pre, kind = 'pk-', 'Pre-K site'
    elif ds == 'nysed_activeinstitutions': pre, kind = 'swdpre-', 'Preschool for students with disabilities'
    else: continue
    name = tc(r.get('facname', ''))
    if pre == 'pk-' and re.sub(r'[^a-z0-9]', '', name.lower()) in schools: continue
    boro = BORO.get((r.get('boro') or '').upper(), '')
    addr = '%s, %s %s' % (tc(r.get('address', '')), boro, r.get('zipcode', '')) if r.get('address') else ''
    who = r.get('overagency') or ''
    intro = ['%s is a %s at %s.' % (name, kind[0].lower() + kind[1:], addr)]
    add(slug=pre + r['uid'][:10], type='prek', name=name, seat='%s · %s' % (kind, boro), desc=intro[0], intro=intro,
        lat=float(r['latitude']) if r.get('latitude') else None, lng=float(r['longitude']) if r.get('longitude') else None,
        addr=addr, zip=r.get('zipcode', ''), kv=[x for x in [['Type', kind], ['Program', tc(r.get('factype', ''))], ['Overseen by', who] if who else None,
        ['Address', addr], ['Borough', boro], ['School district', 'District ' + r['schooldist']] if r.get('schooldist') else None] if x],
        links=[['NYC Facilities Database', 'https://capitalplanning.nyc.gov/facilities']], logo='pre-k-for-all.png' if pre == 'pk-' else '', group='Child care', topic=kind, where=boro, cckind=kind)
    made[kind] += 1

for g, ts in (('Libraries', ['Brooklyn Public Library', 'New York Public Library', 'Queens Public Library']),
              ('Child care', ['Infants and toddlers', 'Preschool child care', 'Pre-K site', 'Preschool for students with disabilities', 'Day camp'])):
    G = next((x for x in D['groups'] if x['name'] == g), None)
    if not G: G = {'name': g, 'topics': []}; D['groups'].append(G)
    for t in ts:
        if t not in G['topics']: G['topics'].append(t)
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print(dict(made))
