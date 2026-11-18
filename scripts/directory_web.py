#!/usr/bin/env python3
"""bkcb6.app/directory/ (and /profiles/ for the apps): the Directory on the site, fully interactive. The same entries, categories and square logo
tiles as the apps' Directory (read from the apps' tools.json dir-* lists), with a search that works inside whatever is
picked, dropdowns for section, category, borough, neighborhood and district (community board, Council, Assembly, State
Senate, Congress), Near me, and a map of the results with each entry's logo.

Writes profiles/index.html (from scripts/directory_web.html), profiles/dir.json, and /directory-in/<key>/ pages that
open the Directory on that district. Rerunnable; runs at the end of app_directory_tiles.py."""
import json, os, re, collections, sys
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
import directory_grid as G
D = json.load(open(P('app/data/civic/orgs/orgs-profiles.json'), encoding='utf-8'))['profiles']
BY = {p['slug']: p for p in D}
OFF = {o['slug']: o for o in json.load(open(P('app/data/civic/officials.json'), encoding='utf-8'))}
BOARDS = {b['borocd']: b for b in json.load(open(P('app/data/civic/boards.json'), encoding='utf-8'))}
BOROS = ['Brooklyn', 'Manhattan', 'Bronx', 'Queens', 'Staten Island']
MERGE = [('Schools by borough, ', 'Schools'), ('Community-based organizations, ', 'Community-based organizations')]

def lists(app, scope=None):
    T = json.load(open(P('app/data/civic/ui', app, 'tools.json'), encoding='utf-8'))['lists']
    S = json.load(open(P('app/data/civic/ui', app, 'screens.json'), encoding='utf-8'))
    out = []
    for sec in S.get('dirSections', []):
        if scope and sec.get('scope') and sec['scope'] != scope: continue
        for it in T.get(sec['list'], []):
            d = it.get('dest', '')
            if d.startswith('screen:tools:'):
                lid = d[len('screen:tools:'):]
                out.append((sec['title'], S.get('titles', {}).get(lid, {}).get('title') or lid, lid, T.get(lid, [])))
            else:
                out.append((sec['title'], sec['title'], sec['list'], [it]))
    return out
def seccat(head, title, lid):
    for pre, name in MERGE:
        if head.startswith(pre): return name, title
    if lid.startswith('dir-cul-'): return head, title.split(', ')[0]
    return head, title
pairs = collections.OrderedDict()   # (section, category) in order
E = collections.OrderedDict()       # dest -> entry
def add(head, title, lid, items):
    s, c = seccat(head, title, lid)
    pairs.setdefault(s, collections.OrderedDict()).setdefault(c, 0)
    for it in items:
        d = it['dest']
        if d.startswith('screen:board:'): d = 'board:' + d.rsplit(':', 1)[1]
        elif d.startswith('org:') and BY.get(d[4:], {}).get('group') == 'Community boards': d = 'board:' + str(BY[d[4:]].get('cd'))
        e = E.setdefault(d, {'name': it['title'], 'cover': it.get('cover') or it.get('tile'), 'b': it.get('b', ''), 'h': it.get('h', ''), 'cats': []})
        if (s, c) not in e['cats']: e['cats'].append((s, c))
for head, title, lid, items in lists('cb6', 'bkcb6'):
    if lid.startswith('dir-cb6-'): add(head, title, lid, items)
for head, title, lid, items in lists('beyond'):
    if not lid.startswith('dir-cb6-'): add(head, title, lid, items)   # BKCB6's own lists come in once, above
# ---- where each one is, its page, and the words it answers to ----
LAYERS = [('cd', 'data/community-districts.geojson', 'boro_cd'), ('cc', 'data/council-districts.geojson', 'cc'), ('ad', 'data/assembly-districts.geojson', 'ad'),
          ('sd', 'data/senate-districts.geojson', 'sd'), ('cg', 'data/congressional-districts.geojson', 'cong_dist')]
geo = {}
for t, f, prop in LAYERS:
    feats = json.load(open(P(f)))['features']; gs = [shape(x['geometry']) for x in feats]
    geo[t] = (feats, gs, STRtree(gs), prop)
def districts(lat, lng):
    out = {}
    pt = Point(lng, lat)
    for t, (feats, gs, tree, prop) in geo.items():
        for i in tree.query(pt):
            if gs[i].contains(pt):
                n = str(feats[i]['properties'][prop]).strip()
                if t == 'cd' and not (n.isdigit() and len(n) == 3 and 1 <= int(n[1:]) <= 18): break
                out[t] = int(n); break
    return out
nolink = 0
for d, e in E.items():
    kind, key = d.split(':', 1)
    p = None; href = ''; ext = 0; keys = ''
    if kind == 'official':
        o = OFF.get(key, {}); href = '/%s/' % key
        keys = (o.get('seat', '') + ' ' + G.KEYS.get(o.get('type'), '').format(n=o.get('district') or '')).strip()
        p = next((x for x in D if x.get('official') == key), None)
    elif kind == 'board':
        b = BOARDS.get(key, {}); href = '/%s.html' % b['slug'] if b else ''
        nn = int(key[1:]) if key.isdigit() else 0
        keys = 'cb%d cb %d community district %d %s%d %s' % (nn, nn, nn, G.BABBR.get(b.get('borough'), ''), nn, key)
        p = next((x for x in D if x.get('group') == 'Community boards' and str(x.get('cd')) == key), None)
    else:
        p = BY.get(key)
        if p:
            href = G.site_page(p) or ''
            if not href and p.get('weburl'): href, ext = p['weburl'], 1
            keys = ' '.join(x for x in (p.get('seat') or '', p.get('addr') or '') if x)
    if not href: nolink += 1
    lat = lng = 0
    if p:
        try: lat, lng = float(p.get('lat') or 0), float(p.get('lng') or 0)
        except Exception: lat = lng = 0
    e.update(href=href, ext=ext, keys=keys.lower(), lat=round(lat, 5), lng=round(lng, 5), dist=districts(lat, lng) if lat and lng else {})
    if kind == 'board' and key.isdigit(): e['dist']['cd'] = int(key)
# BKCB6 places that sit only on a citywide list get the matching BKCB6 heading, so the BKCB6 Directory can show BKCB6 headings only
B6MAP = {'Pharmacies': ('BKCB6 local businesses', 'Health and medical'), 'Supermarkets': ('BKCB6 local businesses', 'Supermarkets'),
         'Government agencies': ('BKCB6 government offices', 'Government offices serving BKCB6'), 'Community boards': ('BKCB6 government offices', 'Government offices serving BKCB6'),
         'Schools and child care by age': ('BKCB6 child care', 'Child care and pre-K'), 'Things to do in parks': ('BKCB6 parks', 'Parks')}
for e in E.values():
    if e['dist'].get('cd') != 306 or any(s.startswith('BKCB6') for s, c in e['cats']): continue
    for s, c in list(e['cats']):
        t = B6MAP.get(s)
        if t and t[1] in pairs.get(t[0], {}) and t not in e['cats']: e['cats'].append(t)
# BKCB6's own six neighborhoods (hoods-cb6.json) for everything inside the district, the nearest one for a spot on an edge
_H6 = [(n, shape({'type': 'Polygon', 'coordinates': r})) for n, r in json.load(open(P('app/data/civic/hoods-cb6.json'))).items()]
def hood6(lat, lng):
    pt = Point(lng, lat)
    return next((n for n, g in _H6 if g.contains(pt)), None) or min(_H6, key=lambda ng: ng[1].distance(pt))[0]
for e in E.values(): e['h6'] = hood6(e['lat'], e['lng']) if e['dist'].get('cd') == 306 and e['lat'] else ''
sections = [{'n': s, 'cats': list(cs)} for s, cs in pairs.items()]
sidx = {s['n']: i for i, s in enumerate(sections)}
hoods = sorted({e['h'] for e in E.values() if e['h']} | {e['h6'] for e in E.values() if e['h6']})
hidx = {h: i for i, h in enumerate(hoods)}
rows = []
for e in E.values():
    cats = [sidx[s] * 1000 + sections[sidx[s]]['cats'].index(c) for s, c in e['cats']]
    dd = e['dist']
    rows.append([e['name'], e['href'], e['cover'], cats, BOROS.index(e['b']) if e['b'] in BOROS else -1, hidx.get(e['h'], -1),
                 dd.get('cd', 0), dd.get('cc', 0), dd.get('ad', 0), dd.get('sd', 0), dd.get('cg', 0), e['lat'], e['lng'], e['ext'], e['keys'], hidx.get(e['h6'], -1)])
for i, s in enumerate(sections): s['count'] = sum(1 for r in rows if any(x // 1000 == i for x in r[3]))
dk = {t: sorted({r[6 + j] for r in rows if r[6 + j]}) for j, t in enumerate(('cd', 'cc', 'ad', 'sd', 'cg'))}
data = {'sections': sections, 'boros': BOROS, 'hoods': hoods, 'districts': dk, 'E': rows}
os.makedirs(P('profiles'), exist_ok=True)
body = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
open(P('profiles/dir.json'), 'w', encoding='utf-8').write(body)
import hashlib
# three Directories from one file: BKCB6 (in the district, or on a BKCB6 list), Brooklyn, and the whole city
b6 = [x['n'].startswith('BKCB6') for x in sections]; bk = [bool(re.match(r"^BKCB6('s elected officials| government offices| schools$| museums)", x['n'])) for x in sections]; gov = [bool(re.match(r'^(Elected officials|Government agencies|Community boards)', x['n'])) for x in sections]
BR = BOROS.index('Brooklyn')
def nb6(r): return [x for x in r[3] if not bk[x // 1000]]
SC = [('bkcb6', 'bkcb6/', 'The BKCB6 Directory', sum(1 for r in rows if r[6] == 306 or any(b6[x // 1000] for x in r[3])),
       'Everything in BKCB6: Park Slope, Carroll Gardens, Cobble Hill, Red Hook, Gowanus and the Columbia Street Waterfront District. Businesses, restaurants, schools, parks, community groups, houses of worship and your elected officials.'),
      ('brooklyn', 'brooklyn/', 'The Brooklyn Directory', sum(1 for r in rows if nb6(r) and (r[4] == BR or (r[4] == -1 and any(gov[x // 1000] for x in r[3])))),
       'Everything across Brooklyn: community boards, elected officials, agencies, schools, parks, museums and community organizations.'),
      ('city', '', 'The Citywide Directory', sum(1 for r in rows if nb6(r)),
       'Everything across New York City: community boards, elected officials, agencies, schools, parks, museums, theatres, stadiums and community organizations.')]
tpl = open(P('scripts/directory_web.html'), encoding='utf-8').read(); V = hashlib.sha1(body.encode()).hexdigest()[:10]
for key, path, h1, n, lede in SC:
    others = [(p2, h2) for k2, p2, h2, *_ in SC if k2 != key]
    tabs = ''.join('<a href="/directory/%s">%s</a>' % (p2, h2) for p2, h2 in others) + '<a href="/directory/government/">The Address Directory</a>'
    page = (tpl.replace('__N__', '{:,}'.format(n)).replace('__V__', V).replace('__SCOPE__', key).replace('__DIR__', '../' if path else '').replace('__H1__', h1)
            .replace('__LEDE__', lede).replace('__TABS__', tabs).replace('__PATH__', path))
    # the Directory's address on the site is /directory/; /profiles/ is the same page, which the apps open (it forwards everyone else)
    for top in ('profiles', 'directory'):
        os.makedirs(P(top, path), exist_ok=True)
        open(P(top, path, 'index.html'), 'w', encoding='utf-8').write(page)
# the Directory inside one district: its own address, which opens the Directory on it
import shutil
if os.path.isdir(P('directory-in')): shutil.rmtree(P('directory-in'))
BN = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
def dname(t, n): return '%s Community Board %d' % (BN[str(n)[0]], int(str(n)[1:])) if t == 'cd' else {'cc': 'Council District %s', 'ad': 'Assembly District %s', 'sd': 'State Senate District %s', 'cg': 'Congressional District %s'}[t] % n
for t, ks in dk.items():
    for k in ks:
        os.makedirs(P('directory-in', '%s-%s' % (t, k)), exist_ok=True)
        nm = dname(t, k)
        open(P('directory-in', '%s-%s' % (t, k), 'index.html'), 'w').write(
            '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="apple-itunes-app" content="app-id=6813967208"><title>The Directory in %s &mdash; bkcb6.app</title>'
            '<link rel="canonical" href="https://bkcb6.app/directory/#d=%s-%s"><meta http-equiv="refresh" content="0;url=/directory/#d=%s-%s"></head>'
            '<body><p><a href="/directory/#d=%s-%s">The Directory in %s</a></p></body></html>\n' % (nm, t, k, t, k, t, k, nm))
print('web directory:', len(rows), 'profiles |', len(sections), 'sections |', sum(len(s['cats']) for s in sections), 'categories |', len(hoods), 'neighborhoods |',
      'no page to open:', nolink, '| dir.json %.1f MB' % (len(body) / 1e6), '| district pages:', sum(len(v) for v in dk.values()))
# the districts that overlap BKCB6, for the toggles on the BKCB6 Directory map: each one's whole outline, the part
# inside BKCB6, and who holds it (their logo and profile)
def _cb6_districts():
    from shapely.geometry import mapping
    cb6 = shape(json.load(open(P('data/cb6-audit/cd306.geojson'))))
    def coords(g):
        g = g.simplify(0.00015, preserve_topology=True)
        polys = [g] if g.geom_type == 'Polygon' else [x for x in getattr(g, 'geoms', []) if x.geom_type == 'Polygon']
        return [[[[round(x, 5), round(y, 5)] for x, y in ring.coords] for ring in [p.exterior]] for p in polys]
    byoff = {(o.get('type'), str(o.get('district'))): o for o in OFF.values()}
    i6 = next(i for i, x in enumerate(sections) if x['n'] == "BKCB6's elected officials")
    B6OFF = {r[1] for r in rows if any(x // 1000 == i6 for x in r[3])}
    def ordinal(n): return '%d%s' % (n, 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))
    L = [('council', 'City Council', 'data/council-districts.geojson', 'cc', 'Council District %s'),
         ('assembly', 'State Assembly', 'data/assembly-districts.geojson', 'ad', 'Assembly District %s'),
         ('senate', 'State Senate', 'data/senate-districts.geojson', 'sd', 'State Senate District %s'),
         ('congress', 'Congress', 'data/congressional-districts.geojson', 'cong_dist', 'Congressional District %s'),
         ('precinct', 'Police precincts', 'data/police-precincts-citywide.geojson', 'precinct', '%s Precinct'),
         ('school', 'School districts', 'data/school-districts-brooklyn.geojson', 'schooldist', 'School District %s')]
    out = []
    for key, title, f, prop, lab in L:
        ds = []
        for ft in json.load(open(P(f)))['features']:
            g = shape(ft['geometry'])
            if not g.is_valid: g = g.buffer(0)
            part = g.intersection(cb6)
            if part.is_empty or part.area < cb6.area * 0.002: continue
            n = int(float(ft['properties'][prop]))
            d = {'n': n, 'label': lab % (ordinal(n) if key == 'precinct' else n), 'share': round(part.area / cb6.area * 100), 'full': coords(g), 'part': coords(part)}
            rp = part.representative_point(); d['at'] = [round(rp.y, 5), round(rp.x, 5)]
            o = byoff.get((key, str(n))) if key in ('council', 'assembly', 'senate', 'congress') else None
            if o: d.update(who=o['name'], href='/%s/' % o['slug'], icon=o.get('icon') or '')
            elif key == 'precinct':
                sl = '%s-precinct' % ordinal(n)
                d.update(href='/%s/' % sl if os.path.isdir(P(sl)) else '', icon='/site-icons/%s.png' % sl if os.path.exists(P('site-icons', sl + '.png')) else '/site-icons/agencies/nypd.png')
            elif key == 'school':
                d.update(href='/school-district-%d/' % n if os.path.isdir(P('school-district-%d' % n)) else '', icon='/site-icons/agencies/nycps.png')
            # BKCB6's own officials only (the BKCB6 list), and no water-only slivers for the other kinds
            if key in ('council', 'assembly', 'senate', 'congress'):
                if not o or d['href'] not in B6OFF: continue
            elif d['share'] < 2: continue
            ds.append(d)
        out.append({'key': key, 'title': title, 'districts': sorted(ds, key=lambda d: -d['share'])})
    json.dump(out, open(P('profiles/cb6-districts.json'), 'w'), separators=(',', ':'))
    print('BKCB6 districts:', {l['key']: [d['n'] for d in l['districts']] for l in out})
_cb6_districts()
