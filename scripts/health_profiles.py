"""A profile for every health care location on the CB6 maps: the block maps' Health services layer (assets/blocks/cb6-layers.json,
from OpenStreetMap) and the Facilities Database health care sites in the apps' Directory. NewYork-Presbyterian Brooklyn
Methodist Hospital and Cobble Hill Health Center have hand-written profiles of their own (data/org-profiles-cal.json).

Reads data/health-locations.json (one record per location: name, kind, specialties, address, phone, website, operator, the
Facilities Database listing, logo, and the map pin it belongs to). Writes:
  data/health-profiles.json                  the site's profile pages (build_org_pages.py builds /<slug>/ from it)
  app/data/civic/orgs/orgs-profiles.json     the apps' Directory: each location's profile, replacing the thinner OpenStreetMap
                                             and Facilities Database copies of the same place (rerunnable: its own health-* entries
                                             are replaced)
  assets/blocks/cb6-layers.json              each Health services map pin links to its profile
Logos: site-icons/<slug>.png (site) and app/data/civic/orgs/logos/health-<slug>.png (apps)."""
import json, html, re, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
LOC = json.load(open('data/health-locations.json'))
import sys
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from vaccine_links import link_file
VAX = link_file()   # each NYC Health Map vaccine site linked to its profile; slug -> vaccines given there
HEALTHMAP = 'https://a816-health.nyc.gov/NYCHealthMap/ServiceCategory/Vaccines'
W = 'https://bkcb6.app'

def esc(s): return html.escape(s or '', quote=False)
def tel(p): return re.sub(r'\D', '', p or '')[-10:]

def cb_link(cd):
    n = int(str(cd)[1:])
    return f'<a href="/cb-bk-{n}.html">Brooklyn Community Board {n}</a>', f'Brooklyn Community Board {n}'

def article(kind):
    return 'an' if kind[:1].lower() in 'aeiou' else 'a'

site, app_profiles = [], []
for r in LOC:
    slug, name, kind = r['slug'], r['name'], r['kind']
    hood = r.get('hood') or ''
    cbh, cbt = cb_link(r['cd'])
    where = f" in {hood}" if hood else ''
    if r.get('person'):
        intro = [f"<b>{esc(name)}</b> sees patients at <b>{esc(r['address'])}</b>{esc(where)}."]
    else:
        intro = [f"<b>{esc(name)}</b> is {article(kind)} {esc(kind.lower())} at <b>{esc(r['address'])}</b>{esc(where)}."]
    if r.get('operator'):
        op = esc(r['operator'])
        if 'Brooklyn Methodist Hospital' in op:
            op = op.replace('NewYork-Presbyterian Brooklyn Methodist Hospital', '<a href="/nyp-brooklyn-methodist-hospital/">NewYork-Presbyterian Brooklyn Methodist Hospital</a>')
        intro.append(f"Run by {op}.")
    does = []
    for f in r.get('fac') or []:
        line = f"The New York State Department of Health lists {esc(f['name'])} here as {article(f['type'])} {esc(f['type'].lower())}"
        line += (f", with {esc(f['capacity'])}." if f.get('capacity') else '.')
        does.append(line)
    if r.get('note'):
        intro.append(esc(r['note']))
    kv = []
    if r.get('specialties'): kv.append(['Specialties', esc(', '.join(r['specialties']))])
    if VAX.get(slug):
        kv.append(['Vaccines', esc(', '.join(VAX[slug])) + f' &middot; <a href="{HEALTHMAP}" target="_blank" rel="noopener">NYC Health Map &#8599;</a>'])
    kv.append(['Community board', cbh])
    links = []
    if r.get('web'): links.append(['Their site', r['web'], True])
    links.append(['Zoning and land use for the lot', '/citywide-search.html?address=' + re.sub(r'\s', '%20', r['address'] + ', Brooklyn').replace(',', '%2C'), False])
    links.append(['Search an address', '/citywide-search.html', False])
    rec = {
        'slug': slug, 'unsigned': True, 'name': esc(name), 'seat': f"{esc(kind)} &middot; {esc(hood or 'Brooklyn')}, Brooklyn" if hood else f"{esc(kind)} &middot; Brooklyn",
        'title': esc(name), 'desc': f"{name}, {r['address']}{', ' + hood if hood else ''}. {kind}" + (f": {', '.join(r['specialties'])}" if r.get('specialties') else '') + '.',
        'lat': '%.6f' % r['lat'], 'lng': '%.6f' % r['lng'], 'addr': esc(r['address']), 'zip': r.get('zip') or '', 'addr_note': esc(r.get('addr_note') or ''),
        'cityline': '', 'phone': r.get('phone') or '', 'tel': tel(r.get('phone')), 'email': '', 'web': re.sub(r'^https?://(www\.)?', '', r.get('web') or '').split('/')[0],
        'weburl': r.get('web') or '', 'since': '', 'intro': [' '.join(intro)], 'does_title': 'The state listing', 'does': does, 'kv': kv, 'links': links,
    }
    if not r.get('logo'):
        rec['nologo'] = True
    if r.get('evorg'):
        rec.update(evorg=r['evorg'], evtitle=r['evtitle'], evhref=f"/o/{r['evorg']}.html", evname=r['evname'])
    site.append(rec)
    # the apps' Directory
    plain = lambda s: html.unescape(re.sub(r'<[^>]+>', '', s))
    a = {'slug': 'health-' + slug, 'type': 'health-' + slug, 'name': name,
         'seat': kind + (f' · {hood}' if hood else ''), 'desc': rec['desc'], 'lat': round(r['lat'], 6), 'lng': round(r['lng'], 6),
         'addr': r['address'], 'zip': r.get('zip') or '', 'addr_note': r.get('addr_note') or '', 'phone': r.get('phone') or '', 'email': '',
         'web': rec['web'], 'weburl': r.get('web') or '', 'since': '', 'intro': [plain(rec['intro'][0])], 'does': [plain(x) for x in does],
         'kv': [[k, plain(v)] for k, v in kv], 'links': [[l[0], l[1]] for l in links if l[2]], 'logo': ('health-%s.png' % slug) if r.get('logo') else '',
         'cal': r.get('appcal'), 'n': 0, 'going': [], 'kind': 'org', 'official': '',
         'group': r.get('group') or 'Schools, parks and facilities', 'topic': r.get('topic') or 'Hospitals and health care', 'sort': 0}
    app_profiles.append((a, r.get('replaces') or []))

json.dump(site, open('data/health-profiles.json', 'w'), ensure_ascii=False, indent=1)

P = 'app/data/civic/orgs/orgs-profiles.json'
d = json.load(open(P))
drop = {s for _, rep in app_profiles for s in rep}
keep = {p['slug'] for p in d['profiles'] if not p['slug'].startswith('health-') and p['slug'] not in drop}
# each new profile takes the place in the list of the first copy it replaces, so the Directory's order is kept
pos = {p['slug']: i for i, p in enumerate(d['profiles'])}
placed = []
for a, rep in app_profiles:
    at = min((pos[s] for s in rep + [a['slug']] if s in pos), default=len(d['profiles']))
    placed.append((at, a))
out, j = [], 0
placed.sort(key=lambda x: x[0])
for i, p in enumerate(d['profiles']):
    while j < len(placed) and placed[j][0] <= i:
        out.append(placed[j][1]); j += 1
    if p['slug'] in keep: out.append(p)
out += [a for _, a in placed[j:]]
d['profiles'] = out
json.dump(d, open(P, 'w'), ensure_ascii=False, indent=1)

# map pins link to the profiles
LP = 'assets/blocks/cb6-layers.json'
lay = json.load(open(LP))
for l in lay['layers']:
    if l['id'] != 'health': continue
    for r in LOC:
        for k in r.get('items') or []:
            l['items'][k]['u'] = f"/{r['slug']}/"
            if r.get('logo'): l['items'][k]['i'] = '/' + r['logo']
# the NYC Health Map's vaccine sites around CB6, as their own layer on the block maps (the block cards list the closest ones)
vdoc = json.load(open('data/vaccine-sites.json'))
box = (40.655, 40.695, -74.025, -73.96)
vitems = []
for v in vdoc['sites']:
    if not (box[0] < v['lat'] < box[1] and box[2] < v['lng'] < box[3]): continue
    it = {'x': v['lng'], 'y': v['lat'], 't': v['name'], 's': ', '.join(v.get('vaccines') or []) + ' · ' + v['address']}
    if v.get('u'): it['u'] = v['u']
    if v.get('i'): it['i'] = v['i']
    vitems.append(it)
vl = {'id': 'vaccines', 'label': 'Vaccine sites', 'kind': 'pt', 'n': len(vitems), 'items': vitems, 'note': 'NYC Health Map, Vaccines (NYC Department of Health and Mental Hygiene)'}
lay['layers'] = [l for l in lay['layers'] if l['id'] != 'vaccines']
at = next((i for i, l in enumerate(lay['layers']) if l['id'] == 'health'), len(lay['layers']) - 1) + 1
lay['layers'].insert(at, vl)
open(LP, 'w').write(json.dumps(lay, ensure_ascii=False, separators=(',', ':')))
print(len(vitems), 'vaccine sites on the CB6 map;', sum(1 for v in vdoc['sites'] if v.get('u')), 'linked to profiles')
print(len(site), 'site profiles;', len(app_profiles), 'app profiles;', len(drop), 'older app copies replaced')
