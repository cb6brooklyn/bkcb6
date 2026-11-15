#!/usr/bin/env python3
"""A page on bkcb6.app for every Directory profile that has none: hospitals (/hospital/<slug>.html) and the parks with
courts and fields (/park-place/<slug>.html), in the Directory's profile format (build_org_pages.py, as /nyc-dep/):
logo, intro, the map with the place pinned, details, links. Each profile gets a "Full page" link to its page, which is
what the Directory's tiles open. Rerunnable. Run after hospital_profiles.py and park_profiles.py, before
app_directory_tiles.py."""
import json, os, re, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
E = lambda s: html.escape(str(s or ''), quote=False)
SRC = open(P('build_org_pages.py'), encoding='utf-8').read()
G = {'__file__': P('build_org_pages.py'), '__name__': 'profile_site_pages'}
exec(SRC[:SRC.index('for _f in (')], G)
LOOP = SRC[SRC.index('for o in ORGS:'):SRC.index('# One page per official')]
LOOP = LOOP.replace("d = os.path.join(ROOT, o['slug'])\n    os.makedirs(d, exist_ok=True)\n    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(html)",
                    "open(o['outfile'], 'w', encoding='utf-8').write(html)")
assert "o['outfile']" in LOOP
KINDS = [('hosp-', 'hospital', 'Health'), ('park-', 'park-place', 'Parks'), ('rx-', 'pharmacy', 'Health'), ('mkt-', 'supermarket', 'Food')]
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
made = 0
for pre, folder, crumb in KINDS:
    os.makedirs(P(folder), exist_ok=True)
    for old in os.listdir(P(folder)):
        if old.endswith('.html'): os.remove(P(folder, old))
    for p in D['profiles']:
        if not p['slug'].startswith(pre): continue
        name = re.sub(r'[^a-z0-9]+', '-', html.unescape(p['name']).lower()).strip('-')[:60]
        page = '%s-%s' % (name, p['slug'][len(pre):].lower()) if pre in ('hosp-', 'rx-', 'mkt-') else p['slug'][len(pre):]
        url = 'https://bkcb6.app/%s/%s' % (folder, page)
        p['links'] = [l for l in p.get('links', []) if l[0] != 'Full page']
        street, _, city = (p.get('addr') or '').partition(', ')
        lg = p.get('logo') or ''
        lgpath = ('/app/data/civic/icons/' + lg.split('/')[-1]) if lg.startswith('../../icons/') else ('/app/data/civic/orgs/logos/' + lg) if lg else ''
        if pre == 'park-' and not lgpath: lgpath = '/app/data/civic/orgs/logos/nycparks.png'
        o = {'slug': folder + '-' + page, 'outfile': P(folder, page + '.html'), 'unsigned': True, 'name': E(p['name']), 'title': E(p['name']),
             'seat': E(p.get('seat', '')).replace(' · ', ' &middot; '), 'desc': E(p.get('desc', '')), 'intro': [E(x) for x in p.get('intro', [])], 'does': [],
             'does_title': 'What it does', 'kv': [[E(k), E(v)] for k, v in p.get('kv', [])], 'links': [[E(a), b, False] for a, b in p['links']],
             'addr': E(street), 'zip': p.get('zip', ''), 'cityline': E(city) or ' ', 'addr_note': '', 'phone': p.get('phone', ''), 'tel': re.sub(r'\D', '', p.get('phone', '')),
             'email': '', 'web': p.get('web', ''), 'weburl': p.get('weburl', ''), 'since': ''}
        if p.get('lat') and p.get('lng'): o['lat'] = '%.6f' % p['lat']; o['lng'] = '%.6f' % p['lng']
        else: o['nomap'] = True; o['wherehtml'] = ''; o['lat'] = o['lng'] = ''
        if not lgpath: o['nologo'] = True
        G['ORGS'] = [o]
        exec(LOOP, G)
        t = open(o['outfile'], encoding='utf-8').read()
        t = t.replace('https://bkcb6.app/%s-%s"' % (folder, page), url + '"')
        if lgpath: t = t.replace('/site-icons/%s-%s.png' % (folder, page), lgpath)
        t = t.replace('<a href="/govhub.html" style="color:inherit">Government</a>', '<a href="/profiles/" style="color:inherit">Directory</a>', 1)
        t = t.replace('its boundary, the office, overlaps, land use', 'where it is, overlaps, land use')
        open(o['outfile'], 'w', encoding='utf-8').write(t)
        p['links'].append(['Full page', url])
        made += 1
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('site pages made:', made)
