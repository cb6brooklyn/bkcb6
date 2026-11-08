#!/usr/bin/env python3
"""The NYC Parks sign banner at the top of each CB6 park's profile in the apps.

Renders the same banner the site's park profiles open with (build_park_profiles.banner) to
app/data/civic/orgs/going/park-sign-<place slug>.jpg and puts it first in that place profile's `going`
cards in app/data/civic/orgs/orgs-profiles.json (the org-profile screen draws `going` at the top).
Idempotent: replaces its own card, leaves any other cards. Run after places_profiles.py.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_park_profiles as B
from playwright.sync_api import sync_playwright

ROOT = B.ROOT
P = os.path.join(ROOT, 'app/data/civic/orgs/orgs-profiles.json')
GO = os.path.join(ROOT, 'app/data/civic/orgs/going')
SUFFIX = ('-courts-and-fields', '-pool', '-recreation-center')
FONT = 'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;800&display=swap'

def pid_of(i):
    for g, parts in B.GROUPS.items():
        if i in parts: return g
    return i

def card_text(pid):
    h = B.park_hours(pid)
    ws = {x['what'] for x in B.signs_for(pid)}
    dog = ('Dogs may be off leash before 9 a.m. and after 9 p.m.' if any('Off-Leash OK' in w for w in ws) else
           'Dog run here; dogs leashed outside it.' if any(w.startswith('Dog Run') or w.startswith('Park with Dog Run') for w in ws) else
           'Dogs must be leashed at all times.' if any('No Off' in w for w in ws) else '')
    return ' '.join(x for x in [f'Open {h}.' if h else '', dog] if x)

def main():
    d = json.load(open(P))
    todo = []
    for p in d['profiles']:
        if not p['slug'].startswith('place-') or p['slug'].endswith(SUFFIX): continue
        m = re.search(r'nycgovparks\.org/parks/(B[0-9A-Z]+)', p.get('weburl') or '')
        if not m: continue
        pid = pid_of(m.group(1))
        if pid not in B.SLUG and pid not in B.SMALL: continue
        name = B.NAME.get(pid) or B.PK[pid if pid in B.PK else B.GROUPS[pid][0]]['n']
        url = 'https://bkcb6.app/park/' + (B.SLUG[pid] + '.html' if pid in B.SLUG else B.SMALL_SLUG + '.html#' + pid)
        todo.append((p, pid, name, url))
    os.makedirs(GO, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={'width': 640, 'height': 300}, device_scale_factor=2)
        for p, pid, name, url in todo:
            html = (f'<!doctype html><html><head><meta charset="utf-8"><link href="{FONT}" rel="stylesheet"><style>body{{margin:0;background:#fff}}'
                    f'{B.BANNER_CSS}.pbn{{margin:0;border-radius:0;max-width:none}}</style></head><body>{B.banner(name, pid)}</body></html>')
            pg.set_content(html); pg.wait_for_timeout(400)
            img = f'park-sign-{p["slug"][6:]}.jpg'
            pg.locator('.pbn').screenshot(path=os.path.join(GO, img), type='jpeg', quality=88)
            card = {'img': img, 'kicker': 'NYC Parks', 'title': name, 'text': card_text(pid), 'until': '', 'id': 'park-sign',
                    'btns': [['Park profile', url, 'hot']]}
            p['going'] = [card] + [g for g in (p.get('going') or []) if g.get('id') != 'park-sign']
        b.close()
    json.dump(d, open(P, 'w'), ensure_ascii=False, indent=1)
    print(len(todo), 'park banners')

if __name__ == '__main__':
    main()
