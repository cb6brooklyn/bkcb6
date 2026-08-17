#!/usr/bin/env python3
"""
Builds one address card page per stadium.

Each page is NOT an embed and NOT a link to a search result. It carries the same
stylesheet and the same script the citywide address search uses, and triggers
that script for its own fixed address on load. The card is therefore produced by
exactly the same code path as a manual search, so it cannot drift from it.

Below the card each page offers two ways out: back to the stadium hub, and a
citywide address search.

Usage: python3 make_venue_cards.py
"""
import html
import json
import os
import re

SRC = 'cs.html'            # a saved copy of the live citywide-search.html
# Pages live at the site root, not in a subfolder: the search script fetches its
# supporting data with relative paths (data/..., transport-data/...), which would
# resolve against the subfolder and silently drop the parks, schools, libraries
# and transit sections of the card.
OUT = '.'
PREFIX = 'stadium-'
VENUES = json.load(open('venues_final.json'))

src = open(SRC).read()
CSS = re.search(r'<style[^>]*>(.*?)</style>', src, re.S).group(1)
JS = re.search(r'assets/citywide-full-profile-search\.js\?v=[^"]+', src).group(0)

EXTRA_CSS = """
/* venue card chrome */
body{background:var(--off,#f8f7f4)}
.vwrap{max-width:760px;margin:0 auto;background:#fff;min-height:100vh;
  border-left:1px solid var(--border,#e5e2db);border-right:1px solid var(--border,#e5e2db)}
.vhead{background:var(--navy,#0d1b4b);color:#fff;padding:18px 16px 20px;border-bottom:4px solid var(--orange,#f47920)}
.vcrumb{font-family:'DM Mono',monospace;font-size:.62rem;text-transform:uppercase;letter-spacing:.12em;color:rgba(255,255,255,.55)}
.vcrumb a{color:rgba(255,255,255,.75);text-decoration:none}
.vcrumb a:hover{color:#fff}
.vhead h1{font-size:1.7rem;font-weight:900;letter-spacing:-.02em;margin:6px 0 0;line-height:1.15;color:#fff}
.vhead h1 span{color:var(--orange,#f47920)}
.vsub{font-family:'DM Mono',monospace;font-size:.75rem;color:rgba(255,255,255,.62);margin-top:5px}
.vstatus{padding:14px 16px;font-family:'DM Mono',monospace;font-size:.7rem;color:#6b6760}
.vout{padding:6px 12px 4px}
.vrowt{font-family:'DM Mono',monospace;font-size:.62rem;text-transform:uppercase;letter-spacing:.11em;color:#6b6760;margin:14px 0 8px}
.vbtns{display:flex;flex-wrap:wrap;gap:7px}
.vb{display:inline-flex;align-items:center;gap:7px;padding:11px 16px;border:2px solid var(--navy,#0d1b4b);
  border-radius:24px;background:#fff;color:var(--navy,#0d1b4b);font-size:.85rem;font-weight:800;text-decoration:none}
.vb:hover{background:#f2f4fb}
.vb.hot{background:var(--orange,#f47920);border-color:var(--orange,#f47920);color:#fff}
.vsearch{margin:6px 12px 0;padding:13px 14px;border:1px solid var(--border,#e5e2db);border-radius:10px;background:#fbfaf7}
.vsearch .vl{font-family:'DM Mono',monospace;font-size:.6rem;text-transform:uppercase;letter-spacing:.11em;color:#6b6760;margin-bottom:8px}
.vsearch form{display:flex;gap:7px;flex-wrap:wrap}
.vsearch input{flex:1;min-width:180px;font-family:'DM Sans',sans-serif;font-size:.92rem;padding:11px 12px;
  border:1px solid var(--border,#e5e2db);border-radius:8px;background:#fff;color:#1b1b1b}
.vsearch button{font-family:'DM Mono',monospace;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;
  padding:11px 16px;border-radius:8px;border:0;background:var(--orange,#f47920);color:#fff;font-weight:500;cursor:pointer}
.vfoot{padding:16px;font-family:'DM Mono',monospace;font-size:.66rem;color:#6b6760;line-height:1.6;
  border-top:1px solid var(--border,#e5e2db);margin-top:10px}
.vfoot a{color:var(--navy,#0d1b4b)}
/* the search form the script needs, but which this page drives itself */
.driver{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
"""

TPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} &mdash; zoning and districts</title>
<meta name="description" content="The full address card for {addr_h}, better known as {name}: zoning, land use, community board, council and election districts, landmark status and nearby civic services.">
<link rel="canonical" href="https://bkcb6.app/stadium-{slug}">
<meta property="og:site_name" content="Brooklyn Community Board 6">
<meta property="og:type" content="website">
<meta property="og:title" content="{name} &mdash; zoning and districts">
<meta property="og:description" content="Zoning, land use, community board and every district line for {addr_h}.">
<meta property="og:url" content="https://bkcb6.app/stadium-{slug}">
<meta property="og:image" content="https://bkcb6.app/tiles/stadium-zoning.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700;800;900&display=swap" rel="stylesheet">
<style>
{css}
{extra}
</style>
</head>
<body>
<div class="vwrap">

  <div class="vhead">
    <div class="vcrumb"><a href="/">bkcb6.app</a> &middot; <a href="/stadium-zoning.html">Stadium zoning</a></div>
    <h1>{name_h1}</h1>
    <div class="vsub">{addr_h} &middot; {teams_h}</div>
  </div>

  <!-- The script the citywide search uses needs these controls. This page fills
       them in and submits on load, so the card below is produced by exactly the
       same code path as a manual search. -->
  <div class="driver">
    <label for="citywide-borough-address-input">NYC address</label>
    <input id="citywide-borough-address-input" type="search" value="{addr_attr}">
    <button id="citywide-borough-address-search-btn" type="button">Search address</button>
  </div>
  <div id="citywide-borough-address-search-status" class="vstatus" role="status" aria-live="polite">Loading the address card for {name_h}&hellip;</div>
  <div id="citywide-borough-address-search-result" class="result-wrap" hidden></div>

  <div class="vout">
    <div class="vrowt">Keep going</div>
    <div class="vbtns">
      <a class="vb hot" href="/stadium-zoning.html">&larr; Back to stadium hub</a>
      <a class="vb" href="/citywide-search.html">Search all citywide properties</a>
      <a class="vb" href="/jointinterest.html">Joint interest areas</a>
    </div>
  </div>

  <div class="vsearch">
    <div class="vl">Or look up any address in the city</div>
    <form id="vform">
      <input id="vinput" type="search" placeholder="e.g. 250 Baltic Street, Brooklyn" autocomplete="street-address" aria-label="NYC address">
      <button type="submit">Search</button>
    </form>
  </div>

  <div class="vfoot">
    Built on public data from the Department of City Planning and NYC Open Data. This page runs the same
    citywide address search used across the site, fixed to this address.<br>
    <a href="/stadium-zoning.html">Stadium zoning</a> &middot;
    <a href="/citywide-search.html">Search any address</a> &middot;
    <a href="/">bkcb6.app</a>
  </div>

</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="/{js}"></script>
<script>
(function(){{
  // A venue card is its own stable page. The search script stamps ?address=
  // onto the URL after it runs; undo that so the address stays clean.
  var CLEAN = location.pathname;
  if (history.replaceState){{
    var keep = setInterval(function(){{
      if (location.search) history.replaceState(null, '', CLEAN);
    }}, 250);
    setTimeout(function(){{ clearInterval(keep); }}, 20000);
  }}

  // Fire the same search the button would, once the script has bound to it.
  var tries = 0;
  function go(){{
    var input = document.getElementById('citywide-borough-address-input');
    var btn = document.getElementById('citywide-borough-address-search-btn');
    if (!input || !btn) return;
    input.value = {addr_js};
    btn.click();
  }}
  function ready(){{
    tries++;
    var res = document.getElementById('citywide-borough-address-search-result');
    go();
    // Retry briefly in case the script binds its handler after this runs.
    if (tries < 4 && (!res || !res.children.length)) setTimeout(ready, 700);
  }}
  if (document.readyState === 'complete') setTimeout(ready, 120);
  else window.addEventListener('load', function(){{ setTimeout(ready, 120); }});

  var f = document.getElementById('vform');
  if (f) f.addEventListener('submit', function(e){{
    e.preventDefault();
    var v = document.getElementById('vinput').value.trim();
    if (v) location.href = '/citywide-search.html?address=' + encodeURIComponent(v);
  }});
}})();
</script>
</body>
</html>
"""


def build():
    os.makedirs(OUT, exist_ok=True)
    for v in VENUES:
        name_h = html.escape(v['name'])
        # split the name so the last word can take the orange accent
        parts = v['name'].rsplit(' ', 1)
        h1 = (html.escape(parts[0]) + ' <span>' + html.escape(parts[1]) + '</span>') \
            if len(parts) == 2 else name_h
        page = TPL.format(
            css=CSS, extra=EXTRA_CSS, js=JS, slug=v['slug'],
            name=name_h, name_h=name_h, name_h1=h1,
            addr_h=html.escape(v['addr']),
            addr_attr=html.escape(v['addr'], quote=True),
            addr_js=json.dumps(v['addr']),
            teams_h=html.escape(v['teams']),
        )
        path = os.path.join(OUT, PREFIX + v['slug'] + '.html')
        open(path, 'w').write(page)
        print('  wrote', path, len(page), 'bytes')


if __name__ == '__main__':
    build()
