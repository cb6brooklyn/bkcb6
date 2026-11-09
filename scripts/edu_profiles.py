#!/usr/bin/env python3
"""Profiles for every community school district and every Community Education Council, laid out like the other
profile pages (name, bio, map, the rest folded by assets/fold-secs.js):
  school-district-<n>/index.html for the 32 community school districts (the existing pages are left as they are and
  only get the fold script), cec-district-<n>/index.html for the 32 Community Education Councils (CEC 15's own page
  is kept). Contacts from data/school-district-contacts.json (insideschools.org district pages), the district's schools
  from schooldistrict/<n>/index.html, the community districts it crosses from the district shapes.
Usage: python3 scripts/edu_profiles.py"""
import html, json, os, re, warnings
warnings.filterwarnings('ignore')
from shapely.geometry import shape
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
import sys; sys.path.insert(0, 'scripts')
from district_overlaps import clean
C = json.load(open('data/school-district-contacts.json'))
TPL = open('school-district-15/index.html', encoding='utf-8').read()
HEAD = TPL[:TPL.index('<div class="pwrap">')]
BORO = {'1': ('Manhattan', 'mn', 'MNCB'), '2': ('Bronx', 'bx', 'BXCB'), '3': ('Brooklyn', 'bk', 'BKCB'), '4': ('Queens', 'qn', 'QNCB'), '5': ('Staten Island', 'si', 'SICB')}
esc = lambda t: html.escape(str(t or ''), quote=True)
def g(p):
    j = json.load(open(p)); return shape(clean({'type': 'GeometryCollection', 'geometries': [f['geometry'] for f in j['features']]})).buffer(0)
CB = {p.rsplit('-', 1)[1][:-8]: g(p) for p in __import__('glob').glob('data/districts/cb-*.geojson') if re.match(r'.*cb-\d{3}\.geojson$', p)}
def tel(p): d = re.sub(r'\D', '', p or '')[:10]; return d
def host(u): return re.sub(r'^https?://(www\.)?', '', u or '').rstrip('/')
def url(u): return u if not u or u.startswith('http') else 'https://' + u
def schools(n):
    p = 'schooldistrict/%d/index.html' % n
    if not os.path.exists(p): return []
    s = open(p, encoding='utf-8').read()
    return re.findall(r'<li><a href="(/school/[^"]+)">([^<]+)</a></li>', s)
def page(slug, title, seat, icon, intro, mapttl, chamber_n, lat, lng, secs, desc):
    h = HEAD
    h = re.sub(r'<title>.*?</title>', '<title>%s &mdash; bkcb6.app</title>' % esc(title), h, flags=re.S)
    h = re.sub(r'(<meta name="description" content=")[^"]*', r'\g<1>' + esc(desc), h)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*', r'\g<1>' + esc(desc), h)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*', r'\g<1>' + esc(title), h)
    h = re.sub(r'https://bkcb6\.app/school-district-15', 'https://bkcb6.app/' + slug, h)
    h = re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")[^"]*', r'\g<1>https://bkcb6.app' + icon, h)
    body = ('<div class="pwrap">\n\n  <div class="phead">\n    <span class="pmark"><img src="%s" alt="%s"></span>\n    <span>\n'
            '      <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/schooldistricts.html" style="color:inherit">School districts</a></div>\n'
            '      <h1>%s</h1>\n      <div class="pseat">%s</div>\n    </span>\n  </div>\n\n'
            '  <div class="sec introsec"><div class="bio dmintro">%s</div></div>\n\n'
            '  <div class="sec"><h2>Where it is</h2>\n    <div class="mapinner">\n'
            '      <div class="mapttl">%s</div>\n'
            '      <div class="msearch"><input type="search" placeholder="Search an address to drop a pin" autocomplete="off"><button type="button">Find</button><button type="button" class="mreset" data-map-reset>Reset</button></div>\n'
            '      <div class="pmap" id="map" data-profile-map data-chamber="school" data-district="%d" data-fit-own="1"%s data-point-zoom="17" data-point-icon="%s" data-point-icon-w="200" data-point-icon-h="200"></div>\n'
            '      <div class="mstat" data-map-status></div>\n'
            '      <button type="button" class="mtoggle" aria-expanded="false" data-map-toggle-btn><span style="flex:1;text-align:left">Add to the map</span><span class="marr">&#9660;</span></button>\n'
            '      <div class="mtools" data-map-toggles hidden></div>\n'
            '      <div class="mhint">Tap the map anywhere to drop a pin and open that lot.</div>\n    </div>\n  </div>\n\n') % (
        esc(icon), esc(title), esc(title), seat, intro, mapttl, chamber_n,
        (' data-point-lat="%.6f" data-point-lng="%.6f"' % (lat, lng)) if lat else '', esc(icon))
    body += ''.join(secs)
    body += ('  <div class="pfoot">Contacts from the district pages of insideschools.org. Schools from the NYC Department of Education. '
             'District lines from the Department of City Planning. Logos are the districts&rsquo; own, used to identify them.<br>\n'
             '  <a href="/schooldistricts.html">Every school district</a> &middot; <a href="/directory">The Address Directory</a> &middot; <a href="/citywide-search.html">Search any address</a></div>\n</div>\n'
             '<script src="/assets/profile-map.js?v=20261109a"></script>\n<script src="/assets/fold-secs.js?v=20261109a"></script>\n</body></html>\n')
    return h + body
made = []
for n in range(1, 33):
    D = C['district'][str(n)]; E = C['cec'][str(n)]
    sd = g('data/districts/school-%d.geojson' % n)
    parts = sorted(((cd, sd.intersection(G).area / sd.area) for cd, G in CB.items() if sd.intersects(G)), key=lambda x: -x[1])
    parts = [(cd, s) for cd, s in parts if s >= 0.01]
    boro = BORO[parts[0][0][0]][0] if parts else ''
    cbtxt = ', '.join('%s%d (%d%%)' % (BORO[cd[0]][2], int(cd[1:]), round(s * 100)) for cd, s in parts)
    cblinks = ', '.join('<a href="/cb-%s-%d.html">%s%d</a>' % (BORO[cd[0]][1], int(cd[1:]), BORO[cd[0]][2], int(cd[1:])) for cd, s in parts)
    logo = '/site-icons/school-district-%d.png' % n
    if not os.path.exists(logo[1:]) and os.path.exists('elected/school/%d.png' % n):
        open(logo[1:], 'wb').write(open('elected/school/%d.png' % n, 'rb').read())
    sch = schools(n)
    # the district
    slug = 'school-district-%d' % n
    if not os.path.exists(slug + '/index.html'):
        name = 'Community School District %d' % n
        addr = D['addr']; geo = D.get('geo')
        phones = [('Elementary and middle schools', D.get('em')), ('High schools', D.get('hs')), ('Community Education Council %d' % n, E.get('phone'))]
        phones = [(k, v) for k, v in phones if v]
        secs = ['  <div class="sec"><h2>Reaching %s</h2><div class="bio"><p>%s</p></div></div>\n\n' % (esc(name), '. '.join('%s: %s' % (esc(k), esc(v)) for k, v in phones) + '.' if phones else 'The district office is listed below.'),
                '  <div class="sec"><h2>Contact</h2><div class="bio"><ul class="kv">\n    <li><span class="k">Address</span><span class="v">%s</span></li>\n%s%s    <li><span class="k">Community districts</span><span class="v">%s</span></li>\n  </ul></div></div>\n\n' % (
                    '<br>'.join(esc(x) for x in addr),
                    ('    <li><span class="k">Phone</span><span class="v"><a href="tel:%s">%s</a></span></li>\n' % (tel(D['em']), esc(D['em']))) if D.get('em') else '',
                    ('    <li><span class="k">Website</span><span class="v"><a href="%s" target="_blank" rel="noopener">%s &#8599;</a></span></li>\n' % (esc(url(D['web'])), esc(host(D['web'])))) if D.get('web') else '',
                    cblinks),
                '  <div class="sec"><h2>Community Education Council %d</h2><div class="bio"><p>The elected parent council for the district\'s public elementary and middle schools.</p><div class="btns"><a class="btn hot" href="/cec-district-%d/">Community Education Council %d</a></div></div></div>\n\n' % (n, n, n)]
        if sch:
            secs.append('  <div class="sec"><h2>Schools in District %d</h2><div class="bio"><p>%d schools.</p><div class="chips">%s</div></div></div>\n\n' % (n, len(sch), ''.join('<a class="chip" href="%s">%s</a>' % (esc(h), esc(t)) for h, t in sch)))
        secs.append('  <div class="sec"><h2>Go on</h2><div class="btns">%s<a class="btn" href="/schooldistrict/%d/">The district and its schools, mapped</a><a class="btn" href="/citywide-search.html">Search an address</a></div></div>\n\n' % (
            ('<a class="btn hot" href="%s" target="_blank" rel="noopener">District website &#8599;</a>' % esc(url(D['web']))) if D.get('web') else '', n))
        intro = '<p><b>%s</b> is one of the 32 community school districts of NYC Public Schools, for the public elementary and middle schools in its area.%s</p>' % (name, (' It reaches into %s.' % cbtxt) if cbtxt else '')
        os.makedirs(slug, exist_ok=True)
        open(slug + '/index.html', 'w', encoding='utf-8').write(page(slug, name, 'NYC Public Schools &middot; ' + esc(boro), logo, intro,
            '%s <span>the district office and School District %d</span>' % (esc(addr[0]), n), n, geo[0] if geo else None, geo[1] if geo else None, secs,
            '%s, NYC Public Schools, %s.' % (name, boro)))
        made.append(slug)
    # the Community Education Council
    cslug = 'cec-district-%d' % n
    if not os.path.exists(cslug + '/index.html'):
        name = 'Community Education Council District %d' % n
        geo = E.get('geo'); a = E['addr']
        m = re.match(r'^(.*?),\s*([^,]+,\s*(?:NY|New York),?\s*\d{5})$', a)
        a1, a2 = (m.group(1), m.group(2)) if m else (a, '')
        rows = '    <li><span class="k">Address</span><span class="v">%s%s</span></li>\n' % (esc(a1), ('<br>' + esc(a2)) if a2 else '')
        if E.get('phone'): rows += '    <li><span class="k">Phone</span><span class="v"><a href="tel:%s">%s</a></span></li>\n' % (tel(E['phone']), esc(E['phone']))
        if E.get('email'): rows += '    <li><span class="k">Email</span><span class="v"><a href="mailto:%s">%s</a></span></li>\n' % (esc(E['email']), esc(E['email']))
        if E.get('web'): rows += '    <li><span class="k">Website</span><span class="v"><a href="%s" target="_blank" rel="noopener">%s &#8599;</a></span></li>\n' % (esc(url(E['web'])), esc(host(E['web'])))
        rows += '    <li><span class="k">Community districts</span><span class="v">%s</span></li>\n' % cblinks
        secs = ['  <div class="sec"><h2>What a Community Education Council does</h2><div class="bio"><p>Each Community Education Council has 12 voting members: 10 parents of children in pre-K through 8th grade in the district\'s schools, elected by parents, and 2 members appointed by the Borough President, with 2 non-voting high school seniors appointed by the Community Superintendent. The council approves school zoning lines and advises on education policy.</p></div></div>\n\n',
                '  <div class="sec"><h2>Contact</h2><div class="bio"><ul class="kv">\n%s  </ul></div></div>\n\n' % rows,
                '  <div class="sec"><h2>Go on</h2><div class="btns">%s<a class="btn" href="/school-district-%d/">School District %d</a><a class="btn" href="/citywide-search.html">Search an address</a></div></div>\n\n' % (
                    ('<a class="btn hot" href="%s" target="_blank" rel="noopener">CEC %d website &#8599;</a>' % (esc(url(E['web'])), n)) if E.get('web') else '', n, n)]
        intro = '<p>The <b>Community Education Council for District %d</b> (CEC%d) is the elected parent council for the public elementary and middle schools of School District %d%s.</p>' % (n, n, n, (', which reaches into %s' % ', '.join('%s%d' % (BORO[cd[0]][2], int(cd[1:])) for cd, s in parts)) if parts else '')
        os.makedirs(cslug, exist_ok=True)
        clogo = '/site-icons/cec-district-%d.png' % n   # the council's own logo where we have one, else the district's
        clogo = clogo if os.path.exists(clogo[1:]) else logo
        open(cslug + '/index.html', 'w', encoding='utf-8').write(page(cslug, name, 'Elected parent council &middot; School District %d' % n, clogo, intro,
            '%s <span>the council\'s office and School District %d</span>' % (esc(a1), n), n, geo[0] if geo else None, geo[1] if geo else None, secs,
            '%s, the elected parent council for School District %d.' % (name, n)))
        made.append(cslug)
# the existing district and council pages get the fold script too
for p in __import__('glob').glob('school-district-*/index.html') + __import__('glob').glob('cec-district-*/index.html'):
    s = open(p, encoding='utf-8').read()
    if 'fold-secs.js' not in s:
        s = s.replace('</body></html>', '<script src="/assets/fold-secs.js?v=20261109a"></script>\n</body></html>', 1)
        open(p, 'w', encoding='utf-8').write(s)
print(len(made), 'pages made:', ' '.join(made))
