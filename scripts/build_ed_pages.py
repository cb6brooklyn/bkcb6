#!/usr/bin/env python3
"""One page per election district at bkcb6.app/ed/<AADDD>/, plus bkcb6.app/ed/ listing them.

Every fact on a page comes from the site's own data files:
  electionexplainer/map/eds.geojson   ED shapes and their districts (2026 BOE election district map)
  electionexplainer/map/ed-cb-split.json  area share of EDs that cross a community district line
  yourdistricts/districts.json        district names and the officials who hold them
  electionexplainer/pollsites.json    Election Day poll site for each ED (BOE Find My Poll Site, Oct 29, 2026)
  electionexplainer/ballot.json       races on the November 3, 2026 ballot (State BOE certification, Oct 7, 2026)
  data/enrollment/nyc-20260220.json   registered voters by party, every NYC ED (NYS BOE, February 20, 2026)
The map is Apple Maps (MapKit JS, assets/ed-map.js): the ED, its neighbors, and the districts it is part of as toggles.

Run: python3 scripts/build_ed_pages.py [--cb 306 ...]   (default: every election district in the city)
"""
import json, os, sys, html, re
from shapely.geometry import shape
from shapely.strtree import STRtree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boe_edlevel import race_key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda p: json.load(open(os.path.join(ROOT, p)))
esc = html.escape

BORO = {'1': 'Manhattan', '2': 'The Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
BOFULL = {'MANHATTAN': 'Manhattan', 'BRONX': 'The Bronx', 'BROOKLYN': 'Brooklyn', 'QUEENS': 'Queens', 'STATEN ISLAND': 'Staten Island'}
BONUM = {'MANHATTAN': '1', 'BRONX': '2', 'BROOKLYN': '3', 'QUEENS': '4', 'STATEN ISLAND': '5'}
BC = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
def ordinal(n):
    n = int(n); s = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'); return '%d%s' % (n, s)
def cbname(c): return '%s Community Board %d' % (BORO[c[0]].replace('The ', ''), int(c[1:]))
def cbshort(c): return '%s CB %d' % (BC[c[0]], int(c[1:]))
def edlabel(e): return 'AD %d · ED %d' % (int(e[:2]), int(e[2:]))
def edlong(e): return 'Election District %d, Assembly District %d' % (int(e[2:]), int(e[:2]))

def main():
    cbs = None
    if '--cb' in sys.argv: cbs = sys.argv[sys.argv.index('--cb') + 1:]
    eds = J('electionexplainer/map/eds.geojson')['features']
    split = J('electionexplainer/map/ed-cb-split.json')['d']
    D = J('yourdistricts/districts.json')['d']
    PS = J('electionexplainer/pollsites.json')
    B = J('electionexplainer/ballot.json')
    enr = J('data/enrollment/nyc-20260220.json'); CHG = set(enr['chg'])
    byid = {f['properties']['id']: f for f in eds}
    geo = {k: shape(f['geometry']).buffer(0) for k, f in byid.items()}

    def cbs_of(e):
        if e in split: return split[e]
        c = byid[e]['properties']['cb']
        return {c: 1.0} if c else {}
    pick = sorted([e for e in byid if cbs is None or any(c in cbs for c in cbs_of(e))])
    print(len(pick), 'election districts', file=sys.stderr)

    def dname(kind, v):
        r = D.get(kind, {}).get(v)
        return r['n'] if r else None

    def races(p):
        out = list(B['state'])
        for k, v in (('cd', p['cd']), ('sd', p['sd']), ('ad', p['ad'])):
            r = B[k].get(str(int(v)) if v else '')
            if r: out.append(r)
        boro = p['bo']
        for k in ('sur', 'sc', 'ccc'):
            r = B.get(k, {}).get(boro)
            if r: out.append(r)
        if p.get('mc') and B['ccd'].get(p['mc']): out.append(B['ccd'][p['mc']])
        if p.get('cc') and B['ccl'].get(str(int(p['cc']))): out.append(B['ccl'][str(int(p['cc']))])
        return out

    keys = list(geo); tree = STRtree([geo[k] for k in keys])
    def neighbors(e):
        g = geo[e]; out = []
        for j in tree.query(g):
            k = keys[int(j)]; h = geo[k]
            if k != e and (g.intersection(h).length > 0 or g.touches(h)):
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
/*race*/.race{margin:0 0 10px}.rh{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:baseline}.rh span{font:500 .68rem var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--orange)}
.cl{margin:8px 0 0;padding:0;list-style:none}.cl li{padding:5px 0;border-top:1px solid #f0eee9}.pl{font:500 .66rem var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-left:6px}
.res{margin-top:10px;border-top:2px solid var(--navy);padding-top:8px}.res .t{font:500 .68rem var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.rr{display:grid;grid-template-columns:1fr auto auto;gap:4px 12px;font-variant-numeric:tabular-nums;font-size:.92rem}.rr .bar{grid-column:1/4;height:5px;background:#f0eee9;border-radius:3px;overflow:hidden;margin-bottom:4px}.rr .bar b{display:block;height:100%;background:var(--navy)}
#edmap{width:100%;height:min(70vh,560px);border-radius:14px;border:1px solid var(--line);background:#dfe7ea}.tg{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 10px}.tg button{font:600 .82rem 'DM Sans',sans-serif;border:1.5px solid var(--c,var(--line));background:#fff;color:var(--navy);border-radius:999px;padding:6px 11px;cursor:pointer;display:inline-flex;align-items:center;gap:6px}.tg button i{width:10px;height:10px;border-radius:3px;background:var(--c)}.tg button[aria-pressed=true]{background:var(--c);color:#fff}.tg button[aria-pressed=true] i{background:#fff}.note{font-size:.82rem;color:var(--muted);line-height:1.5;margin-top:16px}
.nav{display:flex;justify-content:space-between;gap:8px;margin:18px 0 0;flex-wrap:wrap}.nav a{font-weight:700;text-decoration:none}"""
    HEAD = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="apple-itunes-app" content="app-id=6813967208">'
    FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,400;9..40,600;9..40,700;9..40,800&display=swap" rel="stylesheet">'
    LIVE = """<script>(function(){var ED=document.body.dataset.ed;function norm(x){return String(x||'').toLowerCase().replace(/[^a-z0-9 ]/g,' ').replace(/\\b(the|of|and|new york|kings|county|citywide)\\b/g,' ').replace(/\\s+/g,' ').trim()}
function score(a,b){a=norm(a).split(' ');b=norm(b).split(' ');var n=0;a.forEach(function(w){if(w&&b.indexOf(w)>=0)n++});return n/Math.max(a.length,b.length)}
fetch('/data/results/2026-general.json?t='+Date.now(),{cache:'no-store'}).then(function(r){return r.ok?r.json():null}).then(function(d){if(!d||!d.contests||!d.contests.length)return;
var cards=[].slice.call(document.querySelectorAll('.race[data-race]')),used={};
d.contests.forEach(function(c){var e=c.ed&&c.ed[ED];if(!e)return;var best=null,bs=.5;cards.forEach(function(k,i){if(used[i]||best!=null&&bs>1)return;if(c.k&&k.dataset.k===c.k){best=i;bs=2;return}var s=score(k.dataset.race,c.name);if(s>bs){bs=s;best=i}});
var v=e.v||[],tot=v.reduce(function(a,b){return a+b},0),ord=c.c.map(function(x,i){return i}).sort(function(a,b){return v[b]-v[a]});
var h='<div class="t">'+(e.r?'This election district':'This election district, not yet reported')+' · '+tot.toLocaleString()+' votes'+(d.final?'':' · numbers so far from the Board of Elections')+'</div><div class="rr">'+ord.map(function(i){var p=tot?100*v[i]/tot:0;return '<span>'+c.c[i].n.replace(/[<>&]/g,'')+'</span><b>'+v[i].toLocaleString()+'</b><span>'+p.toFixed(1)+'%</span><span class="bar"><b style="width:'+p.toFixed(1)+'%"></b></span>'}).join('')+'</div>';
var box;if(best!=null){used[best]=1;box=cards[best].querySelector('.res')}else{var k=document.createElement('div');k.className='card race';k.innerHTML='<div class="rh"><b>'+c.name.replace(/[<>&]/g,'')+'</b></div><div class="res"></div>';var last=document.querySelector('.race:last-of-type');last.parentNode.insertBefore(k,last.nextSibling);box=k.querySelector('.res')}
box.innerHTML=h;box.hidden=false});
var n=document.getElementById('resnote');if(n&&d.updated)n.textContent='Every race on this election district\\'s ballot, with every candidate and party line, and this election district\\'s results from the Board of Elections, updated '+new Date(d.updated).toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})+'. Every community board: bkcb6.app/results.'}).catch(function(){})})();</script>"""
    MAPJS = '<script src="https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.js"></script><script src="/assets/ed-map.js?v=1"></script>'
    TG = '<div class="tg" id="edtg"><button data-l="nb" aria-pressed="true" style="--c:#3d4a72"><i></i>Neighboring election districts</button><button data-l="ad" aria-pressed="false" style="--c:#2e7d32"><i></i>Assembly</button><button data-l="sd" aria-pressed="false" style="--c:#6a1b9a"><i></i>State Senate</button><button data-l="cd" aria-pressed="false" style="--c:#c62828"><i></i>Congress</button><button data-l="cc" aria-pressed="false" style="--c:#00796b"><i></i>City Council</button><button data-l="mc" aria-pressed="false" style="--c:#8d4b2b"><i></i>Civil Court</button><button data-l="cb" aria-pressed="false" style="--c:#0d1b4b"><i></i>Community boards</button><button data-l="bo" aria-pressed="false" style="--c:#1a3e8c"><i></i>Boroughs</button></div>'
    PARTY = enr['parties']
    PN = {'DEM': 'Democratic', 'REP': 'Republican', 'CON': 'Conservative', 'WOR': 'Working Families', 'OTH': 'Other parties', 'BLANK': 'No party'}

    QS = [(1, 'Speed Up Process for Granting a Revocable Consent to Use Public Space'), (2, 'Reduce City Contractor Paperwork; Require Regular Meetings of Procurement Policy Board'),
          (3, 'Speed Up Street Safety Projects, Disposition of Unused City Property, Office Leasing'), (4, 'Simplify Building Permitting and Move Waterfront Permitting to Department of Buildings'),
          (5, 'Set Contribution Targets for Rainy Day Fund to Promote Sufficient Budgetary Reserves')]
    for i, e in enumerate(pick):
        p = byid[e]['properties']
        share = cbs_of(e)
        acres = geo[e].area  # degrees; converted below
        lat = geo[e].centroid.y
        import math
        acres = geo[e].area * (111320 ** 2) * math.cos(math.radians(lat)) / 4046.86
        ps = PS['d'].get(e)
        site = PS['s'][ps[0]] if ps else None
        top = max(share, key=share.get) if share else None
        bo = BOFULL[p['bo']]
        cbtxt = 'No community district (%s)' % bo if not share else ' and '.join('%s (%d%% of its area)' % (cbname(c), round(f * 100)) for c, f in sorted(share.items(), key=lambda x: -x[1])) if len(share) > 1 else cbname(list(share)[0])
        rows = [
            ('Community board', cbtxt),
            ('Borough', bo),
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
            chgnote = ' The election district\'s lines were changed on the 2026 map after this count, so these figures describe its previous lines.' if e in CHG else ''
            reghtml = '<h2>Registered voters</h2><div class="card"><table class="reg">' + ''.join(
                '<tr><td>%s</td><td class="n">%s</td><td class="n" style="color:var(--muted);font-weight:500">%s%%</td></tr>' % (PN.get(k, k), format(reg[j], ','), round(100 * reg[j] / tot, 1) if tot else 0) for j, k in enumerate(PARTY)) + \
                '<tr><td><b>Total</b></td><td class="n">%s</td><td></td></tr>%s</table><p class="note" style="margin:8px 0 0">NYS Board of Elections, enrollment by election district, %s. Total includes inactive voters.%s</p></div>' % (
                    format(tot, ','), ('<tr><td>Active</td><td class="n">%s</td><td></td></tr>' % format(reg[len(PARTY) + 1], ',')) if reg[len(PARTY) + 1] is not None else '', 'February 20, 2026', chgnote)
        else:
            reghtml = '<h2>Registered voters</h2><div class="card"><p class="note" style="margin:0">This election district number is new on the 2026 map, so the State Board of Elections\' February 20, 2026 enrollment count has no figures for it.</p></div>'
        nb = neighbors(e)
        rc = races(p)
        JUDGE = lambda r: bool(re.match(r'(sc|sur|ccc|mc)', race_key(r['t']) or ''))
        VF = {1: 'Vote for one', 2: 'Vote for up to two', 3: 'Vote for up to three', 4: 'Vote for up to four', 5: 'Vote for up to five', 6: 'Vote for up to six'}
        def racecard(r):
            cands = ''.join('<li><b>%s</b> <span class="pl">%s</span></li>' % (esc(c[0]), esc(' · '.join(c[1]))) for c in r['c'])
            return '<div class="card race" data-race="%s" data-k="%s"><div class="rh"><b>%s</b><span>%s</span></div><ul class="cl">%s</ul><div class="res" hidden></div></div>' % (esc(r['t']), race_key(r['t']) or '', esc(r['t']), esc(VF.get(r['vf'], 'Vote for %d' % r['vf'])), cands)
        racehtml = '<h2>On the ballot November 3, 2026</h2><p class="note" id="resnote" style="margin:0 0 10px">Every race on this election district\'s ballot, with every candidate and party line. Results for this election district appear under each race once the Board of Elections reports them.</p>' + ''.join(racecard(r) for r in rc if not JUDGE(r)) + \
            ''.join('<div class="card race" data-race="Proposal Number %d" data-k="q%d"><div class="rh"><b>City Charter Question %d: %s</b><span>Back of the ballot · Yes or No</span></div><p class="note" style="margin:6px 0 0">What a yes and a no does: <a href="/vote/#questions">bkcb6.app/vote</a>.</p><div class="res" hidden></div></div>' % (n, n, n, esc(t)) for n, t in QS) + \
            (('<details class="card" style="margin:0 0 10px"><summary style="cursor:pointer;font-weight:700">Judges</summary>' + ''.join(racecard(r) for r in rc if JUDGE(r)) + '</details>') if any(JUDGE(r) for r in rc) else '')
        nbhtml = '<h2>Neighboring election districts</h2><div class="nb">' + ''.join('<a href="/ed/%s/">%s</a>' % (n, esc(edlabel(n))) for n in nb) + '</div>' if nb else ''
        prev_ = pick[i - 1] if i > 0 else None; next_ = pick[i + 1] if i + 1 < len(pick) else None
        nav = '<div class="nav"><span>%s</span><a href="/ed/">All election districts</a><span>%s</span></div>' % (
            ('<a href="/ed/%s/">&larr; %s</a>' % (prev_, esc(edlabel(prev_)))) if prev_ else '', ('<a href="/ed/%s/">%s &rarr;</a>' % (next_, esc(edlabel(next_)))) if next_ else '')
        desc = '%s is in %s. Its voters are represented by %s in the Assembly, %s in the State Senate, %s in Congress and %s on the City Council.' % (
            edlong(e), cbtxt, (dname('ad', p['ad']) or '').split(' · ')[-1], (dname('sd', p['sd']) or '').split(' · ')[-1], (dname('cd', p['cd']) or '').split(' · ')[-1], (dname('cc', p['cc']) or '').split(' · ')[-1])
        if site: desc += ' On Election Day they vote at %s, %s.' % (site[0], site[2])
        title = '%s · %s' % (edlong(e), cbshort(top) if top else bo)
        page = HEAD + '<title>%s · bkcb6.app</title><meta name="description" content="%s"><meta property="og:title" content="%s"><meta property="og:description" content="%s"><link rel="canonical" href="https://bkcb6.app/ed/%s/">%s<style>%s</style></head><body data-ed="%s"><script src="/assets/site-bar.js?v=1" defer></script>' % (
            esc(title), esc(desc), esc(edlong(e)), esc(desc), e, FONTS, CSS, e)
        page += '<header><div class="in"><div class="eyebrow"><a href="/ed/">Election districts</a> · %s</div><h1>%s</h1><p class="lede">%s</p></div></header><div class="wrap">' % (esc(cbname(top) if top else bo), esc(edlong(e)), esc(desc))
        page += '<div class="card"><dl class="kv">%s</dl></div>' % kv
        page += '<h2>On the map</h2>' + TG + '<div id="edmap" data-ed="%s" data-nb="%s" role="img" aria-label="Map of %s"></div><p class="note" style="margin-top:8px">Tap a neighboring election district to open its page. Toggles draw the districts this election district is part of, with its own drawn heavier.</p>' % (e, ','.join(nb), esc(edlong(e)))
        page += sitehtml + racehtml + reghtml + nbhtml + nav
        page += '<p class="note">Election district lines are the NYC Board of Elections 2026 map. Poll site from the Board\'s Find My Poll Site, October 29, 2026. Races from the State Board of Elections certification of October 7, 2026.</p></div>' + MAPJS + LIVE + '</body></html>'
        d = os.path.join(ROOT, 'ed', e); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w').write(page)

    # every ED's ballot for /edresults/: race key -> race, ED -> race keys in ballot order
    RACES = {}; EDB = {}
    for n, t in QS: RACES['q%d' % n] = {'t': 'City Charter Question %d: %s' % (n, t), 'vf': 1, 'c': [['Yes', []], ['No', []]]}
    for e in sorted(byid):
        ks = []
        for r in races(byid[e]['properties']):
            k = race_key(r['t'])
            if not k: raise SystemExit('no race key for ' + r['t'])
            RACES.setdefault(k, {'t': r['t'], 'vf': r['vf'], 'c': [[c[0], c[1]] for c in r['c']]}); ks.append(k)
        EDB[e] = ks + ['q%d' % n for n, _ in QS]
    json.dump({'src': 'Races: New York State Board of Elections certification, October 7, 2026 (electionexplainer/ballot.json); election districts: NYC Board of Elections 2026 map',
               'races': RACES, 'ed': EDB}, open(os.path.join(ROOT, 'data/results/ed-ballots.json'), 'w'), separators=(',', ':'))
    print('ballots for', len(EDB), 'election districts,', len(RACES), 'races', file=sys.stderr)

    # index: by borough, then community board; an ED that crosses a line is listed under each board it is in
    BOORD = ['MANHATTAN', 'BRONX', 'BROOKLYN', 'QUEENS', 'STATEN ISLAND']
    bycb = {}
    for e in pick:
        sh = cbs_of(e)
        if not sh: bycb.setdefault(BONUM[byid[e]['properties']['bo']] + 'none', []).append((e, 1.0))
        for c, f in sh.items():
            if cbs is None or c in cbs: bycb.setdefault(c, []).append((e, f))
    secs = ''
    for b in BOORD:
        n = BONUM[b]; keys = sorted(k for k in bycb if k.startswith(n))
        if not keys: continue
        secs += '<section class="bo" id="%s"><h2 class="boh">%s</h2>' % (b.lower().replace(' ', '-'), esc(BOFULL[b]))
        for k in keys:
            name = 'Not in a community district' if k.endswith('none') else cbname(k)
            lst = bycb[k]
            secs += '<details class="cbk" id="cb%s"><summary><b>%s</b> <span class="pl">%d election districts</span></summary><div class="nb">%s</div></details>' % (
                k, esc(name), len(lst), ''.join('<a href="/ed/%s/" data-k="%s %d %d">%s%s</a>' % (e, e, int(e[:2]), int(e[2:]), esc(edlabel(e)), (' <span class="pl">%d%%</span>' % round(f * 100)) if f < 1 else '') for e, f in lst))
        secs += '</section>'
    where = 'New York City' if cbs is None else ', '.join(cbname(c) for c in cbs)
    XCSS = '.boh{font-size:1.3rem;margin:26px 0 8px}.cbk{background:#fff;border:1px solid var(--line);border-radius:12px;margin:0 0 8px;padding:10px 14px}.cbk summary{cursor:pointer}.cbk .nb{margin-top:10px}#q{width:100%;font:500 1rem DM Sans,sans-serif;padding:12px 14px;border:1.5px solid var(--line);border-radius:12px;background:#fff;color:var(--navy)}.jump{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 0}.jump a{font-weight:700;text-decoration:none;border:1.5px solid var(--line);border-radius:999px;padding:5px 12px;background:#fff}'
    FIND = """<script>(function(){var q=document.getElementById('q');q.addEventListener('input',function(){var v=q.value.trim().toLowerCase().replace(/[^0-9 ]/g,' ').replace(/\\s+/g,' ').trim();var parts=v.split(' ');
document.querySelectorAll('.cbk').forEach(function(d){var any=false;d.querySelectorAll('a').forEach(function(a){var k=a.dataset.k.split(' ');var ok=!v||(parts.length==1?(k[0]==parts[0]||k[0].indexOf(parts[0])==0):(k[1]==parts[0]&&k[2]==parts[1]));a.style.display=ok?'':'none';if(ok)any=true});d.style.display=any?'':'none';d.open=!!v&&any});
document.querySelectorAll('.bo').forEach(function(s){s.style.display=[].some.call(s.querySelectorAll('.cbk'),function(d){return d.style.display!='none'})?'':'none'})})})();</script>"""
    idx = HEAD + '<title>Election districts · bkcb6.app</title><meta name="description" content="Every election district in %s: its districts, representatives, poll site, ballot, results and map."><link rel="canonical" href="https://bkcb6.app/ed/">%s<style>%s%s</style></head><body><script src="/assets/site-bar.js?v=1" defer></script>' % (esc(where), FONTS, CSS, XCSS)
    idx += '<header><div class="in"><div class="eyebrow">Election districts · 2026 map</div><h1>Election districts in %s</h1><p class="lede">%s election districts, each with its own page: its districts and representatives, Election Day poll site, every race on its ballot with its results, and a map of everything it is part of.</p></div></header><div class="wrap">' % (esc(where), format(len(pick), ','))
    idx += '<input id="q" type="search" inputmode="numeric" placeholder="Election district, like 52046 or 52 46 (Assembly, then ED)" aria-label="Find an election district"><div class="jump">%s</div>' % ''.join('<a href="#%s">%s</a>' % (b.lower().replace(' ', '-'), esc(BOFULL[b])) for b in BOORD)
    idx += secs + '<p class="note">An election district that crosses a community district line is listed under each board it is in, with the share of its area in that board. Election district lines are the NYC Board of Elections 2026 map.</p></div>' + FIND + '</body></html>'
    os.makedirs(os.path.join(ROOT, 'ed'), exist_ok=True)
    open(os.path.join(ROOT, 'ed', 'index.html'), 'w').write(idx)
    print('wrote', len(pick), 'pages + index', file=sys.stderr)

if __name__ == '__main__':
    main()
