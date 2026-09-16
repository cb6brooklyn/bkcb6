#!/usr/bin/env python3
"""Write data/vzr/cb6-schools.json: every school in the CB6 layers file with the logo Mike compiled.

Source of the schools: assets/blocks/cb6-layers.json (layer id "schools").
Source of the logos: the SCHOOLMAP name-to-file table and the SCHOOLLOGO regex table in myblock/index.html,
which key /assets/map-icons/d15/*.png, with /assets/map-icons/schools-nycps.png as the fallback.
"""
import json, os, re, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
layers = json.load(open(os.path.join(ROOT, 'assets', 'blocks', 'cb6-layers.json')))
schools = [x for x in layers['layers'] if x['id'] == 'schools'][0]['items']

src = open(os.path.join(ROOT, 'myblock', 'index.html')).read()
body = re.search(r'var SCHOOLMAP=\{(.*?)\n\};', src, re.S).group(1)
SMAP = {}
for m in re.finditer(r"""(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")\s*:\s*'([^']*)'""", body):
    name = (m.group(1) or m.group(2)).replace("\\'", "'").replace('\\"', '"')
    SMAP[name] = m.group(3)
logo_body = re.search(r'var SCHOOLLOGO=\[(.*?)\n\];', src, re.S).group(1)
RX = [(re.compile(rx[1:-2], re.I), path) for rx, path in re.findall(r"\[(/.*?/i),'([^']+)'\]", logo_body)]
FALLBACK = '/assets/map-icons/schools-nycps.png'

out, missing = [], []
for it in schools:
    name = it.get('t') or ''
    logo = None
    if name in SMAP:
        logo = '/assets/map-icons/d15/' + SMAP[name] + '.png'
    if not logo:
        for rx, p in RX:
            if rx.search(name):
                logo = p
                break
    if not logo or not os.path.exists(os.path.join(ROOT, logo.lstrip('/'))):
        if logo: missing.append(logo)
        logo = FALLBACK
    out.append({'x': it['x'], 'y': it['y'], 't': name, 's': it.get('s', ''), 'k': it.get('k', ''), 'u': it.get('u', ''), 'logo': logo})

os.makedirs(os.path.join(ROOT, 'data', 'vzr'), exist_ok=True)
json.dump({'generated': datetime.date.today().isoformat(),
           'source': 'Schools in Brooklyn Community District 6 from assets/blocks/cb6-layers.json; logos from /assets/map-icons/d15/ and /assets/map-icons/',
           'schools': out},
          open(os.path.join(ROOT, 'data', 'vzr', 'cb6-schools.json'), 'w'), separators=(',', ':'))
print(len(out), 'schools,', sum(1 for s in out if s['logo'] != FALLBACK), 'with their own logo')
if missing: print('missing files:', missing)
