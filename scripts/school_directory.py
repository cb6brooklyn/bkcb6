#!/usr/bin/env python3
"""A Directory profile for every school in the city, and every Community Education Council and community school
district in the apps' Directory.

Schools: every page in school/ (the DOE roster, 1,962) plus every school in the NYC Facilities Database
(data.cityofnewyork.us ji82-xba5, SCHOOLS (K-12): public, charter, non-public, special education, high school
equivalency) that has no page yet. Each school/<slug>.html is rebuilt on the Directory profile template
(build_org_pages.py, as /nyc-dep/ and /chips/): logo, intro, the map of its school district with the school pinned,
details, the school's own buttons, and any block the page carried (<!--cb6dir-->). The page's own facts are kept in a
<!--schoolsrc --> marker so a rerun reads them back. Logos: the D15 and D13 school map's (myblock), the school logo set,
the CB6 Directory's own, else the NYC Public Schools mark for a DOE school.

Apps (app/data/civic/orgs/orgs-profiles.json): one entry per school (sch-<slug>, group "Schools"; CB6's schools that
already have a profile keep theirs), and one per Community Education Council and community school district (1 to 32).
Usage: python3 scripts/school_directory.py   (needs the facilities file at data/facdb-schools-k12.json)
"""
import glob, html, json, math, os, re, shutil, difflib, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
E = lambda s: html.escape(str(s or ''), quote=True)
SRC = open(P('build_org_pages.py'), encoding='utf-8').read()
G = {'__file__': P('build_org_pages.py'), '__name__': 'school_directory'}
exec(SRC[:SRC.index('for _f in (')], G)
LOOP = SRC[SRC.index('for o in ORGS:'):SRC.index('# One page per official')]
LOOP = (LOOP.replace("d = os.path.join(ROOT, o['slug'])\n    os.makedirs(d, exist_ok=True)\n    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(html)",
                     "open(o['outfile'], 'w', encoding='utf-8').write(html)")
        .replace("print('built /%s' % o['slug'])", ""))
assert "o['outfile']" in LOOP
MAPV = re.search(r'profile-map\.js\?v=(\w+)', open(P('nyc-dep/index.html')).read()).group(1)
BORO = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
BK = {'MANHATTAN': 'Manhattan', 'BRONX': 'Bronx', 'BROOKLYN': 'Brooklyn', 'QUEENS': 'Queens', 'STATEN ISLAND': 'Staten Island'}
BCODE = {'Manhattan': 'mn', 'Bronx': 'bx', 'Brooklyn': 'bk', 'Queens': 'qn', 'Staten Island': 'si'}
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', html.unescape(s).lower().replace('&', 'and').replace("'", '')).strip('-')[:58].strip('-')
NYCPS = P('assets/map-icons/schools-nycps.png')

# ---- logos we have
def nk(s):
    s = html.unescape(s or '').lower().replace('&', ' and ')
    s = re.sub(r'\b(p\.?s\.?|i\.?s\.?|m\.?s\.?|j\.?h\.?s\.?)\s*0*(\d+)', lambda m: re.sub(r'\W', '', m.group(1)) + m.group(2), s)
    s = re.sub(r'\b(the|school|of|for|and|inc|academy|high|elementary|charter)\b', ' ', s)
    return re.sub(r'[^a-z0-9]', '', s)
LOGO = {}
mb = open(P('myblock/index.html'), encoding='utf-8').read()
for n, f in re.findall(r"'([^']+)':'([a-z0-9-]+)'", mb[mb.index('var SCHOOLMAP={'):mb.index('var SCHOOLLOGO')]):
    if os.path.exists(P('assets/map-icons/d15', f + '.png')): LOGO.setdefault(nk(n), P('assets/map-icons/d15', f + '.png'))
LOGORX = [(re.compile(rx, re.I), P(p.lstrip('/'))) for rx, p in re.findall(r"\[/(.*?)/i,'(/assets/map-icons/[^']+)'\]", mb[mb.index('var SCHOOLLOGO'):mb.index('function schoolIcon')]) if os.path.exists(P(p.lstrip('/')))]
for n, f in json.load(open(P('assets/school-logos/logos.json'))).items():
    if os.path.exists(P('assets/school-logos', f)): LOGO.setdefault(nk(n), P('assets/school-logos', f))
PROF = P('app/data/civic/orgs/orgs-profiles.json')
D = json.load(open(PROF, encoding='utf-8'))
OWN = {}   # CB6 schools that already have a Directory profile, by their school page
for p in D['profiles']:
    if p['slug'].startswith('sch-'): continue
    for l in p.get('links') or []:
        m = re.search(r'bkcb6\.app/school/([^/".]+)(?:\.html)?$', l[1])
        if m: OWN[m.group(1)] = p
    if p.get('topic') == 'Schools' and p.get('logo') and os.path.exists(P('app/data/civic/orgs/logos', p['logo'])):
        LOGO.setdefault(nk(p['name']), P('app/data/civic/orgs/logos', p['logo']))

# ---- the schools
def kvs(block):
    return [[html.unescape(re.sub(r'<[^>]+>', '', k)).strip(), v.strip()] for k, v in re.findall(r'<li><span class="k">(.*?)</span><span class="v">(.*?)</span></li>', block, re.S)]
def read_page(f):
    s = open(f, encoding='utf-8').read()
    m = re.search(r'<!--schoolsrc (.*?) schoolsrc-->', s, re.S)
    if m: return json.loads(html.unescape(m.group(1)))
    g = lambda p: (re.search(p, s, re.S) or [None, ''])[1]
    i = s.find('<h2>Details</h2>')
    det = s[i:s.find('</ul>', i)] if i >= 0 else ''
    return {'slug': os.path.basename(f)[:-5], 'name': html.unescape(re.sub(r'<[^>]+>', '', g(r'<h1>(.*?)</h1>'))).strip(),
            'seat': g(r'<div class="pseat">(.*?)</div>'), 'what': re.findall(r'<p>(.*?)</p>', g(r'<h2>What it is</h2><div class="bio">(.*?)</div></div>'), re.S),
            'kv': kvs(det), 'lat': g(r'data-point-lat="([-\d.]+)"'), 'lng': g(r'data-point-lng="([-\d.]+)"'),
            'sd': g(r'data-chamber="school" data-district="(\d+)"'), 'cb6dir': g(r'(<!--cb6dir-->.*?<!--/cb6dir-->)'),
            'foot': g(r'<div class="pfoot">(.*?)</div>'), 'beacon': g(r'(<!-- Cloudflare Web Analytics -->.*?<!-- End Cloudflare Web Analytics -->)')}
pages = [x for x in (read_page(f) for f in sorted(glob.glob(P('school', '*.html')))) if not x.get('new')]
F = json.load(open(P('data/facdb-schools-k12.json')))
F = [f for f in F if f.get('factype') != 'REGENTS APPROVED FOREIGN COLLEGES' and f.get('latitude')]
dist = lambda a, b, c, d: math.hypot((a - c) * 111000, (b - d) * 84000)
ex = [(nk(r['name']), float(r['lat']), float(r['lng']), r) for r in pages if r.get('lat')]
for f in F:
    la, lo, k = float(f['latitude']), float(f['longitude']), nk(f['facname'])
    best = None
    for kk, a, b, r in ex:
        d = dist(la, lo, a, b)
        if d < 3000:
            sc = 1 if kk == k else difflib.SequenceMatcher(None, k, kk).ratio() if abs(len(k) - len(kk)) < 25 else 0
            if (kk == k) or (d < 250 and len(k) > 5 and (k in kk or kk in k)) or (sc > 0.85 and d < 800) or (sc > 0.7 and d < 120):
                c = (sc, -d)
                if not best or c > best[0]: best = (c, r)
    if best: best[1].setdefault('fac', f)
    else: f['_new'] = True

TYPE = {'ELEMENTARY SCHOOL': 'elementary school', 'HIGH SCHOOL': 'high school', 'JUNIOR HIGH-INTERMEDIATE-MIDDLE SCHOOL': 'middle school',
        'MIDDLE SCHOOL': 'middle school', 'K-8 SCHOOL': 'K-8 school', 'K-12 ALL GRADES SCHOOL': 'K-12 school', 'SECONDARY SCHOOL': 'secondary school',
        'UNGRADED SCHOOL': 'ungraded school', 'OTHER SCHOOL': 'school'}
def kind_of(f):
    t = f['factype']
    if f['facsubgrp'].startswith('GED'): return 'High school equivalency program', 'High school equivalency programs'
    if t == 'SATELLITE SITE FOR STUDENTS WITH DISABILITIES': return 'Site for students with disabilities', 'Special education schools'
    if t == 'APPROVED PRIVATE SCHOOLS FOR SWD': return 'Approved private school for students with disabilities', 'Special education schools'
    if t == 'NYCHA COMMUNITY CENTER - SCHOOL': return 'School at a NYCHA community center', 'Public schools'
    base, _, who = t.partition(' - ')
    lvl = TYPE.get(base, 'school')
    if 'SPECIAL EDUCATION' in who: return ('Public ' if 'PUBLIC' in who else 'Charter ') + lvl + ' for special education', 'Special education schools'
    if who == 'CHARTER' or t == 'CHARTER SCHOOL': return ('Charter ' + lvl) if t != 'CHARTER SCHOOL' else 'Charter school', 'Charter schools'
    if who == 'NON-PUBLIC': return 'Private or parochial ' + lvl, 'Private and parochial schools'
    return 'Public ' + lvl, 'Public schools'
def title_name(f):
    n = f.get('opname') if f.get('optype') == 'Non-public' and f.get('opname') and f['opname'].upper().replace('(THE)', '').strip(' ,') in f['facname'].upper() + ' THE' else ''
    n = n or f['facname']
    m = re.match(r'^(.*?)\s*\((The)\)$', n)
    if m: n = 'The ' + m.group(1)
    if n.isupper() or n.islower():
        n = re.sub(r"[A-Za-z][A-Za-z']*", lambda m: m.group(0).capitalize(), n.lower())
        n = re.sub(r'\b(Of|The|And|For|At|In|On|A|An|To)\b', lambda m: m.group(0).lower(), n); n = n[0].upper() + n[1:]
        n = re.sub(r'\b(P\.?s|I\.?s|M\.?s|J\.?h\.?s|Hs|Ii|Iii|Iv|Nyc|Usa|Ymca|Yeshiva|Sar|Ps|Is|Ms)\b', lambda m: m.group(0).upper() if len(m.group(0)) <= 4 and m.group(0) not in ('Yeshiva',) else m.group(0), n)
    n = re.sub(r"(?<=[A-Za-z])'S\b", "'s", n)
    n = re.sub(r'^Ged\b', 'GED', n)
    return n
CD = {}
def cbname(cd):
    b = BORO.get(str(cd)[:1]); n = int(str(cd)[1:]) if str(cd)[1:].isdigit() else 0
    return ('%s Community Board %d' % (b, n), '/cb-%s-%d.html' % (BCODE[b], n)) if b and 0 < n < 19 else ('', '')

schools = []
used = {r['slug'] for r in pages}
for r in pages:
    f = r.get('fac') or {}
    kv = [list(x) for x in r['kv']]
    get = lambda k: next((v for kk, v in kv if kk == k), '')
    boro = BK.get((f.get('boro') or '').upper()) or BORO.get(f.get('borocode') or '') or next((b for b in BORO.values() if b in get('Address')), '') or next((b for b in BORO.values() if b in html.unescape(r['seat'])), '')
    dbn = re.sub(r'<[^>]+>', '', get('DBN')).strip()
    seatkind = html.unescape(re.sub(r'&#\d+;', '', r['seat'])).split('·')[0].strip()
    kind, topic = kind_of(f) if f else ((seatkind[0].upper() + seatkind[1:]) if seatkind else 'School', 'Public schools')
    if not f and dbn: kind = 'Public ' + seatkind.lower().replace('junior high-intermediate-middle', 'middle school').replace('school school', 'school') if seatkind and seatkind != 'School' else 'Public school'
    if re.search(r'charter', r['name'], re.I) and topic == 'Public schools': topic = 'Charter schools'
    schools.append({'slug': r['slug'], 'src': r, 'fac': f, 'name': r['name'], 'kind': kind, 'topic': topic, 'boro': boro, 'dbn': dbn,
                    'lat': float(r['lat']), 'lng': float(r['lng']), 'sd': r['sd'] or (f.get('schooldist') or ''), 'cd': f.get('cd') or '', 'kv': kv})
for f in F:
    if not f.get('_new'): continue
    n = title_name(f); s = slug(n) or 'school'
    if s in used: s = slug(n + ' ' + (f.get('address') or ''))[:70].strip('-')
    k = 2
    while s in used: s = '%s-%d' % (slug(n), k); k += 1
    used.add(s)
    kind, topic = kind_of(f)
    schools.append({'slug': s, 'src': None, 'fac': f, 'name': n, 'kind': kind, 'topic': topic, 'boro': BK.get((f.get('boro') or '').upper()) or BORO.get(f.get('borocode') or '', ''), 'dbn': '',
                    'lat': float(f['latitude']), 'lng': float(f['longitude']), 'sd': f.get('schooldist') or '', 'cd': f.get('cd') or '', 'kv': []})

# ---- each school's facts, its page, its Directory entry
LOGOS_DIR = P('app/data/civic/orgs/logos')
for fn in os.listdir(LOGOS_DIR):
    if fn.startswith('sch-'): os.remove(os.path.join(LOGOS_DIR, fn))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('sch-')]
names_have = {nk(p['name']) for p in D['profiles'] if p.get('topic') == 'Schools'}
made = new_pages = entries = 0
nlogo = collections.Counter()
WEBF = P('data/schools-web/web.json')
WEB = json.load(open(WEBF)) if os.path.exists(WEBF) else {}
WEBLOGO = P('assets/school-logos/web')
def grades(g):
    m = {'PK': 'Pre-K', '0K': 'K', 'SE': 'special education', '3K': '3-K'}
    return ', '.join(m.get(x, x.lstrip('0') or x) for x in g.split(',') if x)
SD = lambda n: '<a href="/school-district-%s/">District %s</a> &middot; <a href="/cec-district-%s/">CEC %s</a>' % (n, n, n, n)
for s in schools:
    f = s['fac']; r = s['src'] or {}
    kv = [x for x in s['kv'] if x[0] not in ('Address', 'Phone')]
    phone = re.sub(r'<[^>]+>', '', next((v for k, v in s['kv'] if k == 'Phone'), '')).strip()
    addr = re.sub(r'<[^>]+>', '', next((v for k, v in s['kv'] if k == 'Address'), '')).strip()
    street = addr.split(', ')[0] if addr else ''
    if f:
        fa = re.sub(r"[A-Za-z][A-Za-z']*", lambda m: m.group(0).capitalize(), (f.get('address') or '').lower())
        street = street or fa
        city = '%s, NY %s' % (s['boro'] or BK.get((f.get('city') or '').upper(), (f.get('city') or '').title()), f.get('zipcode') or '')
    else:
        city = '%s, NY' % s['boro'] if s['boro'] else ''
    w = WEB.get(s['slug']) or {}
    if w.get('address'):
        st, _, rest = w['address'].partition(', ')
        street, city = st, rest or city
    phone = w.get('phone') or phone
    if w.get('doe_url'):
        kv = [x for x in kv if x[0] not in ('Principal', 'Grades', 'DBN')]
        if w.get('leader'): kv.append(['School leader', E(re.sub(r',\s*', ', ', w['leader']))])
        if w.get('grades'): kv.append(['Grades', E(grades(w['grades']))])
        if w.get('accessibility'): kv.append(['Accessibility', E(w['accessibility'])])
        if w.get('space'): kv.append(['Building', E(w['space'])])
        if w.get('dbn') and not s['dbn']: s['dbn'] = w['dbn']
    weburl = w.get('website_final') or w.get('website') or ''
    if not any(k == 'Type' for k, _ in kv): kv.insert(0, ['Type', E(s['kind'])])
    if f and not s['src']:
        kv.append(['Run by', E(f.get('opname') if f.get('optype') != 'Non-public' else 'Independent (non-public)')])
        if f.get('capacity') and f['capacity'] not in ('0', '') and f.get('captype') == 'seats': kv.append(['Seats', '{:,}'.format(int(float(f['capacity'])))])
        if s['sd'] and s['sd'].isdigit() and int(s['sd']) <= 32: kv.append(['School district', SD(s['sd'])])
        cbn, cbu = cbname(f.get('cd'))
        if cbn: kv.append(['Community board', '<a href="%s">%s</a>' % (cbu, cbn)])
        if f.get('council'): kv.append(['Council', E(f['council'])])
        if f.get('policeprct'): kv.append(['Precinct', E(f['policeprct'])])
    elif f and f.get('capacity') not in (None, '', '0') and f.get('captype') == 'seats' and not any(k == 'Seats' for k, _ in kv):
        kv.append(['Seats', '{:,}'.format(int(float(f['capacity'])))])
    if s['dbn'] and not any(k == 'DBN' for k, _ in kv): kv.append(['DBN', s['dbn']])
    hood = re.sub(r'<[^>]+>', '', next((v for k, v in kv if k == 'Neighborhood'), '')).strip()
    sdnum = s['sd'] if s['sd'].isdigit() and int(s['sd']) <= 32 else ''
    a = 'an' if s['kind'][0].lower() in 'aeiou' else 'a'
    intro = ['<b>%s</b> is %s %s%s%s.' % (E(s['name']), a, E(s['kind'].lower() if not s['kind'].startswith(('K-', 'NYCHA')) else s['kind']),
             (' in ' + E(hood)) if hood else '', (', ' + s['boro']) if s['boro'] and hood else ((' in ' + s['boro']) if s['boro'] else ''))]
    if sdnum and s['topic'] in ('Public schools', 'Charter schools', 'Special education schools'): intro[0] = intro[0][:-1] + ', in Community School District %s.' % sdnum
    intro += [re.sub(r'^An? [^.]*\.\s*', '', p) for p in (r.get('what') or []) if re.sub(r'^An? [^.]*\.\s*', '', p)]
    if f and not s['src']:
        intro.append('It is run by %s.' % E(f['opname']) if f.get('optype') != 'Non-public' else 'It is an independent school, overseen by the New York State Education Department.')
    if w.get('desc') and re.search(r'admissions process|myschools|mascot|^["\u201c\u2018\']|click here|sign up', w['desc'], re.I): w['desc'] = ''
    if w.get('desc'): intro.append('In its own words: &ldquo;%s&rdquo;' % E(w['desc']))
    links = [('Its website', weburl, True)] if weburl else []
    if s['dbn'] and re.match(r'^\d\d[KMXQR]\d{3}$', s['dbn']):
        links += [('NYC Public Schools page', 'https://www.schools.nyc.gov/schools/' + s['dbn'][2:], True), ('InsideSchools', 'https://insideschools.org/school/' + s['dbn'], True)]
    if sdnum: links += [('School District %s' % sdnum, '/school-district-%s/' % sdnum, False), ('Community Education Council %s' % sdnum, '/cec-district-%s/' % sdnum, False)]
    links.append(('Every school', '/eduhub.html', False))
    # its logo
    lg = LOGO.get(nk(s['name'])) or next((p for rx, p in LOGORX if rx.search(s['name'])), None)
    own = OWN.get(s['slug'])
    if not lg and own and own.get('logo') and os.path.exists(os.path.join(LOGOS_DIR, own['logo'])): lg = os.path.join(LOGOS_DIR, own['logo'])
    if not lg and w.get('logo') and os.path.exists(os.path.join(WEBLOGO, s['slug'] + '.png')): lg = os.path.join(WEBLOGO, s['slug'] + '.png'); nlogo['from its website'] += 1
    if not lg and (s['dbn'] or (f.get('opabbrev') == 'NYCDOE' and s['topic'] in ('Public schools', 'Special education schools'))): lg = NYCPS
    nlogo['own' if lg and lg != NYCPS else 'nycps' if lg else 'none'] += 1
    weblogo = ('/' + os.path.relpath(lg, ROOT)) if lg else ''
    # the page
    o = {'slug': 'school-' + s['slug'], 'outfile': P('school', s['slug'] + '.html'), 'unsigned': True, 'name': E(s['name']), 'title': E(s['name']),
         'seat': E(s['kind']) + ((' &middot; ' + E(hood or s['boro'])) if (hood or s['boro']) else ''), 'desc': E('%s, %s %s%s.' % (s['name'], a, s['kind'].lower(), (' in ' + s['boro']) if s['boro'] else '')),
         'intro': intro, 'does': [], 'does_title': 'What it does', 'kv': kv, 'links': links, 'addr': E(street), 'zip': (f or {}).get('zipcode', ''), 'cityline': E(city) or ' ',
         'addr_note': '', 'phone': phone, 'tel': re.sub(r'\D', '', phone), 'email': '', 'web': re.sub(r'^https?://(www\.)?', '', weburl).rstrip('/'), 'weburl': weburl, 'since': '', 'lat': '%.6f' % s['lat'], 'lng': '%.6f' % s['lng']}
    if sdnum: o['area'] = {'chamber': 'school', 'district': sdnum, 'noun': 'school district', 'caption': 'the school and School District %s' % sdnum}
    if not lg: o['nologo'] = True
    G['ORGS'] = [o]
    exec(LOOP, G)
    t = open(o['outfile'], encoding='utf-8').read()
    t = t.replace('https://bkcb6.app/school-%s"' % s['slug'], 'https://bkcb6.app/school/%s"' % s['slug'])
    if lg: t = t.replace('/site-icons/school-%s.png' % s['slug'], weblogo)
    t = t.replace('<a href="/govhub.html" style="color:inherit">Government</a>', '<a href="/eduhub.html" style="color:inherit">Schools</a>', 1)
    t = re.sub(r'profile-map\.js\?v=\w+', 'profile-map.js?v=' + MAPV, t)
    t = t.replace('its boundary, the office, overlaps, land use', 'its boundary, the school, overlaps, land use')
    if r.get('cb6dir'):   # its district, precinct and sector block; the page already has its map, so the block's own map comes off
        blk = re.sub(r'\s*<div class="sec"><h2>Where it is</h2>.*?</details></div></div>', '', r['cb6dir'], count=1, flags=re.S)
        t = t.replace('  <div class="sec"><h2>Contact</h2>', '  ' + blk + '\n  <div class="sec"><h2>Contact</h2>', 1)
    foot = r.get('foot') or ('From the NYC Department of City Planning Facilities Database (NYC Open Data ji82-xba5), schools K-12, which draws on the Department of Education and the New York State Education Department.<br>\n  <a href="/citywide-search.html">Search any address</a> &middot; <a href="/">bkcb6.app</a>')
    if w.get('checked'):
        bits = (["NYC Public Schools' page for the school (address, phone, school leader, grades), read %s" % w['checked']] if w.get('doe_url') else []) + \
               (['its description and logo from its own website, read %s' % w['checked']] if (w.get('desc') or w.get('logo')) and weburl else [])
        if bits: foot = foot.replace('<br>', '. Also from ' + ' and '.join(bits) + '.<br>', 1) if '<br>' in foot else foot + ' Also from ' + ' and '.join(bits) + '.'
    t = re.sub(r'<div class="pfoot">.*?</div>', lambda m: '<div class="pfoot">' + foot + '</div>', t, count=1, flags=re.S)
    if r.get('beacon') and 'cloudflareinsights' not in t: t = t.replace('</body>', r['beacon'] + '\n</body>', 1)
    keep = r if s['src'] else {'new': True, 'slug': s['slug']}
    if keep: t = t.replace('</body>', '<!--schoolsrc %s schoolsrc-->\n</body>' % html.escape(json.dumps({k: v for k, v in keep.items() if k != 'fac'}, ensure_ascii=False)), 1)
    open(o['outfile'], 'w', encoding='utf-8').write(t)
    made += 1; new_pages += 0 if s['src'] else 1
    # the Directory entry (CB6's schools with a profile of their own keep it)
    if own or nk(s['name']) in names_have and s['boro'] == 'Brooklyn' and s['cd'] in ('306', ''): continue
    logo = ''
    if lg:
        logo = 'sch-%s%s' % (s['slug'], os.path.splitext(lg)[1].lower()); shutil.copy(lg, os.path.join(LOGOS_DIR, logo))
    akv = [[k, html.unescape(re.sub(r'<[^>]+>', '', v)).strip()] for k, v in kv if k not in ('School district',)]
    if sdnum: akv.insert(1, ['School district', 'District ' + sdnum]); akv.insert(2, ['Community Education Council', 'CEC District ' + sdnum])
    kvdest = {'District ' + sdnum: 'org:school-district-' + sdnum, 'CEC District ' + sdnum: 'org:cec-district-' + sdnum} if sdnum else {}
    D['profiles'].append({'slug': 'sch-' + s['slug'], 'type': 'school', 'name': s['name'], 'seat': s['kind'] + ((' · ' + (hood or s['boro'])) if (hood or s['boro']) else ''),
        'desc': '%s, %s %s%s.' % (s['name'], a, s['kind'].lower(), (' in ' + s['boro']) if s['boro'] else ''),
        'lat': round(s['lat'], 6), 'lng': round(s['lng'], 6), 'addr': street, 'zip': (f or {}).get('zipcode', ''), 'addr_note': '', 'cityline': city,
        'phone': phone, 'email': '', 'web': re.sub(r'^https?://(www\.)?', '', weburl).rstrip('/'), 'weburl': weburl, 'since': '',
        'intro': [html.unescape(re.sub(r'<[^>]+>', '', p)) for p in intro], 'does': [], 'kv': akv,
        'links': [[l, u if u.startswith('http') else 'https://bkcb6.app' + u] for l, u, hot in links if hot],
        'logo': logo, 'cal': '', 'n': 0, 'going': [], 'kind': 'org', 'official': '', 'group': 'Schools', 'topic': s['topic'], 'sort': 0,
        'where': s['boro'], 'sd': sdnum, 'kvdest': kvdest,
        'scope': ' '.join(x for x, ok in (('cb6', s['cd'] == '306'), ('bk', s['boro'] == 'Brooklyn')) if ok)})
    entries += 1

# ---- Community Education Councils and community school districts, from their profile pages
def from_page(path, slug_, typ):
    s = open(P(path), encoding='utf-8').read()
    g = lambda p: (re.search(p, s, re.S) or [None, ''])[1]
    ul = s[s.find('<h2>Contact</h2>'):]
    ul = ul[:ul.find('</div></div>')]
    kv = kvs(ul)
    val = lambda k: next((html.unescape(re.sub(r'<[^>]+>', ' ', v)).strip() for kk, v in kv if kk == k), '')
    addr = re.split(r'\s*\n\s*|\s{2,}', val('Address'))
    web = re.search(r'<span class="k">Website</span><span class="v"><a href="([^"]+)"', ul)
    intro = [html.unescape(re.sub(r'<[^>]+>', '', p)) for p in re.findall(r'<p>(.*?)</p>', g(r'<div class="sec introsec"><div class="bio dmintro">(.*?)</div></div>'), re.S)]
    does = []
    for m in re.finditer(r'<div class="sec"><h2>(What a Community Education Council does|Reaching [^<]+)</h2><div class="bio">(.*?)</div></div>', s, re.S):
        does += [html.unescape(re.sub(r'<[^>]+>', '', p)) for p in re.findall(r'<p>(.*?)</p>', m.group(2), re.S)]
    logo = g(r'<span class="pmark"><img src="([^"]+)"')
    lf = ''
    if logo and os.path.exists(P(logo.lstrip('/').split('?')[0])):
        lf = slug_ + os.path.splitext(logo.split('?')[0])[1]; shutil.copy(P(logo.lstrip('/').split('?')[0]), os.path.join(LOGOS_DIR, lf))
    golinks = [(html.unescape(re.sub(r'<[^>]+>', '', t)).replace('↗', '').strip(), u) for u, t in re.findall(r'<a class="btn[^"]*" href="([^"]+)"[^>]*>(.*?)</a>', s)]
    n = re.search(r'district-(\d+)', slug_).group(1)
    return {'slug': slug_, 'type': typ, 'kind': 'agency', 'official': '', 'name': html.unescape(re.sub(r'<[^>]+>', '', g(r'<h1>(.*?)</h1>'))).strip(),
            'seat': html.unescape(re.sub(r'<[^>]+>', '', g(r'<div class="pseat">(.*?)</div>'))).strip(), 'desc': html.unescape(g(r'<meta name="description" content="([^"]*)"')),
            'lat': float(g(r'data-point-lat="([-\d.]+)"') or 0) or None, 'lng': float(g(r'data-point-lng="([-\d.]+)"') or 0) or None,
            'addr': addr[0] if addr else '', 'zip': (re.search(r'\b(\d{5})\b', val('Address')) or [None, ''])[1], 'addr_note': '', 'cityline': addr[1] if len(addr) > 1 else '',
            'phone': val('Phone'), 'email': val('Email'), 'web': re.sub(r'^https?://(www\.)?', '', web.group(1)).rstrip('/') if web else '', 'weburl': web.group(1) if web else '', 'since': '',
            'intro': intro, 'does': does, 'kv': [], 'links': [[l, u if u.startswith('http') else 'https://bkcb6.app' + u] for l, u in golinks if u.startswith('http')][:6],
            'logo': lf, 'cal': '', 'n': 0, 'going': [], 'group': 'Government agencies', 'topic': '', 'sort': 0, 'sd': n,
            'kvdest': {}, 'where': '', 'scope': ''}
have = {p['slug'] for p in D['profiles']}
cecs = 0
for n in range(1, 33):
    for path, sl, typ in (('cec-district-%d/index.html' % n, 'cec-district-%d' % n, 'cec'), ('school-district-%d/index.html' % n, 'school-district-%d' % n, 'school-district')):
        if sl in have or not os.path.exists(P(path)): continue
        D['profiles'].append(from_page(path, sl, typ)); cecs += 1
for p in D['profiles']:
    if re.match(r'^(cec|school)-district-\d+$', p['slug']): p['sd'] = re.search(r'\d+$', p['slug']).group(0)
if not any(g['name'] == 'Schools' for g in D['groups']):
    D['groups'].append({'name': 'Schools', 'topics': ['Public schools', 'Charter schools', 'Private and parochial schools', 'Special education schools', 'High school equivalency programs']})
open(PROF, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')

# ---- bkcb6.app links open the profiles in the apps
pf = P('app/data/civic/profile-index.json'); T = json.load(open(pf, encoding='utf-8'))
for p in D['profiles']:
    if p['slug'].startswith('sch-'):
        T['pages']['/school/%s' % p['slug'][4:]] = 'org:' + p['slug']; T['pages']['/school/%s.html' % p['slug'][4:]] = 'org:' + p['slug']
for k, p in OWN.items():
    T['pages']['/school/%s' % k] = 'org:' + p['slug']; T['pages']['/school/%s.html' % k] = 'org:' + p['slug']
for n in range(1, 33):
    T['pages']['/cec-district-%d/' % n] = 'org:cec-district-%d' % n; T['pages']['/school-district-%d/' % n] = 'org:school-district-%d' % n
json.dump(T, open(pf, 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
print('school pages in the Directory format:', made, '| new pages:', new_pages, '| school entries in the apps Directory:', entries,
      '| CEC and school district entries added:', cecs, '| logos:', dict(nlogo))
print('by kind:', dict(collections.Counter(s['topic'] for s in schools)))
# the roster the web pass (scripts/school_web.py) works from
json.dump([{'slug': s['slug'], 'name': s['name'], 'dbn': s['dbn'], 'boro': s['boro'], 'topic': s['topic'], 'lat': s['lat'], 'lng': s['lng'],
            'addr': (s['fac'] or {}).get('address') or next((re.sub(r'<[^>]+>', '', v) for k, v in s['kv'] if k == 'Address'), ''),
            'zip': (s['fac'] or {}).get('zipcode', '')} for s in schools], open(P('data/schools-web/roster.json'), 'w'), ensure_ascii=False, indent=0)
