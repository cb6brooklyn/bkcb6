#!/usr/bin/env python3
"""Every business in the apps' Directory, and every liquor license holder in CB6, has a profile page on the site,
and the liquor license map's pins open them.

1. Liquor licenses (data/liquor_cb6.json: NYS Liquor Authority active licenses in CB6): each license is matched to the
   business it belongs to in the apps' Directory (same name within 80 m). The business's profile gets the license
   (type, number, status, issued, expires). A licensee with no Directory entry gets one (Local businesses).
2. Site pages: every Local businesses profile, and every other Directory place, that has no page on the site gets
   /biz/<slug>.html in the site's profile template: what it is, contact, details, the license, the place on a map and
   its precinct, sector and school district. The apps' profile links to it ("Profile and map").
3. The liquor license layer of the CB6 block maps (assets/blocks/cb6-layers.json) links each pin to its business.
Rerunnable: liquor-* app entries and /biz/ pages are rewritten.
"""
import html, json, os, re, sys, difflib, math
from shapely.geometry import Point
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
import importlib.util
spec = importlib.util.spec_from_file_location('dss', 'scripts/directory_safety_schools.py'); DSS = importlib.util.module_from_spec(spec); spec.loader.exec_module(DSS)
E = html.escape
PROF = 'app/data/civic/orgs/orgs-profiles.json'; LAY = 'assets/blocks/cb6-layers.json'
D = json.load(open(PROF)); LQ = json.load(open('data/liquor_cb6.json')); L = json.load(open(LAY))
cb6 = DSS.cb6

def slugify(s): return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', html.unescape(s).lower().replace("'", '').replace('&', ' and '))).strip('-')[:70]
def nn(s): return ' '.join(re.sub(r'\b(llc|inc|corp|co|ltd|the)\b', ' ', re.sub(r'[^a-z0-9 ]', ' ', s.lower().replace('&', 'and'))).split())
def dist(a, b, c, d): return math.hypot((a - c) * 111000, (b - d) * 84000)
def titlecase(s): return ' '.join(w.capitalize() if w.isupper() and len(w) > 2 else w for w in s.split())

def has_site_page(p):
    w = p.get('weburl') or ''
    if w.startswith('https://bkcb6.app/') and not w.startswith('https://bkcb6.app/biz/'): return w[len('https://bkcb6.app'):]
    for c in (p['slug'], p['slug'].replace('place-', '', 1), p['slug'].replace('health-', '', 1), 'biz-' + slugify(p['name']), p.get('official') or ''):
        if c and os.path.isfile(f'{c}/index.html'): return f'/{c}/'
    for l in p.get('links') or []:
        if l[1].startswith('https://bkcb6.app/') and not l[1].startswith('https://bkcb6.app/biz/') and l[0] in ('Profile and map', 'Full park profile', 'Profile', 'Sector page and map', 'Full page'):
            return l[1][len('https://bkcb6.app'):]
    return ''

BEV_TOPIC = {'Full Liquor': 'Restaurants, cafes and food', 'Wine & Beer': 'Restaurants, cafes and food', 'Grocery / Drug Store': 'Groceries and food stores',
             'Liquor / Wine Store': 'Stores', 'Brewery / Special': 'Trades, workshops and industrial', 'Wholesale / Temporary': 'Other businesses'}

def lic_rows(x):
    return [['License', x['detail'] if x['bev'].split(' ')[0].lower() in x['detail'].lower() else f'{x["detail"]} ({x["bev"]})'], ['License number', x['license_id']], ['License status', x['status']],
            ['Licensed since', x['issued']], ['License expires', x['expires']], ['Legal name', titlecase(x['legal_name'])]]

def main():
    biz = [p for p in D['profiles'] if p.get('lat') and p.get('lng') and not p['slug'].startswith('liquor-')]
    D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('liquor-')]
    by_key = {}
    new = []; matched = 0
    for x in LQ['records']:
        nm = x['dba'] or x['legal_name']
        best = None
        for p in biz:
            dd = dist(x['lat'], x['lon'], p['lat'], p['lng'])
            if dd > 80: continue
            r = max(difflib.SequenceMatcher(None, nn(nm), nn(p['name'])).ratio(), difflib.SequenceMatcher(None, nn(x['legal_name']), nn(p['name'])).ratio())
            if r >= 0.75 and (not best or r > best[0]): best = (r, p)
        if best:
            p = best[1]; matched += 1
            p.setdefault('_lic', []).append(x)
        else:
            key = (nn(nm), round(x['lat'], 4), round(x['lon'], 4))
            if key in by_key: by_key[key].setdefault('_lic', []).append(x); continue
            name = titlecase(nm)
            p = {'slug': 'liquor-' + slugify(name + ' ' + x['address']), 'name': name, 'seat': x['detail'], 'desc': f'{name}, {x["address"]}.',
                 'lat': x['lat'], 'lng': x['lon'], 'addr': titlecase(x['address']), 'zip': x['zip'], 'addr_note': '', 'phone': '', 'email': '',
                 'web': re.sub(r'^https?://(www\.)?', '', x.get('website') or '').rstrip('/'), 'weburl': x.get('website') or '', 'since': '',
                 'intro': [], 'does': [], 'kv': [], 'links': [], 'logo': '', 'cal': None, 'n': 0, 'going': [], 'kind': 'org', 'official': '',
                 'group': 'Local businesses', 'topic': BEV_TOPIC.get(x['bev'], 'Other businesses'), 'sort': 0, '_lic': [x]}
            p['type'] = p['slug']; by_key[key] = p; new.append(p)
    D['profiles'] += new
    # licenses into each business's details
    for p in D['profiles']:
        lic = p.pop('_lic', None)
        p['kv'] = [r for r in p.get('kv') or [] if not r[0].startswith(('License', 'Licensed since', 'Legal name'))]
        if lic:
            for x in sorted(lic, key=lambda x: x['issued']):
                p['kv'] += lic_rows(x)
            p['_lics'] = lic
            p['kv'] = [r for r in p['kv'] if r[0] != 'Liquor license']
    # site pages
    os.makedirs('biz', exist_ok=True)
    keep = set(); made = 0; used = set(); page_of = {}
    for p in D['profiles']:
        if not (p.get('lat') and p.get('lng')): continue
        if p.get('group') not in ('Local businesses', 'Schools, parks and facilities', 'Community groups', 'Business improvement districts'): continue
        sp = has_site_page(p)
        lics = p.pop('_lics', None)
        if sp:
            page_of[p['slug']] = sp
            if lics: page_of.update({x['license_id']: sp for x in lics})
            continue
        s = slugify(p['name'] + ' ' + (p.get('addr') or ''))
        k = 2
        while s in used: s = f'{s}-{k}'; k += 1
        used.add(s); path = f'/biz/{s}.html'; keep.add(f'{s}.html')
        open(path[1:], 'w').write(page(p, lics, path)); made += 1
        page_of[p['slug']] = path
        if lics: page_of.update({x['license_id']: path for x in lics})
        p['links'] = [l for l in p.get('links') or [] if l[0] != 'Profile and map'] + [['Profile and map', 'https://bkcb6.app' + path]]
    for p in D['profiles']: p.pop('_lics', None)
    json.dump(D, open(PROF, 'w'), ensure_ascii=False, indent=1)
    # liquor map pins -> the business
    lic_by = {}
    for x in LQ['records']: lic_by.setdefault((x['dba'] or x['legal_name']).lower(), []).append(x)
    lay = next(l for l in L['layers'] if l['id'] == 'liquor'); linked = 0
    for it in lay['items']: it['u'] = '/liquor/'
    for it in lay['items']:
        c = [x for x in lic_by.get(it['t'].lower(), []) if dist(it['y'], it['x'], x['lat'], x['lon']) < 30]
        if c and c[0]['license_id'] in page_of: it['u'] = page_of[c[0]['license_id']]; linked += 1
    # pins the license file doesn't have (older map records): the Directory business at that spot, or a page of their own
    extra = 0
    locs = [p for p in D['profiles'] if p.get('lat') and p.get('lng') and p['slug'] in page_of]
    for it in lay['items']:
        if it['u'] != '/liquor/': continue
        best = None
        for p in locs:
            dd = dist(it['y'], it['x'], p['lat'], p['lng'])
            if dd > 80: continue
            r = difflib.SequenceMatcher(None, nn(it['t']), nn(p['name'])).ratio()
            if r >= 0.75 and (not best or r > best[0]): best = (r, p)
        if best: it['u'] = page_of[best[1]['slug']]; linked += 1; continue
        parts = [x.strip() for x in it['s'].split(',')]
        name = titlecase(it['t']); addr = titlecase(parts[0])
        q = {'slug': 'liquor-' + slugify(name + ' ' + addr), 'name': name, 'seat': parts[1] + ' liquor license' if len(parts) > 1 else 'Liquor license', 'lat': it['y'], 'lng': it['x'],
             'addr': addr, 'zip': '', 'phone': '', 'email': '', 'web': '', 'weburl': '', 'intro': [], 'does': [], 'logo': '',
             'kv': [['License', parts[1] if len(parts) > 1 else ''], ['License status', parts[2] if len(parts) > 2 else ''], ['Source', 'NYS Liquor Authority, on the CB6 liquor license map']]}
        sl = slugify(name + ' ' + addr); k = 2
        while sl in used: sl = f'{sl}-{k}'; k += 1
        used.add(sl); keep.add(sl + '.html'); path = f'/biz/{sl}.html'
        q['kv'] = [r for r in q['kv'] if r[1]]
        open(path[1:], 'w').write(page(q, None, path)); it['u'] = path; linked += 1; extra += 1; made += 1
    for f in os.listdir('biz'):
        if f not in keep: os.remove('biz/' + f)
    json.dump(L, open(LAY, 'w'), ensure_ascii=False, separators=(',', ':'))
    print(extra, 'pages for map-only licenses;', end=' ')
    print(len(LQ['records']), 'licenses;', matched, 'matched to Directory businesses;', len(new), 'new businesses;', made, 'new pages;', linked, 'of', len(lay['items']), 'liquor pins linked')

def page(p, lics, path):
    title = p['name']; seat = p.get('seat') or ''
    h = DSS.head(title, f'{title}, {seat}. Contact, details{", liquor license" if lics else ""}, and where it is in Brooklyn Community Board 6.', path)
    logo = f'/app/data/civic/orgs/logos/{p["logo"]}' if p.get('logo') and os.path.exists(f'app/data/civic/orgs/logos/{p["logo"]}') else ''
    h += ('  <div class="phead">\n    <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/directory/" style="color:inherit">Directory</a></div>\n'
          + (f'    <div class="olog" style="margin-top:8px"><img src="{logo}" alt="" style="border-radius:9px"><div class="otx"><h1 style="margin-top:0">{E(title)}</h1><div class="pseat">{E(seat)}</div></div></div>\n' if logo else
             f'    <h1>{E(title)}</h1>\n    <div class="pseat">{E(seat)}</div>\n') + '  </div>\n')
    txt = (p.get('intro') or []) + (p.get('does') or [])
    if txt: h += DSS.sec('What it is', ''.join(f'<p>{E(t)}</p>' for t in txt))
    contact = [('Address', E(((p.get('addr') or '') + (', Brooklyn, NY ' + p['zip'] if p.get('zip') else ', Brooklyn')) if p.get('addr') else '')),
               ('Phone', f'<a href="tel:{E(re.sub(r"[^0-9+]", "", p["phone"]))}">{E(p["phone"])}</a>' if p.get('phone') else ''),
               ('Email', f'<a href="mailto:{E(p["email"])}">{E(p["email"])}</a>' if p.get('email') else ''),
               ('Website', f'<a href="{E(p["weburl"])}" target="_blank" rel="noopener">{E(p.get("web") or p["weburl"])} &#8599;</a>' if p.get('weburl') and not p['weburl'].startswith('https://bkcb6.app') else '')]
    contact = [r for r in contact if r[1]]
    if contact: h += DSS.sec('Contact', DSS.kv(contact))
    det = [(k, E(v)) for k, v in p.get('kv') or [] if v and not k.startswith(('License', 'Licensed since', 'Legal name')) and k not in ('Source',)]
    if det: h += DSS.sec('Details', DSS.kv(det))
    if lics:
        body = ''.join(DSS.kv([(k, E(v)) for k, v in lic_rows(x) if v]) for x in sorted(lics, key=lambda x: x['issued']))
        h += DSS.sec('Liquor license' + ('s' if len(lics) > 1 else ''), body + '<div class="chips"><a class="chip" href="/liquor/">Every liquor license in CB6</a></div>'
                     '<p class="subnote">From the NYS Liquor Authority\'s active licenses (data.ny.gov), as of ' + E(LQ['retrieved'][:10]) + '.</p>')
    h += DSS.sec('Where it is', DSS.mapblock('cb', '306', p['lat'], p['lng'], p.get('addr') or title, 'the place and Brooklyn Community Board 6', zoom=17, fit=False))
    if cb6.buffer(0.002).contains(Point(p['lng'], p['lat'])):
        sd, pct, sec_ = DSS.where(p['lat'], p['lng'])
        rows = DSS.links_row({'sd': sd, 'pct': pct, 'sec': sec_})
        if rows: h += DSS.sec('Its precinct, sector and school district', DSS.kv(rows))
    src = next((v for k, v in p.get('kv') or [] if k == 'Source'), '')
    h += DSS.FOOT.format(src=E('Business details from ' + (src or 'the CB6 business directory')) + ('; liquor license from the NYS Liquor Authority' if lics else '') + '. Precinct, sector and school district from the NYC Open Data maps.')
    return h

if __name__ == '__main__':
    main()
