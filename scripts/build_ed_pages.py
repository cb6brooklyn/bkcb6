#!/usr/bin/env python3
"""One page per election district at bkcb6.app/ed/<AADDD>/, plus bkcb6.app/ed/ listing them.

Every fact on a page comes from the site's own data files:
  electionexplainer/map/eds.geojson   ED shapes and their districts (2026 BOE election district map)
  electionexplainer/map/ed-cb-split.json  area share of EDs that cross a community district line
  yourdistricts/districts.json        district names and the officials who hold them
  electionexplainer/pollsites.json    Election Day poll site for each ED (BOE Find My Poll Site, Oct 29, 2026)
  electionexplainer/ballot.json       races on the November 3, 2026 ballot (State BOE certification, Oct 7, 2026)
  data/enrollment/cb6.json            registered voters by party (NYS BOE, February 20, 2026)
The map is bkcb6.app/yourdistricts/ in embed mode, opened at the ED.

Run: python3 scripts/build_ed_pages.py [--cb 306 ...]   (default: Brooklyn Community Board 6)
"""
import json, os, sys, html
from shapely.geometry import shape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda p: json.load(open(os.path.join(ROOT, p)))
esc = html.escape

BORO = {'1': 'Manhattan', '2': 'The Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
BC = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
def ordinal(n):
    n = int(n); s = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'); return '%d%s' % (n, s)
def cbname(c): return '%s Community Board %d' % (BORO[c[0]], int(c[1:]))
def cbshort(c): return '%s CB %d' % (BC[c[0]], int(c[1:]))
def edlabel(e): return 'AD %d · ED %d' % (int(e[:2]), int(e[2:]))
def edlong(e): return 'Election District %d, Assembly District %d' % (int(e[2:]), int(e[:2]))

def main():
    cbs = ['306']
    if '--cb' in sys.argv: cbs = sys.argv[sys.argv.index('--cb') + 1:]
    eds = J('electionexplainer/map/eds.geojson')['features']
    split = J('electionexplainer/map/ed-cb-split.json')['d']
    D = J('yourdistricts/districts.json')['d']
    PS = J('electionexplainer/pollsites.json')
    B = J('electionexplainer/ballot.json')
    enr = J('data/enrollment/cb6.json')['dates'][-1]
    byid = {f['properties']['id']: f for f in eds}
    geo = {k: shape(f['geometry']).buffer(0) for k, f in byid.items()}

    def cbs_of(e):
        return split.get(e) or {byid[e]['properties']['cb']: 1.0}
    pick = sorted([e for e in byid if any(c in cbs for c in cbs_of(e))])
    print(len(pick), 'election districts', file=sys.stderr)

    def dname(kind, v):
        r = D.get(kind, {}).get(v)
        return r['n'] if r else None

    def races(p):
        out = [r['t'] for r in B['state']]
        for k, v in (('cd', p['cd']), ('sd', p['sd']), ('ad', p['ad'])):
            r = B[k].get(str(int(v)) if v else '')
            if r: out.append(r['t'])
        boro = p['bo']
        for k in ('sur', 'sc', 'ccc'):
            r = B.get(k, {}).get(boro)
            if r: out.append(r['t'])
        if p.get('mc') and B['ccd'].get(p['mc']): out.append(B['ccd'][p['mc']]['t'])
        if p.get('cc') and B['ccl'].get(str(int(p['cc']))): out.append(B['ccl'][str(int(p['cc']))]['t'])
        return out

    def neighbors(e):
        g = geo[e]; out = []
        for k, h in geo.items():
            if k != e and g.bounds[0] <= h.bounds[2] and h.bounds[0] <= g.bounds[2] and g.bounds[1] <= h.bounds[3] and h.bounds[1] <= g.bounds[3]:
                if g.intersection(h).length > 0 or g.touches(h):
                    out.append(k)
        return sorted(out)

    CSS = """:root{--navy:#0d1b4b;--orange:#f47920;--bg:#f8f7f4;--line:#e5e2db;--muted:#6b6760;--mono:'DM Mono',ui-monospace,monospace}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--navy);font-family:'DM Sans',system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased}
header{background:var(--navy);color:#fff;padding:20px 16px 18px;border-bottom:4px solid var(--orange)}header .in,.wrap{max-width:1000px;margin:0 auto}
.wrap{padding:16px 16px 40px}.eyebrow{font:500 .72rem var(--mono);letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.65)}.eyebrow a{color:inherit}
h1{margin:6px 0 4px;font-size:clamp(1.5rem,4.4vw,2.2rem);font-weight:800;line-height:1.1}.lede{margin:0;color:rgba(255,255,255,.85);line-height:1.45}
h2{font-size:1.05rem;margin:22px 0 8px}.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.kv{display:grid;grid-template-columns:minmax(120px,190px) 1fr;gap:8px 14px;font-size:.95rem}.kv dt{font:500 .7rem var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding-top:3px}.kv dd{margin:0}
@media(max-width:560px){.kv{grid-template-columns:1fr}.kv dd{margin-bottom:6px}}
ul.r{margin:0;padding-left:18px;line-height:1.55}a{color:var(--navy)}
.reg{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:.92rem}.reg td{padding:6px 4px;border-bottom:1px solid #f0eee9}.reg td.n{text-align:right;font-weight:700}
.nb{display:flex;flex-wrap:wrap;gap:6px}.nb a{font:600 .82rem 'DM Sans',sans-serif;border:1.5px solid var(--line);border-radius:999px;padding:5px 10px;text-decoration:none;background:#fff}
iframe{width:100%;border:0;display:block;min-height:900px;background:transparent}.note{font-size:.82rem;color:var(--muted);line-height:1.5;margin-top:16px}
.nav{display:flex;justify-content:space-between;gap:8px;margin:18px 0 0;flex-wrap:wrap}.nav a{font-weight:700;text-decoration:none}"""
    HEAD = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="apple-itunes-app" content="app-id=6813967208">'
    FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,400;9..40,600;9..40,700;9..40,800&display=swap" rel="stylesheet">'
    RESIZE = "<script>addEventListener('message',function(e){if(e.data&&e.data.bkcbEmbedHeight){var f=document.getElementById('edmap');if(f)f.style.height=(e.data.bkcbEmbedHeight+8)+'px'}});</script>"
    PARTY = enr['parties']
    PN = {'DEM': 'Democratic', 'REP': 'Republican', 'CON': 'Conservative', 'WOR': 'Working Families', 'OTH': 'Other parties', 'BLANK': 'No party'}

    for i, e in enumerate(pick):
        p = byid[e]['properties']
        share = cbs_of(e)
        acres = geo[e].area  # degrees; converted below
        lat = geo[e].centroid.y
        import math
        acres = geo[e].area * (111320 ** 2) * math.cos(math.radians(lat)) / 4046.86
        ps = PS['d'].get(e)
        site = PS['s'][ps[0]] if ps else None
        cbtxt = ' and '.join('%s (%d%% of its area)' % (cbname(c), round(f * 100)) for c, f in sorted(share.items(), key=lambda x: -x[1])) if len(share) > 1 else cbname(list(share)[0])
        rows = [
            ('Community board', cbtxt),
            ('Borough', BORO[list(share)[0][0]]),
            ('Assembly', dname('ad', p['ad']) or 'Assembly District %s' % p['ad']),
            ('State Senate', dname('sd', p['sd']) or 'Senate District %s' % p['sd']),
            ('Congress', dname('cd', p['cd']) or 'Congressional District %s' % p['cd']),
            ('City Council', dname('cc', p['cc']) or 'Council District %s' % p['cc']),
        ]
        if p.get('mc'): rows.append(('Civil Court', dname('mc', p['mc']) or p['mc']))
        rows.append(('Area', '%s acres' % format(round(acres, 1), ',')))
        kv = ''.join('<dt>%s</dt><dd>%s</dd>' % (esc(k), esc(v)) for k, v in rows)
        sitehtml = ''
        if site:
            sitehtml = '<h2>Where this election district votes on Election Day</h2><div class="card"><b>%s</b><br>%s%s%s<br><a href="https://www.google.com/maps/dir/?api=1&amp;destination=%s,%s" target="_blank" rel="noopener">Directions</a></div>' % (
                esc(site[0]), esc(site[1]), ('<br>Entrance: ' + esc(site[3])) if site[3] and site[3] != site[2] else '', ('<br>Room: ' + esc(site[4])) if site[4] else '', site[5], site[6])
        reg = enr['eds'].get(e)
        reghtml = ''
        if reg:
            tot = reg[len(PARTY)]
            reghtml = '<h2>Registered voters</h2><div class="card"><table class="reg">' + ''.join(
                '<tr><td>%s</td><td class="n">%s</td><td class="n" style="color:var(--muted);font-weight:500">%s%%</td></tr>' % (PN.get(k, k), format(reg[j], ','), round(100 * reg[j] / tot, 1) if tot else 0) for j, k in enumerate(PARTY)) + \
                '<tr><td><b>Total</b></td><td class="n">%s</td><td></td></tr><tr><td>Active</td><td class="n">%s</td><td></td></tr></table><p class="note" style="margin:8px 0 0">NYS Board of Elections, enrollment by election district, %s. Total includes inactive voters.</p></div>' % (format(tot, ','), format(reg[len(PARTY) + 1], ','), 'February 20, 2026')
        rc = races(p)
        racehtml = '<h2>On the ballot November 3, 2026</h2><div class="card"><ul class="r">' + ''.join('<li>%s</li>' % esc(r) for r in rc) + '</ul><p class="note" style="margin:8px 0 0">Plus the five City Charter questions on the back. Candidates and what each office does at <a href="/vote/">bkcb6.app/vote</a>.</p></div>'
        nb = neighbors(e)
        nbhtml = '<h2>Neighboring election districts</h2><div class="nb">' + ''.join('<a href="/ed/%s/">%s</a>' % (n, esc(edlabel(n))) for n in nb) + '</div>' if nb else ''
        prev_ = pick[i - 1] if i > 0 else None; next_ = pick[i + 1] if i + 1 < len(pick) else None
        nav = '<div class="nav"><span>%s</span><a href="/ed/">All election districts</a><span>%s</span></div>' % (
            ('<a href="/ed/%s/">&larr; %s</a>' % (prev_, esc(edlabel(prev_)))) if prev_ else '', ('<a href="/ed/%s/">%s &rarr;</a>' % (next_, esc(edlabel(next_)))) if next_ else '')
        desc = '%s is in %s. Its voters are represented by %s in the Assembly, %s in the State Senate, %s in Congress and %s on the City Council.' % (
            edlong(e), cbtxt, (dname('ad', p['ad']) or '').split(' · ')[-1], (dname('sd', p['sd']) or '').split(' · ')[-1], (dname('cd', p['cd']) or '').split(' · ')[-1], (dname('cc', p['cc']) or '').split(' · ')[-1])
        if site: desc += ' On Election Day they vote at %s, %s.' % (site[0], site[2])
        title = '%s · %s' % (edlong(e), cbshort(max(share, key=share.get)))
        page = HEAD + '<title>%s · bkcb6.app</title><meta name="description" content="%s"><meta property="og:title" content="%s"><meta property="og:description" content="%s"><link rel="canonical" href="https://bkcb6.app/ed/%s/">%s<style>%s</style></head><body><script src="/assets/site-bar.js?v=1" defer></script>' % (
            esc(title), esc(desc), esc(edlong(e)), esc(desc), e, FONTS, CSS)
        page += '<header><div class="in"><div class="eyebrow"><a href="/ed/">Election districts</a> · %s</div><h1>%s</h1><p class="lede">%s</p></div></header><div class="wrap">' % (esc(cbname(max(share, key=share.get))), esc(edlong(e)), esc(desc))
        page += '<div class="card"><dl class="kv">%s</dl></div>' % kv
        page += '<h2>On the map</h2><iframe id="edmap" title="Map of %s and the districts it is part of" src="/yourdistricts/?embed=1#ed=%s&fit=ed" loading="lazy"></iframe>' % (esc(edlong(e)), e)
        page += sitehtml + racehtml + reghtml + nbhtml + nav
        page += '<p class="note">Election district lines are the NYC Board of Elections 2026 map. Poll site from the Board\'s Find My Poll Site, October 29, 2026. Races from the State Board of Elections certification of October 7, 2026.</p></div>' + RESIZE + '</body></html>'
        d = os.path.join(ROOT, 'ed', e); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w').write(page)

    # index
    byad = {}
    for e in pick: byad.setdefault(int(e[:2]), []).append(e)
    groups = ''.join('<h2>Assembly District %d</h2><div class="nb">%s</div>' % (ad, ''.join('<a href="/ed/%s/">ED %d</a>' % (e, int(e[2:])) for e in es)) for ad, es in sorted(byad.items()))
    idx = HEAD + '<title>Election districts · bkcb6.app</title><meta name="description" content="Every election district in %s: its districts, representatives, poll site, ballot, registered voters and map."><link rel="canonical" href="https://bkcb6.app/ed/">%s<style>%s</style></head><body><script src="/assets/site-bar.js?v=1" defer></script>' % (esc(', '.join(cbname(c) for c in cbs)), FONTS, CSS)
    idx += '<header><div class="in"><div class="eyebrow">Election districts · 2026 map</div><h1>Election districts in %s</h1><p class="lede">%d election districts, each with its own page: its districts and representatives, Election Day poll site, ballot, registered voters and a map of everything it is part of.</p></div></header><div class="wrap">%s<p class="note">Includes election districts that cross into %s from a neighboring community district.</p></div></body></html>' % (
        esc(', '.join(cbname(c) for c in cbs)), len(pick), groups, esc(', '.join(cbshort(c) for c in cbs)))
    os.makedirs(os.path.join(ROOT, 'ed'), exist_ok=True)
    open(os.path.join(ROOT, 'ed', 'index.html'), 'w').write(idx)
    print('wrote', len(pick), 'pages + index', file=sys.stderr)

if __name__ == '__main__':
    main()
