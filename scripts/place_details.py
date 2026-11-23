#!/usr/bin/env python3
"""More about each place, so people can tell what it is: its menu (the menu link on its own website) and the food it
serves (the kind of food the Health Department lists for it). data/cb6-audit/place-details.json {slug: {menu, food}}.
Adds them to the app profile (Food in its details, Menu in its links) and to its site page (Contact and Details).
Rerunnable; run after the Directory rebuild, before og_logos.py."""
import json, os, re, math, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
E = lambda s: html.escape(s or '', quote=True)
def main():
    X = json.load(open('data/cb6-audit/place-details.json'))
    f = 'app/data/civic/orgs/orgs-profiles.json'; D = json.load(open(f, encoding='utf-8'))
    for p in D['profiles']:
        p['kv'] = [k for k in p.get('kv') or [] if k[0] != 'Food']; p['links'] = [l for l in p.get('links') or [] if l[0] != 'Menu']
        x = X.get(p['slug'])
        if not x: continue
        if x.get('food'): p['kv'] = [['Food', x['food']]] + p['kv']
        if x.get('menu'): p['links'] = [['Menu', x['menu']]] + p['links']
    open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
    # the site pages: the Directory row for the place (same name, nearest)
    rows = {}
    for r in json.load(open('profiles/dir.json'))['E']: rows.setdefault(r[0], []).append(r)
    P = {p['slug']: p for p in D['profiles']}; n = 0; PG = {}
    for s, x in sorted(X.items()):
        p = P.get(s)
        if not p or not rows.get(p['name']): continue
        r = min(rows[p['name']], key=lambda r: math.hypot((r[11] or 0) - float(p.get('lat') or 0), (r[12] or 0) - float(p.get('lng') or 0)))
        h = r[1].split('#')[0]; fp = h[1:] if h.endswith('.html') else h[1:] + 'index.html' if h.endswith('/') else h[1:] + '.html'
        if os.path.isfile(fp): PG[fp] = {**x, **PG.get(fp, {})}
    for fp, x in PG.items():
        t = open(fp, encoding='utf-8').read(); u = re.sub(r'<li data-pd>.*?</li>', '', t)
        if x.get('menu'):
            li = '<li data-pd><span class="k">Menu</span><span class="v"><a href="%s" target="_blank" rel="noopener">See the menu &#8599;</a></span></li>' % E(x['menu'])
            if '<h2>Contact</h2><div class="bio"><ul class="kv">' in u: u = u.replace('<h2>Contact</h2><div class="bio"><ul class="kv">', '<h2>Contact</h2><div class="bio"><ul class="kv">' + li, 1)
            elif '<h2>Details</h2><div class="bio"><ul class="kv">' in u: u = u.replace('<h2>Details</h2><div class="bio"><ul class="kv">', '<h2>Details</h2><div class="bio"><ul class="kv">' + li, 1)
            elif '<ul class="kv">' in u: u = u.replace('<ul class="kv">', '<ul class="kv">' + li, 1)
        if x.get('food'):
            li = '<li data-pd><span class="k">Food</span><span class="v">%s</span></li>' % E(x['food'])
            if '<h2>Details</h2><div class="bio"><ul class="kv">' in u: u = u.replace('<h2>Details</h2><div class="bio"><ul class="kv">', '<h2>Details</h2><div class="bio"><ul class="kv">' + li, 1)
            elif '<ul class="kv">' in u: u = u.replace('<ul class="kv">', '<ul class="kv">' + li, 1)
        if u != t: open(fp, 'w', encoding='utf-8').write(u); n += 1
    print('places with more detail:', len(X), '| site pages updated:', n)
if __name__ == '__main__': main()
