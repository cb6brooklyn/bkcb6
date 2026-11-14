#!/usr/bin/env python3
"""Every NYC and NYS agency profile (/agencies/<slug>/, /agencies/nys/<slug>/) in the Directory profile format.

The agency pages were short pages (In brief, What it does, Go on). This rebuilds each one on the same template as
the Directory profiles (/nyc-dep/, /chips/), from build_org_pages.py: the logo header, the intro, the map of the
building (with its community district and zoning, as on /nyc-dep/), the details, what it does, any other section
the page carried (the offices that report to it, the members lists), and the buttons. The words, links and
buttons are the page's own, carried over as they were. NYC headquarters come from data/agency-locations.json; the
NYS agencies have no address on file, so their profile carries no map. Pages that forward elsewhere are left
alone. Idempotent: the page's own content is kept in a marker so a second run reads it back.
"""
import glob, html, json, os, re
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
SRC = open(P('build_org_pages.py'), encoding='utf-8').read()
G = {'__file__': P('build_org_pages.py'), '__name__': 'agency_profiles'}
exec(SRC[:SRC.index('for _f in (')], G)          # the templates and helpers, not the build loop
LOOP = SRC[SRC.index('for o in ORGS:'):SRC.index('# One page per official')]
LOOP = LOOP.replace("d = os.path.join(ROOT, o['slug'])", "d = os.path.join(ROOT, o['outdir'])").replace("print('built /%s' % o['slug'])", "")
MAPV = re.search(r'profile-map\.js\?v=(\w+)', open(P('nyc-dep/index.html')).read()).group(1)
LOC = json.load(open(P('data/agency-locations.json')))['agencies']

def layer():
    shapes, keys = [], []
    for f in sorted(os.listdir(P('data/districts'))):
        m = re.match(r'cb-(\d{3})\.geojson$', f)
        if not m: continue
        g = json.load(open(P('data/districts', f)))
        for ft in g.get('features', []):
            g2 = ft.get('geometry')
            if not g2: continue
            if g2['type'] == 'MultiPolygon': g2 = {'type': 'MultiPolygon', 'coordinates': [[r for r in p if len(r) >= 4] for p in g2['coordinates'] if len(p[0]) >= 4]}
            s = shape(g2); s = s if s.is_valid else s.buffer(0)
            shapes.append(s); keys.append(m.group(1))
    return STRtree(shapes), shapes, keys
CB = layer()
def cd_of(lat, lng):
    t, sh, k = CB; pt = Point(lng, lat)
    for i in t.query(pt):
        if sh[i].contains(pt): return k[i]
    return ''

def secs(s):
    """The page's sections: [(title, inner html)] in order, from the saved copy if there is one."""
    m = re.search(r'<!--agencysrc (.*?) agencysrc-->', s, re.S)
    if m: return json.loads(html.unescape(m.group(1)))
    out = []
    pos = 0
    while True:
        m2 = re.search(r'<(div|details) class="sec[^"]*"', s[pos:])
        if not m2: break
        st = pos + m2.start(); tag = m2.group(1); depth = 0; end = None
        for t in re.finditer(r'<(/?)%s\b' % tag, s[st:]):
            depth += -1 if t.group(1) else 1
            if depth == 0: end = st + s[st:].index('>', t.start()) + 1; break
        if end is None: break
        block = s[st:end]
        hm = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.S)
        title = re.sub(r'<[^>]+>', '', hm.group(1)).strip() if hm else ''
        if title in ('In brief', 'What it does', 'Go on'):
            inner = block[hm.end():block.rindex('</%s>' % tag)]
            out.append([title, inner])
        else:
            # kept whole, with its markers (the members lists) if it has them
            a = s.rfind('<!--members-->', pos, st); b = s.find('<!--/members-->', end)
            if a >= 0 and s[a + 14:st].strip() == '' and b >= 0 and s[end:b].strip() == '':
                block = s[a:b + 15]
            out.append([title or '_', '__RAW__' + block])
        pos = end
    g = lambda pat, d='': (re.search(pat, s, re.S) or [None, d])[1]
    head = {'name': html.unescape(re.sub(r'<[^>]+>', '', g(r'<h1>(.*?)</h1>'))).strip(),
            'seat': g(r'<div class="pseat">(.*?)</div>') or g(r'<div class="psub">(.*?)</div>'),
            'logo': g(r'<span class="pmark"><img src="([^"]+)"') or g(r'<img src="(/site-icons/agencies/[^"]+)"'),
            'desc': html.unescape(g(r'<meta name="description" content="([^"]*)"')),
            'beacon': g(r'(<!-- Cloudflare Web Analytics -->.*?<!-- End Cloudflare Web Analytics -->)') or g(r"(<script type='module' src='https://static\.cloudflareinsights\.com[^\n]*?</script>)"),
            'foot': (re.search(r'<div class="pfoot">(.*?)</div>', s, re.S) or [None, ''])[1]}
    return {'head': head, 'secs': out}

made = skipped = 0
for f in sorted(glob.glob(P('agencies/*/index.html')) + glob.glob(P('agencies/nys/*/index.html'))):
    rel = os.path.relpath(os.path.dirname(f), ROOT)
    s = open(f, encoding='utf-8').read()
    if rel == 'agencies/nys' or 'http-equiv="refresh"' in s or 'location.replace(' in s[:3000] or '<h1>' not in s:
        skipped += 1; continue
    src = secs(s)
    h, S = src['head'], src['secs']
    slug = rel.split('/')[-1]; nys = rel.startswith('agencies/nys/')
    paras = lambda x: re.findall(r'<p>(.*?)</p>', x, re.S)
    intro = next((paras(v) for k, v in S if k == 'In brief'), []) or [h['desc']]
    does = next((paras(v) for k, v in S if k == 'What it does'), [])
    golinks = next((v for k, v in S if k == 'Go on'), '')
    links = [(html.unescape(re.sub(r'<[^>]+>', '', t)).replace('↗', '').strip(), u, 'target="_blank"' in a)
             for a, u, t in re.findall(r'(<a [^>]*href="([^"]+)"[^>]*>)(.*?)</a>', golinks, re.S)]
    extra = ''.join(('  ' + v[7:] + '\n') if v.startswith('__RAW__') else ('  <div class="sec"><h2>%s</h2>%s</div>\n' % (k, v)) for k, v in S if k not in ('In brief', 'What it does', 'Go on'))
    o = {'slug': slug, 'outdir': rel, 'unsigned': True, 'name': h['name'], 'title': h['name'], 'seat': h['seat'], 'desc': html.escape(h['desc']),
         'intro': intro, 'does': does, 'does_title': 'What it does', 'kv': [], 'links': links, 'addr': '', 'zip': '', 'cityline': '', 'addr_note': '',
         'phone': '', 'tel': '', 'email': '', 'web': '', 'weburl': '', 'since': ''}
    loc = None if nys else LOC.get(slug)
    if loc and loc.get('lat'):
        o['lat'], o['lng'] = '%.6f' % loc['lat'], '%.6f' % loc['lng']
        a = loc['addr']; street, _, rest = a.partition(', ')
        o['addr'] = html.escape(street); o['cityline'] = html.escape(rest) or ' '
        o['addr_note'] = loc.get('note') or ''
        if loc.get('phone'): o['phone'] = loc['phone']; o['tel'] = re.sub(r'\D', '', loc['phone'])
    else:
        o['nomap'] = True; o['wherehtml'] = ''
    G['ORGS'] = [o]
    exec(LOOP, G)
    out = os.path.join(ROOT, rel, 'index.html'); t = open(out, encoding='utf-8').read()
    # its own address, its own logo, its own district and the map script the other profiles use now
    t = t.replace('https://bkcb6.app/%s"' % slug, 'https://bkcb6.app/%s/"' % rel)
    t = t.replace('/site-icons/%s.png' % slug, h['logo'])
    if not nys:
        t = t.replace('<a href="/govhub.html" style="color:inherit">Government</a>', '<a href="/agencies/" style="color:inherit">Agencies</a>', 1)
    else:
        t = t.replace('<a href="/govhub.html" style="color:inherit">Government</a>', '<a href="/agencies/nys/" style="color:inherit">State agencies</a>', 1)
    if loc and loc.get('lat'):
        cd = cd_of(loc['lat'], loc['lng'])
        t = t.replace('data-bid-slug="park-slope-5th-avenue" ', ('data-chamber="cb" data-district="%s" data-start-zoning="1" ' % cd) if cd else '', 1)
    if extra:   # the page's other sections (the offices that report to it, the members lists), before Contact
        t = t.replace('  <div class="sec"><h2>Contact</h2>', extra + '  <div class="sec"><h2>Contact</h2>', 1)
    t = re.sub(r'profile-map\.js\?v=\w+', 'profile-map.js?v=' + MAPV, t)
    if h.get('foot'): t = re.sub(r'<div class="pfoot">.*?</div>', lambda m: '<div class="pfoot">' + h['foot'] + '</div>', t, count=1, flags=re.S)
    if h.get('beacon') and 'cloudflareinsights' not in t: t = t.replace('</body>', h['beacon'] + '\n</body>', 1)
    t = t.replace('</body>', '<!--agencysrc %s agencysrc-->\n</body>' % html.escape(json.dumps(src, ensure_ascii=False)), 1)
    open(out, 'w', encoding='utf-8').write(t)
    made += 1
print('agency profiles in the Directory format:', made, '| forwarding pages left alone:', skipped)
