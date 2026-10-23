#!/usr/bin/env python3
"""One profile page per elected official and per agency on bkcb6.app.

Elected officials: each had a Directory page built by build_org_pages.py from data/gov-profiles.json
(/shahana-hanif/, with the calendar and "Going on now" cards) and a district profile (/cmhanif/, with the
district, overlaps, committees and bills). The district profile is the one page: it takes the Directory page's
cards and calendar at the top, and the Directory page forwards to it.

Agencies: the citywide directory page (/agencies/dep/) and the local profile the apps use (/nyc-dep/) were two
pages for one agency. The local profile is the one page; the directory page forwards to it.

Every link on the site to a forwarded page is pointed at the one page. Writes data/profile-index.json and
app/data/civic/profile-index.json (every official, agency and community board: its one page on the site, the
screen in the apps, and the outside addresses that mean it), which the apps use to open the in-app profile for any
link to an official, an agency or a board. Idempotent: run after build_org_pages.py or build_agencies.py.
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
EV_JS = open(os.path.join(ROOT, 'scripts/oneprofile/ev_script.js'), encoding='utf-8').read()
EV_CSS = open(os.path.join(ROOT, 'scripts/oneprofile/ev.css'), encoding='utf-8').read()
START, END = '<!--oneprofile-->', '<!--/oneprofile-->'

gov = {r['slug']: r for r in J('data/gov-profiles.json')}
profiles = {p['slug']: p for p in J('app/data/civic/orgs/orgs-profiles.json')['profiles']}
officials = J('app/data/civic/officials.json')
boards = J('app/data/civic/boards.json')

# Directory page -> the one page
FORWARD = {}
for s, p in profiles.items():
    if p.get('kind') == 'official' and p.get('official') and os.path.isfile(os.path.join(ROOT, p['official'], 'index.html')):
        FORWARD['/%s/' % s] = '/%s/' % p['official']
AGENCY_DUP = {'dep': 'nyc-dep', 'hpd': 'nyc-hpd', 'dpr': 'nyc-parks-brooklyn', 'dcp': 'nyc-planning', 'lpc': 'landmarks-preservation-commission',
              'rgb': 'rent-guidelines-board', 'nycha': 'nycha-cb6', 'nycc': 'new-york-city-council', 'nycps': 'nyc-public-schools-cb6',
              'dsny': 'dsny-brooklyn-6', 'nyc-dot': 'nyc-dot', 'bpl': 'brooklyn-public-library-cb6'}
for a, local in AGENCY_DUP.items():
    if a != local or True:
        if os.path.isfile(os.path.join(ROOT, local, 'index.html')) and os.path.isdir(os.path.join(ROOT, 'agencies', a)):
            FORWARD['/agencies/%s/' % a] = '/%s/' % local

def redirect(to, title):
    return ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8"><title>%s | bkcb6.app</title>\n'
            '<link rel="canonical" href="https://bkcb6.app%s">\n<meta http-equiv="refresh" content="0; url=%s">\n'
            "<script>location.replace('%s'+location.search+location.hash);</script>\n"
            '</head><body><a href="%s">%s</a></body></html>\n') % (html.escape(title), to, to, to, to, html.escape(title))

def js(v): return json.dumps(v, ensure_ascii=False)

def cards_html(rec):
    out = ''
    for g in rec.get('going') or []:
        btns = ''.join('<a class="%s" href="%s"%s>%s</a>' % ('hot' if len(b) > 2 else '', html.escape(b[1]),
                       '' if b[1].startswith(('/', 'mailto:')) else ' target="_blank" rel="noopener"', html.escape(b[0])) for b in g.get('btns') or [])
        src = g.get('img') or ''
        if src and not src.startswith(('/', 'http')): src = '/app/data/civic/orgs/going/' + src
        img = '<img src="%s" alt="%s">' % (html.escape(src), html.escape(g.get('alt') or g.get('title') or '')) if src else ''
        out += ('<div class="gocard"%s>%s<div class="gobody"><div class="gokick">%s</div><div class="gottl">%s</div><p>%s</p><div class="gobtns">%s</div></div></div>'
                % (' data-until="%s"' % g['until'] if g.get('until') else '', img, g.get('kicker', ''), g.get('title', ''), g.get('text', ''), btns))
    if not out: return ''
    return ('<div class="sec gosec"><h2>Going on now</h2>%s</div>\n'
            "<script>document.querySelectorAll('.gocard[data-until]').forEach(function(c){var u=c.getAttribute('data-until').split('-');"
            "if(new Date()>new Date(+u[0],+u[1]-1,+u[2],23,59,59))c.remove();});</script>\n") % out

GO_CSS = ('.gocard{background:#fff;border:1px solid var(--rule,#e5e2db);border-radius:14px;overflow:hidden;margin-bottom:14px}'
          '.gocard img{display:block;width:100%;max-height:420px;object-fit:cover}.gobody{padding:14px 16px}'
          '.gokick{font-family:"DM Mono",monospace;font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;opacity:.75}'
          '.gottl{font-weight:800;font-size:1.15rem;margin:4px 0 6px}.gobody p{font-size:.92rem;line-height:1.5}'
          '.gobtns{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}.gobtns a{font-size:.85rem;font-weight:700;text-decoration:none;padding:9px 13px;border-radius:8px;border:1.5px solid #0d1b4b;color:#0d1b4b;background:#fff}'
          '.gobtns a.hot{background:#f47920;border-color:#f47920;color:#fff}')

def official_block(rec):
    accent = (rec.get('brand') or {}).get('accent', '#0d1b4b')
    cal = ''
    if rec.get('evorg'):
        script = (EV_JS.replace('__ORG__', js(rec['evorg'])).replace('__HREF__', js(rec.get('evhref') or '/o/%s.html' % rec['evorg']))
                  .replace('__NAME__', js(rec.get('evname') or 'The calendar')).replace('__LOGO__', js('/site-icons/%s.png' % rec['slug'])))
        cal = ('<div class="sec evsec"><h2>%s</h2><div id="orgEvents"><div class="evcard"><div class="evline">Loading from the CB6 calendar…</div></div></div>'
               '<div id="orgMore"></div></div>\n%s\n') % (rec.get('evtitle') or 'Coming up', script)
    cards = cards_html(rec)
    if not cal and not cards: return ''
    css = '<style>\n%s\n%s\n.evsec h2{color:%s}.evcard{background:%s}.evall{color:%s}\n</style>\n' % (GO_CSS, EV_CSS, accent, accent, accent)
    return START + '\n' + css + cards + cal + END + '\n'

def place_block(page, block):
    s = open(page, encoding='utf-8').read()
    s = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n?', '', s, flags=re.S)
    # the earlier hand-placed Gounardes job card and calendar give way to the generated block
    s = re.sub(r'<div class="sec gosec" id="jobcard">.*?(?=<style>\n#orgEvents)', '', s, flags=re.S)
    s = re.sub(r'<style>\n#orgEvents,#orgMore\{--ink:#0d1b4b\}.*?</script>\n(?=  <div data-profile-tiles)', '', s, flags=re.S)
    if block:
        anchor = '  <div data-profile-tiles'
        if anchor in s: s = s.replace(anchor, block + anchor, 1)
        else:
            m = re.search(r'<div class="sec', s)
            s = s[:m.start()] + block + s[m.start():] if m else s
    open(page, 'w', encoding='utf-8').write(s)

# 1. officials: the one page takes the cards and calendar; the Directory page forwards
for frm, to in sorted(FORWARD.items()):
    slug = frm.strip('/')
    if slug in gov:
        rec = dict(gov[slug]); rec['going'] = (profiles.get(slug) or {}).get('going') or rec.get('going') or []
        place_block(os.path.join(ROOT, to.strip('/'), 'index.html'), official_block(rec))
    page = os.path.join(ROOT, frm.strip('/'), 'index.html')
    name = (gov.get(slug) or {}).get('name') or (profiles.get(slug) or {}).get('name') or slug
    open(page, 'w', encoding='utf-8').write(redirect(to, re.sub('<[^>]+>', '', name)))
    print('one page', frm, '->', to)

# 2. every link on the site to a forwarded page points at the one page
SKIP = {'node_modules', '.git', 'app', 'scripts', 'tools'}
pat = re.compile(r'(href=["\'])(%s)(["\'#?])' % '|'.join(re.escape(k) for k in sorted(FORWARD, key=len, reverse=True)))
nfix = 0
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP]
    for n in fn:
        if not n.endswith('.html'): continue
        p = os.path.join(dp, n); rel = '/' + os.path.relpath(p, ROOT).replace(os.sep, '/').replace('index.html', '')
        if rel in FORWARD: continue
        s = open(p, encoding='utf-8', errors='surrogateescape').read()
        t = pat.sub(lambda m: m.group(1) + FORWARD[m.group(2)] + m.group(3), s)
        if t != s: open(p, 'w', encoding='utf-8', errors='surrogateescape').write(t); nfix += 1
print('pages with links pointed at the one page:', nfix)

# 3. the index: every official, agency and board, its one page and its screen in the apps
def norm(u):
    u = (u or '').strip().lower()
    u = re.sub(r'^https?://', '', u); u = re.sub(r'^(www1?|m)\.', '', u); u = u.split('#')[0].split('?')[0]
    u = re.sub(r'/index\.(page|html|shtml)$', '', u); return u.rstrip('/')
idx = {'pages': {}, 'urls': {}, 'forward': FORWARD}
def add(page, app, *urls):
    idx['pages'][page] = app
    for u in urls:
        k = norm(u)
        if k and k not in ('nyc.gov', 'ny.gov', 'council.nyc.gov', 'nyassembly.gov', 'nysenate.gov', 'governor.ny.gov') and k not in idx['urls']: idx['urls'][k] = page
people = J('app/data/civic/gov.json')['people']
council_url = {int(d): v[1] for d, v in people.get('council', {}).items()}
for o in officials:
    urls = [(o.get('office') or {}).get('site', '')]
    if o.get('type') == 'council' and o.get('district') in council_url: urls.append(council_url[o['district']])
    add('/%s/' % o['slug'], 'official:%s' % o['slug'], *urls)
for s, p in profiles.items():
    if p.get('kind') == 'official' and p.get('official'):
        g = gov.get(s, {})
        idx['urls'].setdefault(norm(g.get('weburl') or p.get('weburl')), '/%s/' % p['official'])
    elif p.get('kind') == 'agency':
        page = '/%s/' % s if os.path.isfile(os.path.join(ROOT, s, 'index.html')) else ('/agencies/%s/' % s if os.path.isdir(os.path.join(ROOT, 'agencies', s)) else '')
        if page: add(page, 'org:%s' % s, p.get('weburl', ''))
for frm, to in FORWARD.items():
    if frm.startswith('/agencies/') and to in idx['pages']: idx['pages'][frm] = idx['pages'][to]
for a in J('data/agencies.json')['agencies']:
    k = norm(a.get('url')); page = FORWARD.get('/agencies/%s/' % a['slug'], '/agencies/%s/' % a['slug'])
    if k and page in idx['pages']: idx['urls'].setdefault(k, page)
for a in J('data/agencies-nys.json')['agencies']:
    page = '/agencies/nys/%s/' % a['slug']
    if os.path.isdir(os.path.join(ROOT, page.strip('/'))): add(page, 'web:%sindex.html?app=1' % page.lstrip('/'), a.get('site', ''), a.get('ny', ''))
# police precincts and school districts (scripts/district_profiles.py): the apps open the site page, whose map is the
# area's own boundary
for g in gov.values():
    if g.get('area') and os.path.isfile(os.path.join(ROOT, g['slug'], 'index.html')):
        add('/%s/' % g['slug'], 'web:%s/index.html?app=1' % g['slug'], g.get('weburl', ''))
# the same areas in apps that have the area profile screen (civic/area-profiles.json): "areas" is read before "pages",
# so an app without that screen keeps opening the site page
idx['areas'] = {}
if os.path.exists(os.path.join(ROOT, 'app/data/civic/area-profiles.json')):
    for a in J('app/data/civic/area-profiles.json'):
        if a.get('page') in idx['pages']: idx['areas'][a['page']] = 'official:%s' % a['slug']
BORO = {'1': ['manhattan', 'm'], '2': ['bronx', 'bx'], '3': ['brooklyn', 'bk'], '4': ['queens', 'q'], '5': ['statenisland', 'si']}
# the boards' own websites that do not follow the nyc.gov pattern
OWN_SITES = {'brooklyncb5.org': '305', 'brooklyncb8.org': '308', 'brooklyncb11.org': '311', 'brooklyncb12.org': '312', 'cb14brooklyn.com': '314',
             'cb5.org': '105', 'cbsix.org': '106', 'cb8m.com': '108', 'cb9m.org': '109', 'cb11m.org': '111', 'queenscb3.cityofnewyork.us': '403',
             'brooklyncb6.cityofnewyork.us': '306'}
for b in boards:
    if not os.path.isdir(os.path.join(ROOT, b['slug'])): continue
    cd = b['borocd']; n = int(cd[1:]); names = BORO[cd[0]]
    urls = [b.get('website', '')] + ['nyc.gov/site/%scb%d' % (names[0], n), 'nyc.gov/%scb%d' % (names[0], n), 'nyc.gov/%scb%d' % (names[1], n)]
    urls += [u for u, c in OWN_SITES.items() if c == cd]
    add('/%s/' % b['slug'], 'board:%s' % cd, *urls)
# outside addresses that name an agency or official by another address than the one on file
EXTRA = {'nyc.gov/site/dot': '/nyc-dot/', 'nyc.gov/site/parks': '/nyc-parks-brooklyn/', 'nyc.gov/site/criminaljustice': '/agencies/mocj/',
         'nysp.ny.gov': '/agencies/nys/division-of-state-police/', 'hcr.ny.gov/governance': '/agencies/nys/homes-and-community-renewal/',
         'hcr.ny.gov/sonyma': '/agencies/nys/housing-finance-agency-state-of-ny-mortgage-agency-sonyma/',
         'governor.ny.gov/lt-governor-antonio-delgado': '/lieutenantgovernor/', 'nycgo.com': '/agencies/new-york-city-tourism-plus-conventions/'}
for k, v in EXTRA.items():
    if v in idx['pages']: idx['urls'][k] = v
for p in ('data/profile-index.json', 'app/data/civic/profile-index.json'):
    json.dump(idx, open(os.path.join(ROOT, p), 'w'), ensure_ascii=False, indent=0, sort_keys=True)
print('index:', len(idx['pages']), 'profiles,', len(idx['urls']), 'outside addresses,', len(FORWARD), 'forwards')
