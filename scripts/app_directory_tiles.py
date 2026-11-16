#!/usr/bin/env python3
"""The apps' Directory as logo tiles, from the pack (no build): the hub screens of the Oct 30 build.

Every Directory section (group and topic) is a tools.json list of tiles, one per profile: its logo (`org`, from
civic/orgs/logos/), its name, and a tap that opens its profile (`official:<slug>` for elected officials,
`org:<slug>` for everyone else). The Directory screen in each app (screens.json "directory") opens with every
section as a tile on one page, grouped under headers (elected officials first, CB6's own first in BKCB6), each
tile opening its section's tiles (`screen:tools:<list>`). The Directory's own search and lists stay below.
Writes app/data/civic/ui/{cb6,bk,beyond}/tools.json (lists dir-*) and screens.json ("directory" parts and
"titles" for the section screens). Idempotent: rerun after any change to orgs-profiles.json.
"""
import json, os, re

import collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
D = json.load(open(P('app/data/civic/orgs/orgs-profiles.json'), encoding='utf-8'))
OFF = {o['slug']: o for o in json.load(open(P('app/data/civic/officials.json'), encoding='utf-8'))}
LOGOS = set(os.listdir(P('app/data/civic/orgs/logos')))
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

import hashlib
from PIL import Image, ImageDraw, ImageFont
ICONS = P('app/data/civic/icons')
CW, CH = 300, 300   # the tile's picture box: square, like the Gowanus community-based organizations grid
try:
    FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
except Exception:
    FONT = ImageFont.load_default()
MADE = set()
SRCMEMO = {}
def cover_from(src, key=None):
    """The organization's logo, whole, on a white tile (as the Gowanus community-based organizations grid draws it).
    Named by the picture itself, so tiles that show the same logo share one file: the apps download every file one
    by one, so the fewer files, the sooner the Directory shows."""
    if src in SRCMEMO: return SRCMEMO[src]
    import io
    if src.lower().endswith('.svg'):
        import cairosvg
        im = Image.open(io.BytesIO(cairosvg.svg2png(url=src, output_width=720))).convert('RGBA')
    else:
        im = Image.open(src).convert('RGBA')
    # trim the white or empty margin the logo file carries, so the logo fills the tile
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); flat = Image.alpha_composite(bg, im).convert('RGB')
    from PIL import ImageChops
    box = ImageChops.difference(flat, Image.new('RGB', im.size, (255, 255, 255))).convert('L').point(lambda v: 255 if v > 18 else 0).getbbox()
    if box and (box[2] - box[0]) * (box[3] - box[1]) > 0.05 * im.width * im.height: im = im.crop(box)
    c = Image.new('RGB', (CW, CH), (255, 255, 255))
    sc = min((CW - 30) / im.width, (CH - 30) / im.height)
    im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.LANCZOS)
    c.paste(im, ((CW - im.width) // 2, (CH - im.height) // 2), im)
    buf = io.BytesIO(); c.quantize(colors=128, method=Image.Quantize.FASTOCTREE).save(buf, format='PNG', optimize=True)
    data = buf.getvalue()
    name = 'dir-' + hashlib.sha1(data).hexdigest()[:12]
    out = os.path.join(ICONS, name + '.png')   # PNG: the apps' cover art reads civic/icons/<name>.png
    if not os.path.exists(out): open(out, 'wb').write(data)
    MADE.add(name); SRCMEMO[src] = name
    return name
def cover_cat(head, title):
    """A section tile: the category itself (its heading and name on the app's navy), never one member's logo."""
    from PIL import ImageFont as _F
    big = _F.truetype(P('assets/fonts/DMSans-Bold.ttf'), 30); small = _F.truetype(P('assets/fonts/DMSans-Bold.ttf'), 15)
    c = Image.new('RGB', (CW, CH), (6, 2, 77)); d = ImageDraw.Draw(c)
    d.rectangle([0, 0, CW, 7], fill=(244, 121, 32))
    d.text((40, 24), head.upper()[:34], fill=(244, 121, 32), font=small)
    words, lines, cur = title.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=big) <= CW - 80: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); lines = lines[:4]
    y = 52 + max(0, (CH - 52 - 38 * len(lines)) // 2 - 6)
    for ln in lines:
        d.text((40, y), ln, fill=(255, 255, 255), font=big); y += 38
    import io
    buf = io.BytesIO(); c.quantize(colors=16).save(buf, format='PNG', optimize=True); data = buf.getvalue()
    name = 'dir-c-' + hashlib.sha1(data).hexdigest()[:12]
    out = os.path.join(ICONS, name + '.png')
    if not os.path.exists(out): open(out, 'wb').write(data)
    MADE.add(name)
    return name
KINDS = {'cbo': 'Community-based organization', 'school': 'School', 'biz': 'Local business', 'place': 'Place', 'org': 'Organization'}
def cover_kind(p):
    """No logo: one shared white tile per kind (the name is printed under every tile)."""
    k = 'cbo' if p['slug'].startswith('cbo-') else 'school' if p.get('group') == 'Schools' or p.get('topic') == 'Schools' else \
        'biz' if p.get('group') == 'Local businesses' else 'place' if p.get('group') == 'Schools, parks and facilities' else 'org'
    name = 'dir-k-' + k
    out = os.path.join(ICONS, name + '.png')
    if name not in MADE:
        c = Image.new('RGB', (CW, CH), (255, 255, 255)); d = ImageDraw.Draw(c)
        words, lines, cur = KINDS[k].split(), [], ''
        for w in words:
            t = (cur + ' ' + w).strip()
            if d.textlength(t, font=FONT) <= CW - 40: cur = t
            else: lines.append(cur); cur = w
        lines.append(cur)
        y = (CH - 34 * len(lines)) // 2
        for ln in lines:
            d.text(((CW - d.textlength(ln, font=FONT)) / 2, y), ln, fill=(13, 27, 75), font=FONT); y += 34
        c.quantize(colors=8).save(out, optimize=True)
        MADE.add(name)
    return name
# The logos we already have, for the profiles that carry none: the liquor directories' business logos (by name,
# store numbers dropped), the school, health, place, culture and Gowanus logo sets (by name), and for facilities the
# logo of who runs them (MTA, Citi Bike, FDNY, BPL, Board of Elections, NYC Parks, GrowNYC, NYCHA, HPD, DOHMH, NYCPS).
import glob as _glob, html as _html
def _k(s):
    s = _html.unescape(s or '').lower().replace('&', ' and ')
    s = re.sub(r'#\s*\d+|\b(inc|llc|corp|corporation|co|ltd|the)\b|\d{2,}.*$', ' ', s)
    return re.sub(r'[^a-z0-9]', '', s)
_n = lambda s: re.sub(r'[^a-z0-9]', '', _html.unescape(s or '').lower().replace('&', 'and'))
LQ = {}
for _f in sorted(_glob.glob(P('liquor/*/liquor_directory.json'))):
    for r in json.load(open(_f))['businesses']:
        if r.get('logo') and os.path.exists(P(r['logo'].lstrip('/'))):
            for n in (r.get('display_name'), r.get('dba'), r.get('legal_name')):
                if n and len(_k(n)) >= 4: LQ.setdefault(_k(n), P(r['logo'].lstrip('/')))
SETS = {}
for _d, _pre in (('app/data/civic/orgs/logos', ''), ('site-icons', ''), ('site-icons/sq', ''), ('cbo', ''), ('assets/school-logos', 'school-')):
    for _f in sorted(os.listdir(P(_d))):
        if re.search(r'\.(png|jpe?g)$', _f, re.I):
            b = re.sub(r'\.(png|jpe?g)$', '', _f, flags=re.I)
            for x in (b, re.sub(r'^(place|health|school|culture|biz|org)-', '', b)):
                SETS.setdefault(_n(x), P(_d, _f))
for _sn, _f in json.load(open(P('assets/school-logos/logos.json'))).items():
    if os.path.exists(P('assets/school-logos', _f)): SETS.setdefault(_n(_sn), P('assets/school-logos', _f))
# CB6's business directory logos (app/data/civic/business/business-cb6.json, 1,091 with a logo), by name and street
BIZ = {}
_bd = json.load(open(P('app/data/civic/business/business-cb6.json')))
_ci = {c: i for i, c in enumerate(_bd['cols'])}
for _r in _bd['rows']:
    _l = _r[_ci['logo']]
    if not _l: continue
    _f = next((P('app/data/civic/business/logos', _l + e) for e in ('.png', '.jpg', '.jpeg', '.webp', '.svg', '') if os.path.isfile(P('app/data/civic/business/logos', _l + e))), None)
    if not _f: continue
    for _bn in (_r[_ci['name']], _r[_ci['legal']]):
        if _bn and len(re.sub(r'[^a-z0-9]', '', _bn.lower())) >= 4:
            BIZ.setdefault(re.sub(r'[^a-z0-9]', '', _html.unescape(_bn).lower().replace('&', 'and')), []).append((_f, (_r[_ci['address']] or '').lower().split(' ')[:2]))
LG = lambda *a: P(*a) if os.path.exists(P(*a)) else None
BRAND = {'mta': LG('assets/map-icons/mta.png') or LG('app/data/civic/mapicons/mta.png'), 'citibike': LG('assets/map-icons/citibike.png'),
         'fdny': LG('app/data/civic/orgs/logos/agency-fdny.png'), 'bpl': LG('app/data/civic/orgs/logos/bpl.png'),
         'boe': LG('app/data/civic/orgs/logos/agency-boe.png'), 'parks': LG('app/data/civic/orgs/logos/nycparks.png'),
         'grownyc': LG('assets/map-icons/grownyc.png'), 'nycha': LG('assets/agency-logos/nycha.png'), 'hpd': LG('app/data/civic/orgs/logos/hpd.png'),
         'dohmh': LG('app/data/civic/orgs/logos/agency-dohmh.png'), 'nycps': LG('assets/map-icons/schools-nycps.png'), 'hh': LG('app/data/civic/orgs/logos/agency-h-plus-h.png')}
def have_logo(p):
    nm, tp, ty = _html.unescape(p.get('name', '')), p.get('topic') or '', (p.get('type') or '').lower()
    k = _k(nm)
    for x in (_n(nm), _n(re.sub(r'^cbo-', '', p['slug']))):
        if len(x) >= 4 and x in SETS: return SETS[x]
    if len(k) >= 4 and k in LQ: return LQ[k]
    bk = _n(nm)
    if len(bk) >= 4 and bk in BIZ:
        c = BIZ[bk]
        if len(c) == 1: return c[0][0]
        st = (p.get('addr') or '').lower().split(' ')[:2]
        hit = next((f for f, a in c if a == st), None)
        if hit: return hit
    low = nm.lower()
    if tp == 'Subway stations and Citi Bike': return BRAND['citibike'] if ('citi' in low or '&' in nm or ' pl' in low or 'bike' in ty) else BRAND['mta']
    if tp == 'Firehouses': return BRAND['fdny']
    if tp == 'Libraries' or ('library' in low and tp == 'Culture and institutions'): return BRAND['bpl']
    if tp == 'Poll sites': return BRAND['boe']
    if tp == 'Farmers markets' and 'greenmarket' in low: return BRAND['grownyc']
    if tp == 'Housing sites': return BRAND['nycha'] if 'nycha' in low else BRAND['hpd']
    if tp == 'Child care and pre-K': return BRAND['nycps'] if re.search(r'\b(pre-?k|3-?k|p\.?s\.?\s*\d|nyc ?ps)\b', low) else BRAND['dohmh']
    if 'nyc health + hospitals' in low or 'h+h' in low: return BRAND['hh']
    if tp in ('Parks and playgrounds', 'Parks', 'Parks, playgrounds and gardens') or ty in ('park', 'playground', 'court', 'field'): return BRAND['parks']
    return None

# the borough and neighborhood of a profile (data/city-neighborhoods.geojson, the neighborhoods the site's maps use)
from shapely.geometry import shape as _shape, Point as _Point
from shapely.strtree import STRtree as _STR
_HF = json.load(open(P('data/city-neighborhoods.geojson')))['features']
_HG = [_shape(x['geometry']) for x in _HF]; _HT = _STR(_HG)
BOROS5 = ('Manhattan', 'Bronx', 'Brooklyn', 'Queens', 'Staten Island')
from shapely.geometry import Polygon as _Poly
_CB6H = [(n, _Poly(rings[0])) for n, rings in json.load(open(P('app/data/civic/hoods-cb6.json'))).items()]
def area_of(p):
    b = (p.get('culture_where') or p.get('where') or '')
    b = b if b in BOROS5 else ''
    h = ''
    try: lat, lng = float(p.get('lat') or 0), float(p.get('lng') or 0)
    except Exception: lat = lng = 0
    if lat and lng and p.get('group') == 'Local businesses':
        # BKCB6's businesses: the district's own six neighborhoods (hoods-cb6.json), the nearest one for a spot on an edge
        pt = _Point(lng, lat)
        h = next((n for n, g in _CB6H if g.contains(pt)), None) or min(_CB6H, key=lambda ng: ng[1].distance(pt))[0]
        return b or 'Brooklyn', h
    if lat and lng:
        pt = _Point(lng, lat)
        for i in _HT.query(pt):
            if _HG[i].contains(pt):
                h = _HF[i]['properties']['nb']; b = b or _HF[i]['properties'].get('boro', '')
                break
    return b, h
TILEMEMO = {}
def tile(p):
    if p['slug'] in TILEMEMO: return dict(TILEMEMO[p['slug']])
    t = {'title': _html.unescape(p['name']), 'symbol': 'building.2.fill'}
    src = None
    lg = p.get('logo') or ''
    if lg.startswith('../../../Logos/') and os.path.exists(P('app/data/Logos', lg[15:])):   # a community board's seal
        try: t['cover'] = cover_from(P('app/data/Logos', lg[15:]))
        except Exception: t['cover'] = cover_kind(p)
    elif lg.startswith('../../icons/'):   # a logo that is its tile picture (see below): redrawn, so a change of tile shape reaches it
        old = lg[len('../../icons/'):].rsplit('.', 1)[0]
        f = os.path.join(ICONS, old + '.png')
        if old.startswith('dir-k-') or not os.path.exists(f): t['cover'] = cover_kind(p)
        elif old in MADE: t['cover'] = old
        else:
            try: t['cover'] = cover_from(f)
            except Exception: t['cover'] = cover_kind(p)
        if not t['cover'].startswith('dir-k-'): p['logo'] = '../../icons/%s.png' % t['cover']
    else:
        if p.get('kind') == 'official' and p.get('official') in OFF:
            f = P('app/data/civic/officials', p['official'] + '.png')
            if os.path.exists(f): src = f
        elif lg in LOGOS:
            src = P('app/data/civic/orgs/logos', lg)
        else:
            src = have_logo(p)
        try:
            t['cover'] = cover_from(src) if src else cover_kind(p)
        except Exception:
            t['cover'] = cover_kind(p)
        # the schools' and Council-funded organizations' own logos: the profile reads its tile picture, so the
        # apps carry one file for both, not two
        if lg.startswith(('sch-', 'cbo-', 'cul-', 'hosp-', 'rx-', 'mkt-', 'lib-')) and src and not t['cover'].startswith('dir-k-'):
            p['logo'] = '../../icons/%s.png' % t['cover']
    t['dest'] = ('official:' + p['official']) if p.get('kind') == 'official' and p.get('official') in OFF else 'org:' + p['slug']
    # where it is, so a long category can be narrowed to a borough and then a neighborhood
    b, h = area_of(p)
    t['b'] = b; t['h'] = h
    TILEMEMO[p['slug']] = dict(t)
    return t

# elected officials, local first (Council, Borough President, Assembly, State Senate, Congress, District Attorney,
# Comptroller, Public Advocate, Mayor, Attorney General, State Comptroller, Governor, U.S. Senators)
LEVEL = [('City Council', lambda o: o.get('chamber') == 'council'),
         ('Borough Presidents', lambda o: o['slug'].startswith('bp')),
         ('State Assembly', lambda o: o.get('chamber') == 'assembly'),
         ('State Senate', lambda o: o.get('chamber') == 'senate'),
         ('Congress', lambda o: o.get('chamber') == 'congress' or o['slug'].startswith('rep')),
         ('District Attorneys', lambda o: o['slug'].startswith('da')),
         ('Citywide', lambda o: o['slug'] in ('comptroller', 'publicadvocate', 'mayor')),
         ('Statewide', lambda o: o['slug'] in ('attorneygeneral', 'statecomptroller', 'governor', 'lieutenantgovernor')),
         ('U.S. Senate', lambda o: o['slug'].startswith('ussen'))]
CITYWIDE_ORDER = ['comptroller', 'publicadvocate', 'mayor', 'attorneygeneral', 'statecomptroller', 'lieutenantgovernor', 'governor']
def okey(p):
    o = OFF.get(p.get('official'), {})
    return (CITYWIDE_ORDER.index(o['slug']) if o.get('slug') in CITYWIDE_ORDER else 99, o.get('district') or 0, p['name'])

def lvl(p):
    o = OFF[p['official']]
    return next((i for i, (_, f) in enumerate(LEVEL) if f(o)), 99)
cat = lambda p: dict(p.get('kv') or []).get('Category', '')
offs = [p for p in D['profiles'] if p.get('kind') == 'official' and p.get('official') in OFF]
ag = [p for p in D['profiles'] if p['group'] == 'Government agencies']
cbo = [p for p in D['profiles'] if p['slug'].startswith('cbo-')]
local = lambda p: not p['slug'].startswith('cbo-')
byname = lambda ps: sorted(ps, key=lambda p: re.sub(r'^the ', '', p['name'].lower()))
def in_cd(o, cd): return any(c.get('cd') == cd and c.get('eds', 1) for c in o.get('cbs', []))
BORO = ['Manhattan', 'Bronx', 'Brooklyn', 'Queens', 'Staten Island']

SCH = [p for p in D['profiles'] if p['group'] == 'Schools']
CB6SCH = [p for p in D['profiles'] if p['group'] == 'Schools, parks and facilities' and p.get('topic') == 'Schools']
def sdof(p):
    if p.get('sd'): return str(p['sd'])
    v = dict(p.get('kv') or []).get('School district', '')
    m = re.search(r'(\d+)', v); return m.group(1) if m else ''
def by_sd(n, extra=()):
    """A school district's tiles: its Community Education Council and its district office first, then every school in it."""
    head = [p for p in D['profiles'] if p['slug'] in ('cec-district-%s' % n, 'school-district-%s' % n)]
    head.sort(key=lambda p: not p['slug'].startswith('cec'))
    return head + byname([p for p in list(SCH) + list(extra) if sdof(p) == str(n)])
SDBORO = {'1': 'Manhattan', '2': 'Manhattan', '3': 'Manhattan', '4': 'Manhattan', '5': 'Manhattan', '6': 'Manhattan', '7': 'Bronx', '8': 'Bronx',
          '9': 'Bronx', '10': 'Bronx', '11': 'Bronx', '12': 'Bronx', '13': 'Brooklyn', '14': 'Brooklyn', '15': 'Brooklyn', '16': 'Brooklyn',
          '17': 'Brooklyn', '18': 'Brooklyn', '19': 'Brooklyn', '20': 'Brooklyn', '21': 'Brooklyn', '22': 'Brooklyn', '23': 'Brooklyn',
          '24': 'Queens', '25': 'Queens', '26': 'Queens', '27': 'Queens', '28': 'Queens', '29': 'Queens', '30': 'Queens', '31': 'Staten Island', '32': 'Brooklyn'}
def school_sections(first):
    out = [('Schools by school district', 'Community Education Councils', 'dir-cecs',
            sorted([p for p in D['profiles'] if re.match(r'^cec-district-\d+$', p['slug'])], key=lambda p: (str(sdof(p)) not in first, first.index(sdof(p)) if sdof(p) in first else 0, int(sdof(p)))))]
    order = list(first) + [str(n) for n in range(1, 33) if str(n) not in first]
    for n in order:
        ps = by_sd(n, CB6SCH)
        if ps: out.append(('Schools by school district', 'District %s schools (%s)' % (n, SDBORO[n]), 'dir-sd-' + n, ps))
    bo = (['Brooklyn'] + [b for b in BORO if b != 'Brooklyn'] if '15' in first else list(BORO)) + ['Outside NYC']
    tops = next(x['topics'] for x in D['groups'] if x['name'] == 'Schools')
    for b in bo:
        for t in tops:
            ps = byname([p for p in SCH if p.get('where') == b and p.get('topic') == t])
            if ps: out.append(('Schools by borough, ' + b, t, 'dir-sch-' + slug(b) + '-' + slug(t), ps))
    return out

def area_sections(app):
    """The app's own area first: BKCB6 is CB6's, BKCB is Brooklyn's; CBNYC is the whole city."""
    out = []
    if app == 'cb6':
        H = 'BKCB6'
        cb6b = [p for p in D['profiles'] if p['slug'] == 'brooklyn-community-board-6']
        out.append(('Brooklyn Community Board 6', 'Brooklyn Community Board 6', 'dir-cb6-board', cb6b))
        cb6o = [p for p in offs if in_cd(OFF[p['official']], '306') or OFF[p['official']].get('type') in ('citywide', 'statewide', 'ussenate') or p['official'] in ('bpbrooklyn', 'dagonzalez')]
        for name, f in LEVEL:
            ps = sorted([p for p in cb6o if f(OFF[p['official']])], key=okey)
            if ps: out.append(("BKCB6's elected officials", name, 'dir-cb6-officials-' + slug(name), ps))
        out.append(('BKCB6 government offices', 'Government offices serving BKCB6', 'dir-cb6-agencies', byname([p for p in ag if os.path.exists(P(p['slug'], 'index.html')) and (p.get('type') not in ('cec', 'school-district') or p.get('sd') in ('13', '15'))])))
        out.append(('BKCB6 schools', 'District 15 schools', 'dir-cb6-d15', by_sd('15', CB6SCH)))
        out.append(('BKCB6 schools', 'District 13 schools', 'dir-cb6-d13', by_sd('13', CB6SCH)))
        grp = [p for p in D['profiles'] if p['group'] == 'Community groups' and local(p)] + [p for p in cbo if 'cb6' in (p.get('scope') or '')]
        tops = next((x['topics'] for x in D.get('groups', []) if x['name'] == 'Community groups'), [])
        tops = [t for t in tops if any((p.get('topic') or '') == t for p in grp)] + sorted({p.get('topic') or '' for p in grp} - set(tops))
        for t in tops:
            tp = byname([p for p in grp if (p.get('topic') or '') == t])
            if tp: out.append(('BKCB6 community groups', t or 'Other groups', 'dir-cb6-groups-' + slug(t or 'other'), tp))
        for t in ('Museums', 'Movie theaters'):
            ps = byname([p for p in D['profiles'] if (p.get('culture') or (p.get('topic') if p.get('group') == 'Culture' else None)) == t and str(p.get('culture_cd') or p.get('cd') or '') == '306'])
            if ps: out.append(('BKCB6 museums and movie theaters', t, 'dir-cb6-culture-' + slug(t), ps))
        # restaurants and food spots by kind of food: the Health Department's cuisine (cb6_register_profiles.py) under plainer
        # names, and, where a place has no Health Department cuisine, what its own name says (pizza, bagels, bakery, coffee...)
        FOODLAB = {'Bagels/Pretzels': 'Bagels', 'Bakery Products/Desserts': 'Bakeries and desserts', 'Coffee/Tea': 'Coffee and tea', 'Frozen Desserts': 'Ice cream and frozen desserts',
                   'Juice, Smoothies, Fruit Salads': 'Juice and smoothies', 'Hamburgers': 'Burgers', 'Chicken': 'Chicken', 'Donuts': 'Donuts', 'Sandwiches/Salads/Mixed Buffet': 'Sandwiches',
                   'Soups/Salads/Sandwiches': 'Sandwiches', 'Asian/Asian Fusion': 'Asian fusion', 'Jewish/Kosher': 'Jewish and kosher', 'Bottled Beverages': 'Drinks', 'Soups': 'Soups', 'Salads': 'Salads'}
        BYNAME = [(r"pizz", 'Pizza'), (r"\bbagel", 'Bagels'), (r"baker|patisserie|p[aâ]tisserie|pastry|pastries|cupcake|\bcakes?\b|donut|doughnut", 'Bakeries and desserts'),
                  (r"coffee|espresso|\bcaf[eé]\b|roaster|\btea\b", 'Coffee and tea'), (r"ice cream|gelat|froyo|frozen yogurt", 'Ice cream and frozen desserts'), (r"sushi|ramen|izakaya", 'Japanese'),
                  (r"taco|taqueria|burrito", 'Mexican'), (r"juice|smoothie", 'Juice and smoothies'), (r"burger", 'Burgers'), (r"\bthai\b", 'Thai'), (r"\bdiner\b", 'American'), (r"\bbbq\b|barbecue", 'Barbecue')]
        def foodtype(p):
            if p.get('group') != 'Local businesses': return None
            if p.get('cuisine'): return FOODLAB.get(p['cuisine'], p['cuisine'])
            if p.get('topic') != 'Restaurants, cafes and food': return None
            for rx, lab in BYNAME:
                if re.search(rx, p['name'], re.I): return lab
            return None
        ft = collections.defaultdict(list)
        for p in D['profiles']:
            t_ = foodtype(p)
            if t_: ft[t_].append(p); p['foodtype'] = t_
            else: p.pop('foodtype', None)
        for c_, ps in sorted(ft.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            out.append(('BKCB6 restaurants and food spots by kind', c_, 'dir-cb6-cuisine-' + slug(c_), byname(ps)))
        for lab, cats in (('Bars and nightlife', ('Bars and nightlife',)), ('Breweries, distilleries and wineries', ('Brewery, distillery, winery',))):
            ps = byname([p for p in D['profiles'] if p.get('group') == 'Local businesses' and any(kv[0] == 'Category' and kv[1] in cats for kv in p.get('kv', []))])
            if ps: out.append(('BKCB6 bars and drinks', lab, 'dir-cb6-drinks-' + slug(lab), ps))
        for g in ('Business improvement districts', 'Schools, parks and facilities', 'Local businesses'):
            tops = next((x['topics'] for x in D.get('groups', []) if x['name'] == g), [])
            ps = [p for p in D['profiles'] if p['group'] == g]
            tops = [t for t in tops if any((p.get('topic') or '') == t for p in ps)] + sorted({p.get('topic') or '' for p in ps} - set(tops))
            for t in tops:
                tp = byname([p for p in ps if (p.get('topic') or '') == t])
                if tp: out.append(('BKCB6 ' + g.lower() if g != 'Business improvement districts' else 'BKCB6 business improvement districts', t or g, 'dir-cb6-' + slug(g) + '-' + slug(t or 'all'), tp))
    if app == 'bk':
        H = 'Brooklyn'
        bko = [p for p in offs if any(c.get('cd', '').startswith('3') and c.get('eds', 1) for c in OFF[p['official']].get('cbs', []))
               or OFF[p['official']].get('type') in ('citywide', 'statewide', 'ussenate') or p['official'] in ('bpbrooklyn', 'dagonzalez')]
        for name, f in LEVEL:
            ps = sorted([p for p in bko if f(OFF[p['official']])], key=okey)
            if ps: out.append(("Brooklyn's elected officials", name, 'dir-bk-officials-' + slug(name), ps))
    return out

common = []
BOARDS = [p for p in D['profiles'] if p.get('group') == 'Community boards']
for b in BORO:
    ps = sorted([p for p in BOARDS if p.get('where') == b], key=lambda p: p.get('sort') or int(str(p.get('cd', '0'))[1:] or 0))
    if ps: common.append(('Community boards', b, 'dir-boards-' + slug(b), ps))
for i, (name, f) in enumerate(LEVEL):
    ps = sorted([p for p in offs if f(OFF[p['official']])], key=okey)
    if ps: common.append(('Elected officials', name, 'dir-officials-' + slug(name), ps))
common.append(('Government agencies', 'New York City', 'dir-agencies-nyc', byname([p for p in ag if not p['slug'].startswith('nys-')])))
common.append(('Government agencies', 'New York State', 'dir-agencies-nys', byname([p for p in ag if p['slug'].startswith('nys-')])))
# culture: Broadway theatres, stadiums and arenas, museums and movie theaters (culture_profiles.py)
CULT = [p for p in D['profiles'] if p.get('group') == 'Culture' or p.get('culture')]
ctop = lambda p: p.get('culture') or p.get('topic')
for t in ('Broadway theatres', 'Stadiums and arenas'):
    ps = byname([p for p in CULT if ctop(p) == t])
    if ps: common.append(('Theatres, museums, stadiums and movie theaters', t, 'dir-cul-' + slug(t), ps))
for t in ('Museums', 'Movie theaters'):
    for b in BORO:
        ps = byname([p for p in CULT if ctop(p) == t and (p.get('culture_where') or p.get('where')) == b])
        if ps: common.append(('Theatres, museums, stadiums and movie theaters', '%s, %s' % (t, b), 'dir-cul-' + slug(t) + '-' + slug(b), ps))
# hospitals, by borough (hospital_profiles.py)
for b in BORO:
    ps = byname([p for p in D['profiles'] if (p.get('group') == 'Health' and p.get('topic') == 'Hospitals' and p.get('where') == b) or (p.get('hospital') and p.get('hospital_where') == b)])
    if ps: common.append(('Hospitals', b, 'dir-hosp-' + slug(b), ps))
# pharmacies and supermarkets, by borough (store_profiles.py)
for head, g, pre in (('Pharmacies', 'Health', 'dir-rx-'), ('Supermarkets', 'Food', 'dir-mkt-')):
    for b in BORO:
        ps = byname([p for p in D['profiles'] if p.get('group') == g and p.get('topic') == head and p.get('where') == b])
        if ps: common.append((head, b, pre + slug(b), ps))
# libraries, by system (edu_library_profiles.py)
for t in ('Brooklyn Public Library', 'New York Public Library', 'Queens Public Library'):
    ps = byname([p for p in D['profiles'] if p.get('group') == 'Libraries' and p.get('topic') == t])
    if ps: common.append(('Libraries', t, 'dir-lib-' + slug(t), ps))
# the school and child care finder: by age and level, citywide; the app narrows each to a borough, then a neighborhood
def _levels(p):
    """the levels a school teaches, from its grades, else its type"""
    kv = dict(p.get('kv') or []); g = kv.get('Grades', ''); t = (kv.get('Type', '') + ' ' + (p.get('topic') or '')).lower()
    gs = set(x.strip() for x in g.split(','))
    out = set()
    if gs & {'Pre-K'}: out.add('pk')
    if gs & {'K', '1', '2', '3', '4', '5'}: out.add('el')
    if gs & {'6', '7', '8'}: out.add('ms')
    if gs & {'9', '10', '11', '12'}: out.add('hs')
    if not (gs - {'', 'special education'}):
        if 'elementary' in t or 'k-8' in t or 'k-12' in t: out.add('el')
        if 'middle' in t or 'k-8' in t or 'secondary' in t or 'k-12' in t: out.add('ms')
        if 'high school' in t and 'equivalency' not in t or 'secondary' in t or 'k-12' in t: out.add('hs')
        if 'early childhood' in t: out.add('pk')
    if 'special education' in t or 'disabilities' in t: out.add('sped')
    if 'equivalency' in t: out.add('hse')
    return out
_SCH = [p for p in D['profiles'] if p.get('group') == 'Schools']
_LV = {p['slug']: _levels(p) for p in _SCH}
_CC = lambda k: [p for p in D['profiles'] if p.get('group') == 'Child care' and p.get('cckind') == k]
FINDER = [('Infants and toddlers, ages 0 to 2 (child care)', 'infants', _CC('Infants and toddlers')),
          ('Preschool child care, ages 2 to 5', 'preschool', _CC('Preschool child care')),
          ('Pre-K, age 4 (schools and Pre-K sites)', 'prek', _CC('Pre-K site') + [p for p in _SCH if 'pk' in _LV[p['slug']]]),
          ('Preschools for students with disabilities', 'swd-preschool', _CC('Preschool for students with disabilities')),
          ('Elementary school, K to 5', 'elementary', [p for p in _SCH if 'el' in _LV[p['slug']]]),
          ('Middle school, 6 to 8', 'middle', [p for p in _SCH if 'ms' in _LV[p['slug']]]),
          ('High school, 9 to 12', 'high', [p for p in _SCH if 'hs' in _LV[p['slug']]]),
          ('Special education schools', 'special-education', [p for p in _SCH if 'sped' in _LV[p['slug']]]),
          ('High school equivalency programs', 'hse', [p for p in _SCH if 'hse' in _LV[p['slug']]]),
          ('Day camps (child care permits)', 'day-camps', _CC('Day camp'))]
for label, key, ps in FINDER:
    if ps: common.append(('Schools and child care by age', label, 'dir-edu-' + key, byname(ps)))
# things to do in parks: every activity, then (in the app) a borough, then a neighborhood (park_profiles.py)
_ACT = json.load(open(P('data/park-activities.json'))) if os.path.exists(P('data/park-activities.json')) else {}
for code, label in sorted(_ACT.items(), key=lambda kv: kv[1]):
    ps = byname([p for p in D['profiles'] if code in (p.get('acts') or [])])
    if ps: common.append(('Things to do in parks', label, 'dir-act-' + code.lower(), ps))
# the community-based organizations: by borough, then by policy area
CATS = [c for c, _ in sorted(__import__('collections').Counter(cat(p) for p in cbo).items(), key=lambda kv: -kv[1]) if c]
for b in BORO + ['Outside NYC', '']:
    for c in CATS:
        ps = byname([p for p in cbo if (p.get('where') or '') == b and cat(p) == c])
        if ps: common.append(('Community-based organizations, ' + (b or 'no address listed'), c, 'dir-cbo-' + slug(b or 'no-address') + '-' + slug(c), ps))
# one tile per place: the same place listed by more than one source shows once, as its fullest profile (directory_dedupe.py)
import importlib.util as _iu
_sp = _iu.spec_from_file_location('directory_dedupe', P('scripts/directory_dedupe.py')); _dd = _iu.module_from_spec(_sp); _sp.loader.exec_module(_dd)
CANON = _dd.canon(D['profiles']); _BYS = {p['slug']: p for p in D['profiles']}
def dedupe(ps):
    seen, out = set(), []
    for p in ps:
        q = _BYS.get(CANON.get(p['slug'], p['slug']), p)
        if q['slug'] in seen: continue
        seen.add(q['slug']); out.append(q)
    return out
total = 0
for app in ('cb6', 'bk', 'beyond'):
    cm = common
    if app in ('cb6', 'bk'):
        bd = [x for x in cm if x[2].startswith('dir-boards-')]
        bd = sorted(bd, key=lambda x: x[2] != 'dir-boards-brooklyn')
        it = iter(bd); cm = [next(it) if x[2].startswith('dir-boards-') else x for x in cm]   # Brooklyn's community-based organizations first in the Brooklyn apps
        bkc = [x for x in cm if x[0] == 'Community-based organizations, Brooklyn']
        rest = [x for x in cm if x not in bkc]
        k = next(i for i, x in enumerate(rest) if x[0].startswith('Community-based organizations'))
        cm = rest[:k] + bkc + rest[k:]
    k = next(i for i, x in enumerate(cm) if x[0].startswith('Community-based organizations'))
    first = ['15', '13', '14', '16', '17', '18', '19', '20', '21', '22', '23', '32'] if app in ('cb6', 'bk') else []
    cm = cm[:k] + school_sections(first) + cm[k:]
    sections = [(h, t, l, dedupe(ps)) for h, t, l, ps in area_sections(app) + cm]
    sections = [x for x in sections if x[3]]
    total = max(total, sum(len(x[3]) for x in sections))
    tf = P('app/data/civic/ui', app, 'tools.json'); T = json.load(open(tf, encoding='utf-8'))
    T['lists'] = {k: v for k, v in T['lists'].items() if not k.startswith('dir-')}
    heads = []
    for head, title, lid, ps in sections:
        def tl(p):
            t = tile(p)
            cd = str(p.get('cd') or '')
            if p.get('group') == 'Community boards' and cd and (app == 'beyond' or (app == 'bk' and cd.startswith('3'))):
                t['dest'] = 'screen:board:' + cd   # the app's own board page
            return t
        T['lists'][lid] = [tl(p) for p in ps]
        if len(ps) == 1 and title == ps[0]['name']:
            sec = tl(ps[0])   # a heading with one member shows that member itself
        else:
            sec = {'title': '%s · %s' % (title, '{:,}'.format(len(ps))), 'symbol': 'square.grid.2x2.fill', 'dest': 'screen:tools:' + lid, 'cover': cover_cat(head, title)}
        hid = 'dir-sections-' + slug(head)
        T['lists'].setdefault(hid, []).append(sec)
        if hid not in heads: heads.append(hid)
    traw = open(tf, encoding='utf-8').read()
    tind = len(re.match(r'\{\n( *)', traw).group(1)) if traw.startswith('{\n') else None
    open(tf, 'w', encoding='utf-8').write(json.dumps(T, ensure_ascii=False, indent=tind) + ('\n' if traw.endswith('\n') else ''))
    sf = P('app/data/civic/ui', app, 'screens.json'); raw = open(sf, encoding='utf-8').read(); S = json.loads(raw)
    S.setdefault('titles', {})
    for head, title, lid, ps in sections:
        S['titles'][lid] = {'title': title, 'subtitle': '%s · %s on the Directory' % (head, '{:,}'.format(len(ps)))}
    parts = [p for p in S['screens']['directory'] if not str(p.get('list', '')).startswith('dir-sections-') and p.get('gen') != 'dir']
    i = next((k + 1 for k, p in enumerate(parts) if p.get('id') == 'survey-button'), 0)
    new = []
    for hid in heads:
        head = next(h for h, t, l, ps in sections if 'dir-sections-' + slug(h) == hid)
        new.append({'kind': 'tools', 'list': hid, 'title': head})
    S['screens']['directory'] = parts[:i] + new + parts[i:]
    ind = len(re.match(r'\{\n( *)', raw).group(1)) if raw.startswith('{\n') else None
    open(sf, 'w', encoding='utf-8').write(json.dumps(S, ensure_ascii=False, indent=ind) + ('\n' if raw.endswith('\n') else ''))
# covers no list uses any more come off
used = set()
for app in ('cb6', 'bk', 'beyond'):
    for k, v in json.load(open(P('app/data/civic/ui', app, 'tools.json')))['lists'].items():
        for b in v: used.add(b.get('cover')); used.add(b.get('tile'))
for f in os.listdir(ICONS):
    if f.startswith('dir-') and f.rsplit('.', 1)[0] not in used: os.remove(os.path.join(ICONS, f))
print('covers:', len([f for f in os.listdir(ICONS) if f.startswith('dir-')]))
# the profiles now pointing at their tile pictures; the logo copies they no longer use come off
open(P('app/data/civic/orgs/orgs-profiles.json'), 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
keep = {p.get('logo') for p in D['profiles']}
gone = 0
for f in os.listdir(P('app/data/civic/orgs/logos')):
    if f.startswith(('sch-', 'cbo-', 'cul-', 'hosp-', 'rx-', 'mkt-')) and f not in keep: os.remove(P('app/data/civic/orgs/logos', f)); gone += 1
print('logo copies removed:', gone)
print('sections (CBNYC):', len(sections), '| tiles:', total, '| profiles in the Directory file:', len(D['profiles']))
# the screen's layout: dropdowns, compact logo grids and the map (app_directory_layout.py)
import runpy; runpy.run_path(P('scripts/app_directory_layout.py'), run_name='__main__')
# the Directory inside every board and legislative district (directory_in_district.py)
runpy.run_path(P('scripts/directory_in_district.py'), run_name='__main__')
# the Directory on the site, from the same entries (directory_web.py)
import subprocess, sys
subprocess.run([sys.executable, P('scripts/directory_web.py')], check=True)
# the logos as small tiles in the approved app builds (app_directory_tilekey.py)
subprocess.run([sys.executable, P('scripts/app_directory_tilekey.py')], check=True)
