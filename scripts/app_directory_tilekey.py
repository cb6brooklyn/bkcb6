#!/usr/bin/env python3
"""The Directory's logos as small tiles in the approved app builds. Those builds draw a list item's `cover` as full-bleed
artwork, two across and large; `tile` draws the smaller tile picture. Every Directory list item (lists dir-*) carries its
picture as `tile`, and the Directory screen's grids read `{tile}`. Runs at the end of app_directory_tiles.py; rerunnable."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
def save(f, obj, raw):
    ind = len(re.match(r'\{\n( *)', raw).group(1)) if raw.startswith('{\n') else None
    open(f, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=ind) + ('\n' if raw.endswith('\n') else ''))
n = 0
for app in ('cb6', 'bk', 'beyond'):
    f = P('app/data/civic/ui', app, 'tools.json'); raw = open(f, encoding='utf-8').read(); T = json.loads(raw)
    for lid, items in T['lists'].items():
        if not lid.startswith('dir-'): continue
        for it in items:
            if 'cover' in it: it['tile'] = it.pop('cover'); n += 1
    save(f, T, raw)
    f = P('app/data/civic/ui', app, 'screens.json'); raw = open(f, encoding='utf-8').read()
    save(f, json.loads(raw.replace('"{cover}"', '"{tile}"')), raw)
print('directory items drawn as tiles:', n)
