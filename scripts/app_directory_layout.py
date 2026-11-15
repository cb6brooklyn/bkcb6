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
COLS = 3
GROUP = [('Schools by borough, ', 'Schools by borough'), ('Community-based organizations, ', 'Community-based organizations')]

NARROW = 48          # a category longer than this is narrowed: by borough, then by neighborhood
NOCOUNT = {'Things to do in parks'}   # its categories overlap (a park has several courts), so no total
BORDER = {'cb6': ['Brooklyn', 'Manhattan', 'Bronx', 'Queens', 'Staten Island'], 'bk': ['Brooklyn', 'Manhattan', 'Bronx', 'Queens', 'Staten Island'],
          'beyond': ['Manhattan', 'Bronx', 'Brooklyn', 'Queens', 'Staten Island']}
sl = lambda x: re.sub(r'[^a-z0-9]+', '-', x.lower()).strip('-')

def grid(app, lid, where=None, sort=None):
    return {'type': 'each', 'columns': COLS, 'spacing': 8,
            'data': dict({'file': 'civic/ui/%s/tools.json' % app, 'at': 'lists.' + lid}, **({'where': where} if where else {}), **({'sort': sort} if sort else {})),
            'item': {'type': 'v', 'spacing': 4, 'dest': '{dest}', 'maxWidth': 'full', 'align': 'top',
                     'children': [
                         {'type': 'image', 'tile': '{cover}', 'height': 96, 'maxWidth': 'full', 'align': 'center',
                          'bg': 'white', 'corner': 12, 'border': 'rule', 'borderWidth': 1, 'pad': 4},
                         {'type': 'text', 'text': '{title}', 'size': 10, 'weight': 'medium', 'lines': 2,
                          'textAlign': 'center', 'maxWidth': 'full', 'align': 'center'},
                         # its neighborhood, so a person can tell where each one is
                         {'type': 'text', 'text': '{h}', 'size': 9, 'color': 'muted', 'lines': 1, 'when': {'has': 'h'},
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
    import collections
    def hoods(lid, t, items, b, name):
        """Rows of the neighborhoods these entries are in, each opening its own grid."""
        kids = []
        hc = collections.Counter(x.get('h') or '' for x in items)
        for h in sorted(k for k in hc if k):
            nm = '%s--h-%s' % (name, sl(h))
            nodes[nm] = {'type': 'v', 'spacing': 10, 'title': '%s, %s' % (t, h), 'children': [grid(app, lid, dict({'h': h}, **({'b': b} if b else {})))]}
            kids.append(row('%s · %d' % (h, hc[h]), 'node:' + nm))
        if hc.get(''):
            nm = name + '--h-none'
            nodes[nm] = {'type': 'v', 'spacing': 10, 'title': t, 'children': [grid(app, lid, dict({'h': ''}, **({'b': b} if b is not None else {})))]}
            kids.append(row('No neighborhood on file · %d' % hc[''], 'node:' + nm))
        return kids
    for lid, items in T.items():
        if not lid.startswith('dir-') or lid.startswith('dir-sections-'): continue
        t = titles.get(lid, {}).get('title') or lid
        name = 'dirl-' + lid
        repl['tools:' + lid] = 'node:' + name
        if len(items) <= NARROW:
            nodes[name] = {'type': 'v', 'spacing': 10, 'title': t, 'children': [grid(app, lid)]}
            continue
        nodes[name + '--all'] = {'type': 'v', 'spacing': 10, 'title': t, 'children': [grid(app, lid)]}
        kids = [row('All %s, A to Z' % '{:,}'.format(len(items)), 'node:' + name + '--all')]
        bc = collections.Counter(x.get('b') or '' for x in items)
        real = [b for b in BORDER[app] if bc.get(b)]
        if len(real) > 1:
            kids.append(sub('Or pick a borough'))
            for b in real:
                sub_items = [x for x in items if (x.get('b') or '') == b]
                nm = '%s--b-%s' % (name, sl(b))
                if len(sub_items) <= NARROW:
                    nodes[nm] = {'type': 'v', 'spacing': 10, 'title': '%s, %s' % (t, b), 'children': [grid(app, lid, {'b': b}, 'h')]}   # neighbors together
                else:
                    nodes[nm + '--all'] = {'type': 'v', 'spacing': 10, 'title': '%s, %s' % (t, b), 'children': [grid(app, lid, {'b': b})]}
                    nodes[nm] = {'type': 'v', 'spacing': 8, 'title': '%s, %s' % (t, b), 'children':
                                 [row('All %s in %s' % ('{:,}'.format(len(sub_items)), b), 'node:' + nm + '--all'), sub('Or pick a neighborhood')] + hoods(lid, t, sub_items, b, nm)}
                kids.append(row('%s · %s' % (b, '{:,}'.format(len(sub_items))), 'node:' + nm))
            if bc.get(''):
                nm = name + '--b-none'
                nodes[nm] = {'type': 'v', 'spacing': 10, 'title': t, 'children': [grid(app, lid, {'b': ''})]}
                kids.append(row('No address on file · %s' % '{:,}'.format(bc['']), 'node:' + nm))
        else:
            kids.append(sub('Or pick a neighborhood'))
            kids += hoods(lid, t, items, None, name)
        nodes[name] = {'type': 'v', 'spacing': 8, 'title': t, 'children': kids}

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
                    'title': head if n == 1 or head in NOCOUNT else '%s · %s' % (head, '{:,}'.format(n)), **({'icon': 'logo:cb306'} if head == 'Brooklyn Community Board 6' else {}),
                    'node': {'type': 'v', 'spacing': 8, 'children': kids}})
    i = next((k + 1 for k, p in enumerate(keep) if p.get('id') == 'survey-button'), 0)
    S['screens']['directory'] = keep[:i] + new + keep[i:]
    nodes['dirmap'] = dirmap(app)
    # written compact: the narrowing screens make this a big file, and every phone downloads it
    open(sf, 'w', encoding='utf-8').write(json.dumps(S, ensure_ascii=False, separators=(',', ':')) + '\n')
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
            k = {'Community boards': 'boards', 'Elected officials': 'officials', 'Government agencies': 'agencies', 'Culture': 'culture', 'Parks': 'parks', 'Health': {'Pharmacies': 'pharmacies'}.get(p.get('topic'), 'hospitals'), 'Food': 'supermarkets'}.get(g)
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
        L += [layer('cb6-gov', 'BKCB6: board, officials and government', True), layer('cb6-groups', 'BKCB6 community groups', False),
              layer('cb6-schools', 'BKCB6 schools', False, 9000), layer('cb6-places', 'BKCB6 parks, libraries and facilities', False, 9000),
              layer('cb6-biz', 'BKCB6 local businesses', False, 4000, 30)]
    L += [layer('boards', 'Community boards', True), layer('officials', "Elected officials' offices", app != 'cb6'),
          layer('agencies', 'Government agencies', False, 20000), layer('culture', 'Theatres, museums, stadiums and movie theaters', False),
          layer('parks', 'Parks with courts and fields', False, 12000, 30), layer('hospitals', 'Hospitals', False),
          layer('pharmacies', 'Pharmacies', False, 8000, 30), layer('supermarkets', 'Supermarkets', False, 8000, 30)]
    for b in BORO + ['other']:
        for pre, t in (('schools-', 'Schools'), ('groups-', 'Community groups'), ('places-', 'Parks and facilities'), ('biz-', 'Businesses')):
            if pre + b in ks:
                L.append(layer(pre + b, '%s, %s' % (t, b if b != 'other' else 'outside NYC'), False, 8000, 30))
    L = [l for l in L if l['id'] in ks]
    center = {'cb6': ([40.676, -73.995], 9000), 'bk': ([40.650, -73.950], 30000), 'beyond': ([40.705, -73.950], 60000)}[app]
    m = {'type': 'map', 'height': 'full', 'corner': 0,
         'center': center[0], 'distance': center[1], 'search': True, 'searchScope': '306' if app == 'cb6' else ('3' if app == 'bk' else 'city'),
         'toggles': True, 'layers': L}
    # the layer switches sit under the map, clear of the tab bar; only the main ones start on, people turn on the rest
    return {'type': 'v', 'title': 'Map of the Directory', 'scroll': False, 'spacing': 0, 'children': [m, {'type': 'v', 'height': 96, 'children': []}]}

MAPKS = {a: mapfile(a) for a in ('cb6', 'bk', 'beyond')}
for a in ('cb6', 'bk', 'beyond'):
    print(a, 'sections:', build(a), '| map pins:', MAPKS[a][1], '| layers:', len(MAPKS[a][0]))
