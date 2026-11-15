#!/usr/bin/env python3
"""The apps' Directory screen, compact: every section a closed dropdown (the stack of section headers is the table of
contents), small logo tiles four across inside, long categories as one-line rows that open their own logo grid, and a
map of everything in the Directory with each entry's logo as its pin. All from screens.json and the pack, no build.

Reads what app_directory_tiles.py wrote (tools.json dir-* lists, the directory screen's dir-sections parts) and rewrites
the directory screen's parts, the "dirl-*" nodes (a long category's grid), "dirmap" (the map), and "replace" so every
tools:dir-* list opens as the compact grid. Writes app/data/civic/directory-map/<app>.geojson. Rerunnable."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
INLINE = 12          # a category this size or smaller shows its logos inside the dropdown
COLS = 4
GROUP = [('Schools by borough, ', 'Schools by borough'), ('Community-based organizations, ', 'Community-based organizations')]

def grid(app, lid):
    return {'type': 'each', 'columns': COLS, 'spacing': 8,
            'data': {'file': 'civic/ui/%s/tools.json' % app, 'at': 'lists.' + lid},
            'item': {'type': 'v', 'spacing': 4, 'dest': '{dest}', 'maxWidth': 'full', 'align': 'top',
                     'children': [
                         {'type': 'image', 'tile': '{cover}', 'height': 40, 'maxWidth': 'full', 'align': 'center',
                          'bg': 'white', 'corner': 6, 'border': 'rule', 'borderWidth': 1, 'pad': 3},
                         {'type': 'text', 'text': '{title}', 'size': 10, 'weight': 'medium', 'lines': 2,
                          'textAlign': 'center', 'maxWidth': 'full', 'align': 'center'}]}}

def row(title, dest):
    return {'type': 'h', 'dest': dest, 'spacing': 8, 'pad': 10, 'bg': 'white', 'corner': 10,
            'border': 'rule', 'borderWidth': 1, 'maxWidth': 'full', 'align': 'center',
            'children': [{'type': 'text', 'text': title, 'size': 14, 'weight': 'bold', 'color': 'navy'},
                         {'type': 'spacer'},
                         {'type': 'symbol', 'name': 'chevron.right', 'size': 12, 'color': 'orange'}]}

def sub(text):
    return {'type': 'text', 'text': text, 'size': 11, 'mono': True, 'upper': True, 'tracking': 0.8, 'color': 'orange', 'top': 6}

def leaf_of(item):
    d = item.get('dest', '')
    return d[len('screen:tools:'):] if d.startswith('screen:tools:') else None

def build(app):
    tf = P('app/data/civic/ui', app, 'tools.json'); T = json.load(open(tf, encoding='utf-8'))['lists']
    sf = P('app/data/civic/ui', app, 'screens.json'); raw = open(sf, encoding='utf-8').read(); S = json.loads(raw)
    parts = S['screens']['directory']
    secs = [{'list': p['list'], 'title': p.get('title', '')} for p in parts if str(p.get('list', '')).startswith('dir-sections-')]
    if secs: S['dirSections'] = secs                      # kept so a rerun knows the sections and their order
    else: secs = [x for x in S.get('dirSections', []) if x['list'] in T]
    keep = [p for p in parts if not str(p.get('list', '')).startswith('dir-sections-') and p.get('gen') != 'dir']
    nodes = S.setdefault('nodes', {}); repl = S.setdefault('replace', {})
    for k in [k for k in nodes if k.startswith('dirl-')]: del nodes[k]
    for k in [k for k, v in repl.items() if k.startswith('tools:dir-') and str(v).startswith('node:dirl-')]: del repl[k]
    titles = S.get('titles', {})
    # every dir-* list opens as the compact grid
    for lid, items in T.items():
        if not lid.startswith('dir-') or lid.startswith('dir-sections-'): continue
        t = titles.get(lid, {}).get('title') or lid
        nodes['dirl-' + lid] = {'type': 'v', 'spacing': 10, 'title': t, 'children': [grid(app, lid)]}
        repl['tools:' + lid] = 'node:dirl-' + lid

    def content(sec):
        items = T[sec['list']]
        if not any(leaf_of(it) for it in items):    # a section of entries (BKCB6 itself): their logos
            return [grid(app, sec['list'])], len(items)
        kids, n = [], 0
        for it in items:
            lid = leaf_of(it)
            if not lid: continue
            cnt = len(T.get(lid, []))
            n += cnt
            if cnt <= INLINE: kids += [sub(it['title']), grid(app, lid)]
            else: kids.append(row(it['title'], 'node:dirl-' + lid))
        return kids, n

    folds, grouped = [], {}
    for sec in secs:
        head = sec.get('title', '')
        g = next((g for pre, g in GROUP if head.startswith(pre)), None)
        kids, n = content(sec)
        if g:
            if g not in grouped:
                grouped[g] = {'kids': [], 'n': 0}
                folds.append(('group', g))
            grouped[g]['kids'] += [sub(head.split(', ', 1)[1])] + kids
            grouped[g]['n'] += n
        else:
            folds.append(('one', (head, kids, n)))
    new = [{'gen': 'dir', 'kind': 'button', 'title': 'Map of the Directory', 'dest': 'node:dirmap', 'color': '#06024d', 'id': 'dir-map-button'}]
    for kind, v in folds:
        if kind == 'group':
            head, kids, n = v, grouped[v]['kids'], grouped[v]['n']
        else:
            head, kids, n = v
        new.append({'gen': 'dir', 'kind': 'node', 'fold': True, 'open': False, 'id': 'dir-' + re.sub(r'[^a-z0-9]+', '-', head.lower()).strip('-'),
                    'title': head if n == 1 else '%s · %s' % (head, '{:,}'.format(n)), **({'icon': 'logo:cb306'} if head == 'Brooklyn Community Board 6' else {}),
                    'node': {'type': 'v', 'spacing': 8, 'children': kids}})
    i = next((k + 1 for k, p in enumerate(keep) if p.get('id') == 'survey-button'), 0)
    S['screens']['directory'] = keep[:i] + new + keep[i:]
    nodes['dirmap'] = dirmap(app)
    ind = len(re.match(r'\{\n( *)', raw).group(1)) if raw.startswith('{\n') else None
    open(sf, 'w', encoding='utf-8').write(json.dumps(S, ensure_ascii=False, indent=ind) + ('\n' if raw.endswith('\n') else ''))
    return len(new) - 1

# ---- the map ----
D = json.load(open(P('app/data/civic/orgs/orgs-profiles.json'), encoding='utf-8'))['profiles']
BORO = ['Brooklyn', 'Manhattan', 'Bronx', 'Queens', 'Staten Island']

def mapfile(app):
    T = json.load(open(P('app/data/civic/ui', app, 'tools.json'), encoding='utf-8'))['lists']
    cover, cb6 = {}, set()
    for lid, items in T.items():
        if not lid.startswith('dir-') or lid.startswith('dir-sections-'): continue
        for it in items:
            cover.setdefault(it['dest'], it['cover'])
            if lid.startswith('dir-cb6-') and app == 'cb6': cb6.add(it['dest'])
    feats = []
    for p in D:
        if p.get('lat') is None or p.get('lng') is None: continue
        dest = ('official:' + p['official']) if p.get('kind') == 'official' and p.get('official') else 'org:' + p['slug']
        if dest not in cover:
            alt = [d for d in cover if d.endswith(':' + p['slug'])]
            if alt: dest = alt[0]
            else: continue
        g = p.get('group') or ''
        if dest in cb6:
            k = {'Local businesses': 'cb6-biz', 'Community groups': 'cb6-groups', 'Schools': 'cb6-schools',
                 'Schools, parks and facilities': 'cb6-places', 'Business improvement districts': 'cb6-groups'}.get(g, 'cb6-gov')
        else:
            b = p.get('where') if p.get('where') in BORO else 'other'
            k = {'Community boards': 'boards', 'Elected officials': 'officials', 'Government agencies': 'agencies'}.get(g)
            if not k:
                k = {'Schools': 'schools-', 'Community groups': 'groups-', 'Local businesses': 'biz-',
                     'Schools, parks and facilities': 'places-', 'Business improvement districts': 'groups-'}.get(g, 'groups-') + b
        feats.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [round(p['lng'], 6), round(p['lat'], 6)]},
                      'properties': {'k': k, 'c': cover[dest], 'd': dest}})
    os.makedirs(P('app/data/civic/directory-map'), exist_ok=True)
    json.dump({'type': 'FeatureCollection', 'features': feats}, open(P('app/data/civic/directory-map', app + '.geojson'), 'w'), separators=(',', ':'))
    return {f['properties']['k'] for f in feats}, len(feats)

def dirmap(app):
    ks, n = MAPKS[app]
    pin = lambda size: {'style': 'image', 'image': 'civic/icons/{c}.png', 'size': size, 'corner': 4}
    def layer(k, title, on, maxd=None, size=34):
        l = {'id': k, 'title': title, 'on': on, 'file': 'civic/directory-map/%s.geojson' % app, 'where': {'k': k}, 'pin': pin(size), 'dest': '{d}'}
        if maxd: l['maxDistance'] = maxd
        return l
    L = []
    if app == 'cb6':
        L += [layer('cb6-gov', 'BKCB6: board, officials and government', True), layer('cb6-groups', 'BKCB6 community groups', True),
              layer('cb6-schools', 'BKCB6 schools', True, 9000), layer('cb6-places', 'BKCB6 parks, libraries and facilities', True, 9000),
              layer('cb6-biz', 'BKCB6 local businesses', False, 4000, 30)]
    L += [layer('boards', 'Community boards', True), layer('officials', "Elected officials' offices", app != 'cb6'),
          layer('agencies', 'Government agencies', False, 20000)]
    for b in BORO + ['other']:
        for pre, t in (('schools-', 'Schools'), ('groups-', 'Community groups'), ('places-', 'Parks and facilities'), ('biz-', 'Businesses')):
            if pre + b in ks:
                L.append(layer(pre + b, '%s, %s' % (t, b if b != 'other' else 'outside NYC'), False, 8000, 30))
    L = [l for l in L if l['id'] in ks]
    center = {'cb6': ([40.676, -73.995], 9000), 'bk': ([40.650, -73.950], 30000), 'beyond': ([40.705, -73.950], 60000)}[app]
    return {'type': 'map', 'title': 'Map of the Directory', 'scroll': False, 'height': 'full', 'corner': 0,
            'center': center[0], 'distance': center[1], 'search': True, 'searchScope': '306' if app == 'cb6' else ('3' if app == 'bk' else 'city'),
            'toggles': True, 'layers': L}

MAPKS = {a: mapfile(a) for a in ('cb6', 'bk', 'beyond')}
for a in ('cb6', 'bk', 'beyond'):
    print(a, 'sections:', build(a), '| map pins:', MAPKS[a][1], '| layers:', len(MAPKS[a][0]))
