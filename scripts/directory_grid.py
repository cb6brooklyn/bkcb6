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
# each official's own logo (elected/), where there is one; the rest use their profile page icon
OWN_LOGO = {'repocasiocortez': '/elected/aoc.png', 'cmaviles': '/elected/aviles.png', 'dabragg': '/elected/bragg.png',
            'amcarroll': '/elected/carroll.png', 'daclark': '/elected/clark.png', 'repclarke': '/elected/clarke.png',
            'statecomptroller': '/elected/dinapoli.png', 'repespaillat': '/elected/espaillat.png', 'bpstatenisland': '/elected/fossella.png',
            'bpbronx': '/elected/gibson.png', 'ussengillibrand': '/elected/gillibrand.png', 'repgoldman': '/elected/goldman.png',
            'dagonzalez': '/elected/gonzalez.png', 'sengounardes': '/elected/gounardes.png', 'cmhanif': '/elected/hanif.png',
            'governor': '/elected/hochul.png', 'bpmanhattan': '/elected/hoylman.png', 'repjeffries': '/elected/jeffries.png',
            'dakatz': '/elected/katz.png', 'replatimer': '/elected/latimer.png', 'comptroller': '/elected/levine.png',
            'repmalliotakis': '/elected/malliotakis.png', 'mayor': '/elected/mamdani.png', 'damcmahon': '/elected/mcmahon.png',
            'repmeeks': '/elected/meeks.png', 'repmeng': '/elected/meng.png', 'ammitaynes': '/elected/mitaynes.png',
            'senmyrie': '/elected/myrie.png', 'repnadler': '/elected/nadler.png', 'bpbrooklyn': '/elected/reynoso.png',
            'bpqueens': '/elected/richards.png', 'ussenschumer': '/elected/schumer.png', 'amsimon': '/elected/simon.png',
            'repsuozzi': '/elected/suozzi.png', 'reptorres': '/elected/torres.png', 'repvelazquez': '/elected/velazquez.png',
            'publicadvocate': '/elected/williams.png', 'attorneygeneral': '/elected/tish-james.png', 'lieutenantgovernor': '/elected/delgado.png'}
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

# extra words each tile answers to in the directory search: district numbers and the short forms people type
KEYS = {'assembly': 'ad{n} ad {n} assembly district {n} assemblymember assemblyman assemblywoman',
        'council': 'cd{n} council district {n} cm councilmember councilman councilwoman',
        'senate': 'sd{n} sd {n} senate district {n} senator state senator',
        'congress': 'ny{n} ny-{n} ny {n} congressional district {n} congress member congressman congresswoman representative rep',
        'bp': 'bp borough president', 'da': 'da district attorney prosecutor', 'ussenate': 'us senator united states senate',
        'statewide': 'state of new york', 'citywide': 'city of new york nyc'}
BABBR = {'Manhattan': 'mn', 'Bronx': 'bx', 'Brooklyn': 'bk', 'Queens': 'qn', 'Staten Island': 'si'}

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
        nb = next((v for k, v in p.get('kv', []) if k == 'Neighborhood'), '')
        # the directory's organizations, places and businesses are CB6's (and so Brooklyn's)
        tiles.append([p['name'], href, logo, g, t or g, 1 if ext else 0, [nb] if nb else [], 0, '', 'cb6 bk'])
    BORO = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
    for o in J('app/data/civic/officials.json'):
        icon = OWN_LOGO.get(o['slug']) or o.get('icon') or ''
        icon = icon if icon and os.path.exists(os.path.join(ROOT, icon.lstrip('/'))) else ''
        boros = sorted({BORO[c['cd'][0]] for c in o.get('cbs', []) if c.get('eds', 1)}, key=list(BORO.values()).index)
        if o['type'] in ('citywide', 'statewide', 'ussenate'): boros = list(BORO.values())
        tiles.append([o['name'] + ' \u00b7 ' + re.sub(r'\s*\u00b7.*', '', o.get('seat', '')), '/' + o['slug'] + '/', icon,
                      'Elected officials', OFF_TOPIC.get(o['type'], 'Elected officials'), 0, boros, o.get('district') or 0,
                      o.get('seat', '') + ' ' + KEYS.get(o['type'], '').format(n=o.get('district') or ''),
                      ' '.join(x for x, ok in (('cb6', o['type'] in ('citywide', 'statewide', 'ussenate') or any(c.get('cd') == '306' and c.get('eds', 1) for c in o.get('cbs', []))
                                                     or (o['type'] in ('bp', 'da') and 'Brooklyn' in boros)),
                                               ('bk', 'Brooklyn' in boros)) if ok)])
    # the 59 community boards, by borough, each to its board page
    for b in J('app/data/civic/boards.json'):
        logo = f"/app/data/Logos/{b.get('logo') or 'cb' + b['borocd']}.png"
        logo = logo if os.path.exists(os.path.join(ROOT, logo.lstrip('/'))) else ''
        nn = int(b['borocd'][1:])
        tiles.append([b['name'], '/' + b['slug'] + '.html', logo, 'Community boards', b['borough'], 0, [b['borough']], nn,
                      'cb%d cb %d community district %d %s%d %s' % (nn, nn, nn, BABBR.get(b['borough'], ''), nn, b['borocd']),
                      ('cb6 ' if b['borocd'] == '306' else '') + ('bk' if b['borough'] == 'Brooklyn' else '')])
    groups = ['Elected officials', 'Community boards', 'Government agencies', 'Community groups', 'Business improvement districts',
              'Schools, parks and facilities', 'Local businesses']
    groups += sorted({t[3] for t in tiles} - set(groups))
    topics = {}
    for g in groups:
        ts = sorted({t[4] for t in tiles if t[3] == g})
        if g == 'Elected officials': ts = [x for x in OFF_ORDER if x in ts] + [x for x in ts if x not in OFF_ORDER]
        if g == 'Government agencies': ts = ['New York City', 'New York State']
        if g == 'Community boards': ts = [x for x in ['Manhattan', 'Bronx', 'Brooklyn', 'Queens', 'Staten Island'] if x in ts]
        topics[g] = ts
    tiles.sort(key=lambda t: (groups.index(t[3]), topics[t[3]].index(t[4]), t[7], re.sub(r'^the ', '', t[0].lower())))
    # where: boroughs for officials, neighborhoods for everything located in CB6
    BORDER = ['Manhattan', 'Bronx', 'Brooklyn', 'Queens', 'Staten Island']
    wheres = {}
    for g in groups:
        ws = {w for t in tiles if t[3] == g for w in t[6]}
        wheres[g] = [b for b in BORDER if b in ws] if g in ('Elected officials', 'Community boards') else sorted(ws, key=lambda w: (-sum(1 for t in tiles if t[3] == g and w in t[6]), w))
    os.makedirs(os.path.join(ROOT, 'profiles'), exist_ok=True)
    data = {'groups': [{'name': g, 'topics': topics[g], 'where': wheres[g], 'whereLabel': 'Borough' if g in ('Elected officials', 'Community boards') else 'Neighborhood'} for g in groups],
            'tiles': [[t[0], t[1], t[2], groups.index(t[3]), topics[t[3]].index(t[4]), t[5], [wheres[t[3]].index(w) for w in t[6]]]
                      + [(t[8] if len(t) > 8 else '').lower(), (t[9] if len(t) > 9 else '').strip()] for t in tiles]}
    json.dump(data, open(os.path.join(ROOT, 'profiles/tiles.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    page = open(os.path.join(ROOT, 'scripts/directory_grid.html'), encoding='utf-8').read()
    page = page.replace('__N__', f'{len(tiles):,}').replace('__V__', str(abs(hash(json.dumps(data))) % 10**8))
    open(os.path.join(ROOT, 'profiles/index.html'), 'w', encoding='utf-8').write(page)
    print(len(tiles), 'tiles;', sum(1 for t in tiles if t[2]), 'with logos;', sum(t[5] for t in tiles), 'link out')

if __name__ == '__main__':
    main()
