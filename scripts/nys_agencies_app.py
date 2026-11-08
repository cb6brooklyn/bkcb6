#!/usr/bin/env python3
"""The apps' Directory, Government agencies: every New York State agency on bkcb6.app/agencies/nys (the 98 on
ny.gov/agencies) becomes a profile in app/data/civic/orgs/orgs-profiles.json, read from its site page
(agencies/nys/<slug>/index.html: name, ny.gov category, description in the state's words, official site, ny.gov page,
tile). Rerunnable: its own nys-* entries are replaced."""
import html, json, os, re
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
P = 'app/data/civic/orgs/orgs-profiles.json'
d = json.load(open(P))
U = lambda s: html.unescape(re.sub(r'<[^>]+>', '', s)).strip()
made = []
for slug in sorted(os.listdir('agencies/nys')):
    f = f'agencies/nys/{slug}/index.html'
    if not os.path.isfile(f): continue
    s = open(f).read()
    name = U(re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S).group(1))
    seat = U(re.search(r'<div class="pseat">(.*?)</div>', s, re.S).group(1))
    cat = seat.split('·')[-1].strip()
    m = re.search(r'What it does</h2><div class="wide">(.*?)</div>', s, re.S)
    what = [U(p) for p in re.findall(r'<p>(.*?)</p>', m.group(1), re.S)] if m else []
    what = [w for w in what if w and not w.startswith("In the state")]
    links = re.findall(r'<a class="btn[^"]*" href="([^"]+)"[^>]*>(.*?)</a>', s)
    off = next((h for h, t in links if 'Official site' in t), '')
    nyg = next((h for h, t in links if 'ny.gov' in U(t)), '')
    tile = f'site-icons/agencies/nys/{slug}.png'; logo = ''
    if os.path.exists(tile):
        logo = f'agency-nys-{slug}.png'; dst = f'app/data/civic/orgs/logos/{logo}'
        if not os.path.exists(dst):
            im = Image.open(tile).convert('RGBA'); im.thumbnail((400, 400)); im.save(dst, optimize=True)
    made.append({'slug': f'nys-{slug}', 'type': f'nys-{slug}', 'name': name, 'seat': f'New York State agency · {cat}',
                 'desc': f'{name}, a New York State agency.', 'lat': None, 'lng': None, 'addr': '', 'zip': '', 'addr_note': '', 'phone': '', 'email': '',
                 'web': re.sub(r'^https?://(www\.)?', '', off).rstrip('/') if off else '', 'weburl': off, 'since': '',
                 'intro': [f'{name} is a New York State agency, listed by ny.gov under {cat}.'], 'does': what,
                 'kv': [['Level', 'New York State'], ['ny.gov category', cat], ['Source', 'ny.gov/agencies']],
                 'links': [l for l in [['Profile', f'https://bkcb6.app/agencies/nys/{slug}/'], ['Official site', off] if off else None, ['On ny.gov', nyg] if nyg else None] if l],
                 'logo': logo, 'cal': None, 'n': 0, 'going': [], 'kind': 'org', 'official': '', 'group': 'Government agencies', 'topic': '', 'sort': 5})
d['profiles'] = [p for p in d['profiles'] if not p['slug'].startswith('nys-')] + made
json.dump(d, open(P, 'w'), ensure_ascii=False, indent=1)
print(len(made), 'state agencies')
