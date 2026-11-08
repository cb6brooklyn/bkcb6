#!/usr/bin/env python3
"""bkcb6.app/profiles/: every profile in the directory as a logo tile, laid out like the Community-Based
Organizations grid on gowanus.html (#gowanus-cbos): square white tiles, 3 across (2 on a phone), the logo
contained in the tile. Flip through by group and topic, a page at a time (buttons or a swipe), or search.

Every profile in app/data/civic/orgs/orgs-profiles.json is a tile, plus every elected official in
app/data/civic/officials.json (their pages replace the 21 official entries in the directory file). A tile
links to the profile's page on bkcb6.app, or to the organization's own site when it has no page here. A profile
with no logo gets a tile with its name in the same box. Writes profiles/index.html and profiles/tiles.json.
Rerun after any profile script."""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
LOGOS = 'app/data/civic/orgs/logos/'
OFF_TOPIC = {'council': 'City Council', 'assembly': 'State Assembly', 'senate': 'State Senate', 'congress': 'Congress',
             'ussenate': 'U.S. Senate', 'statewide': 'Statewide', 'citywide': 'Citywide', 'bp': 'Borough Presidents',
             'da': 'District Attorneys'}
OFF_ORDER = ['Citywide', 'Statewide', 'U.S. Senate', 'Borough Presidents', 'District Attorneys', 'City Council',
             'State Assembly', 'State Senate', 'Congress']
SKIP_LINKS = ('/calendar', '/citywide-search', '/o/', '/park/rules', '/parks-policy', '/permits', '/transport-map')

idx = J('data/profile-index.json')

def site_page(p):
    for t, u in p.get('links', []):
        if t in ('Full profile', 'Profile and map', 'Full park profile', 'Full page') and u.startswith('https://bkcb6.app'):
            return u.replace('https://bkcb6.app', '')
    w = p.get('weburl') or ''
    if w.startswith('https://bkcb6.app'): return w.replace('https://bkcb6.app', '')
    nm = re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', html.unescape(p['name']).lower().replace("'", '').replace('&', ' and '))).strip('-')[:70]
    for cand in (p['slug'], p['slug'].replace('place-', '', 1), p['slug'].replace('health-', '', 1), 'biz-' + nm, p.get('official') or None,
                 'agencies/' + p['slug'], 'agencies/nys/' + p['slug'][4:] if p['slug'].startswith('nys-') else None):
        if cand and os.path.exists(os.path.join(ROOT, cand, 'index.html')): return '/' + cand + '/'
    for t, u in p.get('links', []):
        if u.startswith('https://bkcb6.app/') and not any(s in u for s in SKIP_LINKS): return u.replace('https://bkcb6.app', '')
    k = re.sub(r'^https?://(www1?\.)?', '', w).split('?')[0].rstrip('/').lower()
    k = re.sub(r'/index\.(page|html)$', '', k)
    if k and k in idx['urls']: return idx['urls'][k]
    return None

def main():
    d = J('app/data/civic/orgs/orgs-profiles.json')
    tiles = []
    for p in d['profiles']:
        if p.get('group') == 'Elected officials': continue
        href = site_page(p); ext = False
        if not href:
            href = p.get('weburl') or ''; ext = True
        if not href:
            print('no page and no site:', p['slug'], p['name']); continue
        logo = p.get('logo') or ''
        logo = ('/' + LOGOS + logo) if logo and os.path.exists(os.path.join(ROOT, LOGOS, logo)) else ''
        g = p.get('group') or 'Other'
        t = p.get('topic') or ''
        if g == 'Government agencies': t = 'New York State' if p['slug'].startswith('nys-') else 'New York City'
        tiles.append([p['name'], href, logo, g, t or g, 1 if ext else 0])
    for o in J('app/data/civic/officials.json'):
        icon = o.get('icon') or ''
        icon = icon if icon and os.path.exists(os.path.join(ROOT, icon.lstrip('/'))) else ''
        tiles.append([o['name'] + ' · ' + re.sub(r'\s*·.*', '', o.get('seat', '')), '/' + o['slug'] + '/', icon,
                      'Elected officials', OFF_TOPIC.get(o['type'], 'Elected officials'), 0])
    # an official whose icon is shared with another official (the State of New York and U.S. Senate cards) gets a name tile,
    # so each statewide official and each senator can be told apart
    import collections
    uses = collections.Counter(t[2] for t in tiles if t[2] and t[3] == 'Elected officials')
    for t in tiles:
        if t[3] == 'Elected officials' and t[2] and uses[t[2]] > 1: t[2] = ''
    groups = ['Elected officials', 'Government agencies', 'Community groups', 'Business improvement districts',
              'Schools, parks and facilities', 'Local businesses']
    groups += sorted({t[3] for t in tiles} - set(groups))
    topics = {}
    for g in groups:
        ts = sorted({t[4] for t in tiles if t[3] == g})
        if g == 'Elected officials': ts = [x for x in OFF_ORDER if x in ts] + [x for x in ts if x not in OFF_ORDER]
        if g == 'Government agencies': ts = ['New York City', 'New York State']
        topics[g] = ts
    tiles.sort(key=lambda t: (groups.index(t[3]), topics[t[3]].index(t[4]), re.sub(r'^the ', '', t[0].lower())))
    os.makedirs(os.path.join(ROOT, 'profiles'), exist_ok=True)
    data = {'groups': [{'name': g, 'topics': topics[g]} for g in groups],
            'tiles': [[t[0], t[1], t[2], groups.index(t[3]), topics[t[3]].index(t[4]), t[5]] for t in tiles]}
    json.dump(data, open(os.path.join(ROOT, 'profiles/tiles.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    page = open(os.path.join(ROOT, 'scripts/directory_grid.html'), encoding='utf-8').read()
    page = page.replace('__N__', f'{len(tiles):,}').replace('__V__', str(abs(hash(json.dumps(data))) % 10**8))
    open(os.path.join(ROOT, 'profiles/index.html'), 'w', encoding='utf-8').write(page)
    print(len(tiles), 'tiles;', sum(1 for t in tiles if t[2]), 'with logos;', sum(t[5] for t in tiles), 'link out')

if __name__ == '__main__':
    main()
