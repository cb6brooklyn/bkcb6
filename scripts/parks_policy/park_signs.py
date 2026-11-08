#!/usr/bin/env python3
"""Each CB6 park's own NYC Parks sign, as an image: the Parks leaf in its ring, a rule, and the park's name in
white capitals on Parks green (PMS 553, #1D3425), the way the entrance signs are laid out.

  park/pins/<profile slug>.png                    the pin on the park's profile map (portrait sign)
  app/data/civic/orgs/logos/place-sign-<slug>.png the park's logo in the apps (square sign)

and sets each park place profile's `logo` in app/data/civic/orgs/orgs-profiles.json to its own sign.
Run after build_park_profiles.py and places_profiles.py.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_park_profiles as B
from playwright.sync_api import sync_playwright

ROOT = B.ROOT
FONT = 'https://fonts.googleapis.com/css2?family=Arimo:wght@700&display=swap'
PINS = os.path.join(ROOT, 'park/pins')
LOGOS = os.path.join(ROOT, 'app/data/civic/orgs/logos')
PROF = os.path.join(ROOT, 'app/data/civic/orgs/orgs-profiles.json')
G = '#1D3425'

def fit(name, width_chars):
    n = len(name)
    return 30 if n <= width_chars else 26 if n <= width_chars * 1.6 else 22 if n <= width_chars * 2.4 else 19

def pin_html(name):
    fs = fit(name, 12)
    return (f'<div class="s" style="width:200px"><div class="l" style="padding:16px 0 13px"><div style="width:118px;margin:0 auto">{B.LOGO}</div></div>'
            f'<div class="n" style="font-size:{fs}px;padding:10px 14px 15px">{B.E(name.upper())}</div></div>')

def logo_html(name):
    fs = fit(name, 14) + 2
    return (f'<div class="s" style="width:400px;height:400px;display:flex;flex-direction:column"><div class="l" style="flex:1;display:flex;align-items:center;justify-content:center;padding-top:10px">'
            f'<div style="width:{190 if len(name) <= 28 else 160}px">{B.LOGO}</div></div>'
            f'<div class="n" style="font-size:{fs + 10}px;padding:16px 26px 26px">{B.E(name.upper())}</div></div>')

PAGE = ('<!doctype html><html><head><meta charset="utf-8"><link href="' + FONT + '" rel="stylesheet"><style>body{margin:0;background:transparent}'
        '.s{background:' + G + ';color:#fff;font-family:Arimo,Helvetica,Arial,sans-serif;border-radius:6px;overflow:hidden;box-sizing:border-box}'
        '.l svg{width:100%;height:auto;display:block}.n{border-top:2px solid #fff;font-weight:700;line-height:1.04;letter-spacing:-.005em}</style></head><body>%s</body></html>')

def parks():
    out = []
    for pid, slug in B.SLUG.items():
        out.append((pid, slug, B.NAME.get(pid) or B.PK[pid if pid in B.PK else B.GROUPS[pid][0]]['n']))
    for i in B.SMALL:
        n = B.PK[i]['n']
        if n != 'Park': out.append((i, 'small-' + i.lower(), n))
    out.append(('SMALL', 'cb6-small-spaces', 'Small park spaces'))
    return out

def main():
    os.makedirs(PINS, exist_ok=True)
    made = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(device_scale_factor=2, viewport={'width': 420, 'height': 420})
        for pid, slug, name in parks():
            pg.set_content(PAGE.replace("%s", pin_html(name))); pg.wait_for_timeout(250)
            box = pg.locator('.s').bounding_box()
            pg.locator('.s').screenshot(path=os.path.join(PINS, slug + '.png'), omit_background=True)
            pg.set_content(PAGE.replace("%s", logo_html(name))); pg.wait_for_timeout(250)
            lg = f'place-sign-{slug}.png'
            pg.locator('.s').screenshot(path=os.path.join(LOGOS, lg), omit_background=True)
            made[pid] = {'pin': f'/park/pins/{slug}.png', 'w': round(box['width']), 'h': round(box['height']), 'logo': lg, 'name': name}
        b.close()
    json.dump(made, open(os.path.join(ROOT, 'park/pins/pins.json'), 'w'), indent=0)
    # the apps: each park place profile's logo is its own sign
    d = json.load(open(PROF)); n = 0
    for p in d['profiles']:
        if not p['slug'].startswith('place-') or p['slug'].endswith(('-courts-and-fields', '-pool', '-recreation-center')): continue
        m = re.search(r'nycgovparks\.org/parks/(B[0-9A-Z]+)', p.get('weburl') or '')
        if not m: continue
        i = m.group(1)
        pid = next((g for g, parts in B.GROUPS.items() if i in parts), i)
        if pid in made: p['logo'] = made[pid]['logo']; n += 1
    json.dump(d, open(PROF, 'w'), ensure_ascii=False, indent=1)
    print(len(made), 'signs;', n, 'app logos set')

if __name__ == '__main__':
    main()
