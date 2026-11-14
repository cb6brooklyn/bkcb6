#!/usr/bin/env python3
"""A profile page for every community-based organization the NYC Council has funded (FY2013 to FY2027).

Reads data/cbo/orgs.json (from Mike's "Community Based Organization list by category and council" workbook: the
Council's expense funding data, one row per organization, with its IRS category, website and mission) and
data/cbo/geo.json (each NYC address placed by NYC Planning Labs' geosearch). Writes:
  /cbo/<slug>/index.html   the profile: logo, category, borough, mission, address and map (with its community
                           district and Council district), website, and the community board and Council member
  /cbo/index.html          every organization, searchable, by borough and category
  data/cbo/index.json      the list the index page reads
  data/profile-index.json and app/data/civic/profile-index.json   each profile opens in the apps
  app/data/civic/orgs/orgs-profiles.json   the ones inside Brooklyn Community Board 6, in the app Directory
Organizations that already have a profile on the site or in the apps are not given a second one; their row in
the index points at the profile they have. Idempotent.
"""
import html, json, os, re, shutil
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
J = lambda p: json.load(open(P(p), encoding='utf-8'))
E = html.escape
orgs = J('data/cbo/orgs.json')
geo = J('data/cbo/geo.json')
BOROS = {'Manhattan': ('mn', 1), 'Bronx': ('bx', 2), 'Brooklyn': ('bk', 3), 'Queens': ('qn', 4), 'Staten Island': ('si', 5)}
TOPIC = {'Arts & Culture': 'Arts and culture', 'Environment & Animals': 'Parks, gardens and the environment', 'Housing & Shelter': 'Housing and community development',
         'Community & Economic Development': 'Housing and community development', 'Youth Development': 'Youth, schools and libraries',
         'Education': 'Youth, schools and libraries', 'Food & Nutrition': 'Food and mutual aid', 'Sports & Recreation': 'Sports',
         'Civil Rights & Advocacy': 'Civic and neighborhood groups', 'Public & Civic Benefit': 'Civic and neighborhood groups'}
ASB = ('<script src="/assets/site-bar.js?v=1" defer></script><a id="asb" href="https://apps.apple.com/us/app/bkcb6/id6813967208" target="_blank" rel="noopener" '
       'style="display:block;background:#0d1b4b;text-align:center;padding:8px 0;line-height:0;text-decoration:none"><img src="/appstore-badge.png" '
       'alt="Download BKCB6 on the App Store" width="121" height="40" style="height:40px;width:auto;border:0;display:inline-block"></a><script>(function(){try{var '
       'a=document.getElementById("asb"),q=/[?&]app=1\\b/.test(location.search);if(q)sessionStorage.setItem("bkapp","1");if(location.protocol==="bkcb:"||q||'
       'sessionStorage.getItem("bkapp")==="1"||/^bkcb:/.test(document.referrer)){a.style.display="none"}}catch(e){}})();</script>')

# the districts each address falls in
def layer(prefix, keyf):
    shapes, keys = [], []
    for f in sorted(os.listdir(P('data/districts'))):
        m = re.match(prefix + r'-(\d+)\.geojson$', f)
        if not m or (prefix == 'cb' and len(m.group(1)) != 3): continue
        g = json.load(open(P('data/districts', f)))
        for ft in g.get('features', [g] if g.get('type') == 'Feature' else []):
            if not ft.get('geometry'): continue
            g2 = ft['geometry']
            if g2['type'] == 'MultiPolygon':   # drop slivers too small to be rings
                g2 = {'type': 'MultiPolygon', 'coordinates': [[r for r in poly if len(r) >= 4] for poly in g2['coordinates'] if len(poly[0]) >= 4]}
            elif g2['type'] == 'Polygon':
                g2 = {'type': 'Polygon', 'coordinates': [r for r in g2['coordinates'] if len(r) >= 4]}
            shp = shape(g2)
            if not shp.is_valid: shp = shp.buffer(0)
            shapes.append(shp); keys.append(keyf(m.group(1)))
    return STRtree(shapes), shapes, keys
CB = layer('cb', lambda s: s)
CC = layer('council', int)
def where(t, lat, lng):
    tree, shapes, keys = t; pt = Point(lng, lat)
    for i in tree.query(pt):
        if shapes[i].contains(pt): return keys[i]
    return None
officials = J('app/data/civic/officials.json')
COUNCIL = {o['district']: o for o in officials if o.get('chamber') == 'council'}

def display(name):
    n, the = name.strip(), False
    while True:
        m = re.match(r'(.*?),?\s+(Inc|Incorporated|Corp|Corporation|Ltd|LLC)\.?$', n, flags=re.I)
        if m: n = m.group(1).strip(); continue
        m = re.match(r'(.*),\s*The$', n, flags=re.I)
        if m: n = m.group(1).strip(); the = True; continue
        break
    return ('The ' + n) if the and not n.lower().startswith('the ') else n
def sentence(t):
    t = (t or '').strip()
    if not t: return ''
    letters = [c for c in t if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.8:
        t = t.lower()
        t = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), t)
        t = re.sub(r'\b(nyc|ny|usa|us|lgbtq\+?|hiv|aids|esl|stem|steam)\b', lambda m: m.group(1).upper(), t)
        t = re.sub(r'\bnew york\b', 'New York', t); t = re.sub(r'\bi\b', 'I', t)
    return t
def website(w):
    w = (w or '').strip()
    if not w or w in ('0', 'N/A', 'NONE'): return ''
    return w if re.match(r'https?://', w, re.I) else 'https://' + w

def page(o):
    name, slug = o['display'], o['slug']
    boro = o['tab'] if o['tab'] in BOROS else ''
    addr = ', '.join(x for x in (o.get('a1'), o.get('a2')) if x and x != '0')
    cityline = ' '.join(x for x in (o.get('city') and o['city'].strip().title(), o.get('state'), o.get('zip')) if x)
    web = website(o.get('web'))
    mission = sentence(o.get('desc'))
    logo = '/cbo/logos/%s' % o['logofile'] if o.get('logofile') else '/cbo/logos/_none.png'
    cd, cc = o.get('cd'), o.get('cc')
    dist = []
    if cd:
        b = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}[cd[0]]
        code = {'1': 'mn', '2': 'bx', '3': 'bk', '4': 'qn', '5': 'si'}[cd[0]]
        dist.append('<a href="/cb-%s-%d.html">%s Community Board %d</a>' % (code, int(cd[1:]), b, int(cd[1:])))
    if cc:
        m = COUNCIL.get(cc)
        dist.append('<a href="/%s/">City Council District %d</a>%s' % (m['slug'], cc, (', ' + E(m['name'])) if m else '') if m else 'City Council District %d' % cc)
    kv = [('Category', E(o['cat']))]
    if boro: kv.append(('Borough', E(boro)))
    if addr: kv.append(('Address', E(addr) + ('<br>' + E(cityline) if cityline else '')))
    if dist: kv.append(('Districts', '<br>'.join(dist)))
    if web: kv.append(('Website', '<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(web), E(re.sub(r'^https?://(www\.)?', '', web).rstrip('/')))))
    kv.append(('Legal name', E(o['name'].strip())))
    kvh = ''.join('<li><span class="k">%s</span><span class="v">%s</span></li>' % kvp for kvp in kv)
    desc = '%s, %s%s.' % (name, o['cat'].lower().replace('&', 'and'), (' organization in ' + boro) if boro else ' organization')
    mapsec = ''
    if o.get('lat'):
        mapsec = ('<div class="sec"><h2>Where it is</h2><div class="pmap" id="map" data-cbo-map data-lat="%s" data-lng="%s" data-cd="%s" data-label="%s" data-logo="%s"></div>'
                  '<div class="mhint">%s</div></div>') % (o['lat'], o['lng'], cd or '', E(name), logo, E(addr + (', ' + cityline if cityline else '')))
    intro = ('<p><b>%s</b> is %s %s organization%s that the New York City Council has funded.</p>' %
             (E(name), 'an' if o['cat'][0] in 'AEIOU' else 'a', E(o['cat'].lower().replace('&', 'and')), (' in ' + E(boro)) if boro else ''))
    if mission: intro += '<p class="mission"><span class="ml">In its own words, to the IRS</span>%s</p>' % E(mission)
    btns = ''
    if web: btns += '<a class="btn hot" href="%s" target="_blank" rel="noopener">Their website &#8599;</a>' % E(web)
    btns += '<a class="btn" href="/cbo/">Every Council-funded organization &rarr;</a>'
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta name="apple-itunes-app" content="app-id=6813967208"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(name)} &mdash; {E(o['cat'])}{(' &middot; ' + E(boro)) if boro else ''} &mdash; bkcb6.app</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="https://bkcb6.app/cbo/{slug}/">
<meta property="og:site_name" content="Brooklyn Community Board 6"><meta property="og:type" content="profile">
<meta property="og:title" content="{E(name)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="https://bkcb6.app/cbo/{slug}/"><meta property="og:image" content="https://bkcb6.app{logo}"><meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.js"></script><script src="/assets/mapkit-leaflet.js"></script>
<link rel="stylesheet" href="/assets/state-profile.css?v=20261112"><link rel="stylesheet" href="/assets/cbo.css?v=20261114">
</head>
<body>{ASB}
<div class="pwrap">
<div class="phead"><span class="pmark"><img src="{logo}" alt=""></span><span>
<div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/cbo/" style="color:inherit">Council-funded organizations</a></div>
<h1>{E(name)}</h1><div class="pseat">{E(o['cat'])}{(' &middot; ' + E(boro)) if boro else ''}</div></span></div>
<div class="sec"><h2>In brief</h2><div class="bio">{intro}</div></div>
{mapsec}
<div class="sec"><h2>Details</h2><ul class="kv">{kvh}</ul></div>
<div class="sec"><h2>Go on</h2><div class="btns">{btns}</div></div>
<div class="pfoot">Funding from the <a href="https://rnd.council.nyc.gov/expense_funding/" target="_blank" rel="noopener">New York City Council&rsquo;s expense funding data</a>, fiscal years 2013 to 2027. Category, website and mission from the organization&rsquo;s most recent IRS filing where one exists. Address placed by NYC Planning&rsquo;s geosearch.<br>
<a href="/cbo/">Every Council-funded organization</a> &middot; <a href="/orgs/">The CB6 Directory</a></div>
</div>
<script src="/assets/cbo-map.js?v=20261114"></script>
</body></html>
'''

# slugs, districts
used = set(os.listdir(P('cbo'))) if os.path.isdir(P('cbo')) else set()
seen = set()
for o in orgs:
    o['display'] = display(o['name'])
    base = re.sub(r'[^a-z0-9]+', '-', o['display'].lower()).strip('-')[:70] or 'org'
    s = base; k = 2
    while s in seen: s = '%s-%d' % (base, k); k += 1
    seen.add(s); o['slug'] = s
    g = geo.get('%s|%d' % (o['tab'], o['row']))
    # placed only where the address the city's geosearch found is in the borough the Council lists it in
    if g and g.get('lat') and (g.get('conf') or 0) >= 0.8 and (g.get('boro') or '').replace('The ', '') == o['tab']:
        o['lat'], o['lng'] = g['lat'], g['lng']
        o['cd'] = where(CB, g['lat'], g['lng']); o['cc'] = where(CC, g['lat'], g['lng'])

os.makedirs(P('cbo', 'logos'), exist_ok=True)
made = 0; idx = []
for o in orgs:
    ex = o.get('existing')
    row = {'n': o['display'], 'c': o['cat'], 'b': o['tab'], 'cd': o.get('cd'), 'cc': o.get('cc'),
           'l': ('/cbo/logos/' + o['logofile']) if o.get('logofile') else ''}
    if ex:
        row['u'] = ex; idx.append(row); continue
    os.makedirs(P('cbo', o['slug']), exist_ok=True)
    open(P('cbo', o['slug'], 'index.html'), 'w', encoding='utf-8').write(page(o))
    row['u'] = '/cbo/%s/' % o['slug']; idx.append(row); made += 1
os.makedirs(P('data/cbo'), exist_ok=True)
json.dump(idx, open(P('data/cbo/index.json'), 'w'), ensure_ascii=False, separators=(',', ':'))

# the apps open every profile in the app
for p in ('data/profile-index.json', 'app/data/civic/profile-index.json'):
    t = J(p)
    t['pages'] = {k: v for k, v in t['pages'].items() if not k.startswith('/cbo/')}
    t['urls'] = {k: v for k, v in t['urls'].items() if not str(v).startswith('/cbo/')}
    for o in orgs:
        if o.get('existing'): continue
        t['pages']['/cbo/%s/' % o['slug']] = 'web:cbo/%s/index.html?app=1' % o['slug']
        w = website(o.get('web'))
        if w:
            k = re.sub(r'^https?://(www\.)?', '', w).rstrip('/').lower()
            if k and '/' not in k: t['urls'].setdefault(k, '/cbo/%s/' % o['slug'])
    t['pages']['/cbo/'] = 'web:cbo/index.html?app=1'
    json.dump(t, open(P(p), 'w'), ensure_ascii=False, indent=0, sort_keys=True)

# every one goes in the Directory (the apps' and the site's /profiles/), under its category
TOPIC = {'Arts & Culture': 'Arts and culture', 'Human & Social Services': 'Human and social services', 'Education': 'Education',
         'Religious Organizations': 'Faith organizations', 'Community & Economic Development': 'Housing and community development',
         'Health & Mental Health': 'Health and mental health', 'Youth Development': 'Youth, schools and libraries', 'Sports & Recreation': 'Sports',
         'Housing & Shelter': 'Housing and community development', 'Environment & Animals': 'Parks, gardens and the environment',
         'Philanthropy & Foundations': 'Philanthropy', 'Legal Services & Justice': 'Legal services and justice', 'Food & Nutrition': 'Food and mutual aid',
         'Civil Rights & Advocacy': 'Civic and neighborhood groups', 'Public Safety & Emergency Services': 'Public safety',
         'Public & Civic Benefit': 'Civic and neighborhood groups', 'Employment & Workforce': 'Jobs and workforce', 'International': 'International',
         'Other': 'Community and support'}
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('cbo-')]
nk = lambda n: re.sub(r'[^a-z0-9]', '', re.sub(r'\b(inc|incorporated|corp|corporation|ltd|llc|the)\b', '', n.lower().replace('&', 'and')))
names = {nk(p['name']) for p in D['profiles']}
for fn in os.listdir(P('app/data/civic/orgs/logos')):
    if fn.startswith('cbo-'): os.remove(P('app/data/civic/orgs/logos', fn))
added = 0
for o in orgs:
    if o.get('existing') or nk(o['display']) in names: continue
    logo = ''
    if o.get('logofile'):
        shutil.copy(P('cbo', 'logos', o['logofile']), P('app/data/civic/orgs/logos', 'cbo-' + o['logofile'])); logo = 'cbo-' + o['logofile']
    web = website(o.get('web')); mission = sentence(o.get('desc'))
    boro = o['tab'] if o['tab'] in BOROS else ''
    city = ' '.join(x for x in ((o.get('city') or '').strip().title(), o.get('state'), o.get('zip')) if x)
    kv = [['Category', o['cat']]] + ([['Borough', boro]] if boro else []) + [['Legal name', o['name'].strip()]]
    D['profiles'].append({'slug': 'cbo-' + o['slug'], 'type': '', 'name': o['display'], 'seat': o['cat'] + ((' · ' + boro) if boro else ''),
        'desc': '%s, %s organization funded by the NYC Council.' % (o['display'], o['cat'].lower().replace('&', 'and')),
        'lat': o.get('lat'), 'lng': o.get('lng'), 'addr': ', '.join(x for x in (o.get('a1'), o.get('a2')) if x and x != '0'), 'zip': o.get('zip') or '',
        'addr_note': '', 'cityline': city, 'phone': '', 'email': '', 'web': re.sub(r'^https?://(www\.)?', '', web).rstrip('/'), 'weburl': web, 'since': '',
        'intro': ['%s is %s %s organization%s that the New York City Council has funded.' % (o['display'], 'an' if o['cat'][0] in 'AEIOU' else 'a', o['cat'].lower().replace('&', 'and'), (' in ' + boro) if boro else '')]
                 + (['In its own words, to the IRS: ' + mission] if mission else []),
        'does': [], 'kv': kv,
        'links': [['Full profile', 'https://bkcb6.app/cbo/%s/' % o['slug']]] + ([['Their website', web]] if web else []),
        'logo': logo, 'cal': '', 'n': 0, 'kind': 'org', 'official': '', 'group': 'Community groups', 'topic': TOPIC.get(o['cat'], 'Community and support'), 'sort': 0,
        'where': boro or ('Outside NYC' if o['tab'] == 'Outside NYC' else ''), 'scope': ' '.join(x for x, ok in (('cb6', o.get('cd') == '306'), ('bk', boro == 'Brooklyn')) if ok)})
    added += 1
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('profiles made:', made, '| already had a profile:', sum(1 for o in orgs if o.get('existing')), '| in the Directory:', added,
      '| placed on the map:', sum(1 for o in orgs if o.get('lat')))
