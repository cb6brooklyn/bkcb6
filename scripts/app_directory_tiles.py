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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
D = json.load(open(P('app/data/civic/orgs/orgs-profiles.json'), encoding='utf-8'))
OFF = {o['slug']: o for o in json.load(open(P('app/data/civic/officials.json'), encoding='utf-8'))}
LOGOS = set(os.listdir(P('app/data/civic/orgs/logos')))
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

import shutil
def tile(p):
    t = {'title': p['name'], 'symbol': 'building.2.fill'}
    if p.get('kind') == 'official' and p.get('official') in OFF:
        # an official's own logo (civic/officials/<slug>.png), copied beside the org logos the tiles read
        src = P('app/data/civic/officials', p['official'] + '.png'); dst = 'off-%s.png' % p['official']
        if os.path.exists(src):
            if dst not in LOGOS: shutil.copy(src, P('app/data/civic/orgs/logos', dst)); LOGOS.add(dst)
            t['org'] = dst
    elif p.get('logo') in LOGOS: t['org'] = p['logo']
    t['dest'] = ('official:' + p['official']) if p.get('kind') == 'official' and p.get('official') in OFF else 'org:' + p['slug']
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

def area_sections(app):
    """The app's own area first: BKCB6 is CB6's, BKCB is Brooklyn's; CBNYC is the whole city."""
    out = []
    if app == 'cb6':
        H = 'BKCB6'
        cb6o = [p for p in offs if in_cd(OFF[p['official']], '306') or OFF[p['official']].get('type') in ('citywide', 'statewide', 'ussenate') or p['official'] in ('bpbrooklyn', 'dagonzalez')]
        out.append((H, "BKCB6's elected officials", 'dir-cb6-officials', sorted(cb6o, key=lambda p: (lvl(p), okey(p)))))
        out.append((H, 'BKCB6 community groups', 'dir-cb6-groups', byname([p for p in D['profiles'] if p['group'] == 'Community groups' and local(p)]
                                                                            + [p for p in cbo if 'cb6' in (p.get('scope') or '')])))
        out.append((H, 'BKCB6 government offices', 'dir-cb6-agencies', byname([p for p in ag if os.path.exists(P(p['slug'], 'index.html'))])))
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
        out.append((H, "Brooklyn's elected officials", 'dir-bk-officials', sorted(bko, key=lambda p: (lvl(p), okey(p)))))
    return out

common = []
for i, (name, f) in enumerate(LEVEL):
    ps = sorted([p for p in offs if f(OFF[p['official']])], key=okey)
    if ps: common.append(('Elected officials', name, 'dir-officials-' + slug(name), ps))
common.append(('Government agencies', 'New York City', 'dir-agencies-nyc', byname([p for p in ag if not p['slug'].startswith('nys-')])))
common.append(('Government agencies', 'New York State', 'dir-agencies-nys', byname([p for p in ag if p['slug'].startswith('nys-')])))
# the community-based organizations: by borough, then by policy area
CATS = [c for c, _ in sorted(__import__('collections').Counter(cat(p) for p in cbo).items(), key=lambda kv: -kv[1]) if c]
for b in BORO + ['Outside NYC', '']:
    for c in CATS:
        ps = byname([p for p in cbo if (p.get('where') or '') == b and cat(p) == c])
        if ps: common.append(('Community-based organizations, ' + (b or 'no address listed'), c, 'dir-cbo-' + slug(b or 'no-address') + '-' + slug(c), ps))
total = 0
for app in ('cb6', 'bk', 'beyond'):
    cm = common
    if app in ('cb6', 'bk'):   # Brooklyn's community-based organizations first in the Brooklyn apps
        bkc = [x for x in common if x[0] == 'Community-based organizations, Brooklyn']
        rest = [x for x in common if x not in bkc]
        k = next(i for i, x in enumerate(rest) if x[0].startswith('Community-based organizations'))
        cm = rest[:k] + bkc + rest[k:]
    sections = area_sections(app) + cm
    total = max(total, sum(len(x[3]) for x in sections))
    tf = P('app/data/civic/ui', app, 'tools.json'); T = json.load(open(tf, encoding='utf-8'))
    T['lists'] = {k: v for k, v in T['lists'].items() if not k.startswith('dir-')}
    heads = []
    for head, title, lid, ps in sections:
        T['lists'][lid] = [tile(p) for p in ps]
        cover = next((tile(p)['org'] for p in ps if tile(p).get('org')), None)
        sec = {'title': '%s · %s' % (title, '{:,}'.format(len(ps))), 'symbol': 'square.grid.2x2.fill', 'dest': 'screen:tools:' + lid}
        if cover: sec['org'] = cover
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
    parts = [p for p in S['screens']['directory'] if not str(p.get('list', '')).startswith('dir-sections-')]
    i = next((k + 1 for k, p in enumerate(parts) if p.get('id') == 'survey-button'), 0)
    new = []
    for hid in heads:
        head = next(h for h, t, l, ps in sections if 'dir-sections-' + slug(h) == hid)
        new.append({'kind': 'tools', 'list': hid, 'title': head})
    S['screens']['directory'] = parts[:i] + new + parts[i:]
    ind = len(re.match(r'\{\n( *)', raw).group(1)) if raw.startswith('{\n') else None
    open(sf, 'w', encoding='utf-8').write(json.dumps(S, ensure_ascii=False, indent=ind) + ('\n' if raw.endswith('\n') else ''))
print('sections (CBNYC):', len(sections), '| tiles:', total, '| profiles in the Directory file:', len(D['profiles']))
