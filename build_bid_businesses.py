#!/usr/bin/env python3
"""Build a profile page for every business in the Park Slope 5th Avenue BID
directory that has an address we could resolve.

Each page is the same wrapper Bark Slope Salon uses: a header naming the
business and its address, what the BID tells us about it, and then the lot
record rendered by the citywide address search, same code path as a manual
search. Nothing on the page is invented; every field comes from the BID's own
directory or from the card the search draws.
"""
import json, os, re, html

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'data/bids/park-slope-5th-avenue-businesses.json')
CSS = open(os.path.join(ROOT, 'assets/biz-profile.css'), encoding='utf-8').read()
JSV = 'v=20260827-osh'
OG = 'https://bkcb6.app/og/bids/park-slope-5th-avenue.jpg?v=2'

D = json.load(open(DATA, encoding='utf-8'))
CATS, BLOCKS = D['cats'], D['blocks']


def esc(s):
    return html.escape(str(s or ''), quote=True)


def pretty_url(u):
    """Show the host, not a wall of query string."""
    u = re.sub(r'^https?://', '', u or '')
    u = re.sub(r'^www\.', '', u)
    return u.rstrip('/')[:44]


def head_split(addr):
    """427 5 Avenue -> ('427', '5th Avenue') so the number leads like Bark Slope."""
    parts = (addr or '').split(' ', 1)
    if len(parts) == 2 and parts[0].rstrip('A-Za-z').isdigit():
        street = parts[1]
        for a, b in (('5 Avenue', '5th Avenue'), ('5th Ave', '5th Avenue'),
                     ('5 Ave', '5th Avenue')):
            if street == a:
                street = b
        return parts[0], street
    return '', addr or ''


def page(e):
    name, addr = e['n'], e.get('a', '')
    num, street = head_split(addr)
    cats = [CATS.get(c, c) for c in e.get('c', [])]
    blk = BLOCKS[e['b']] if e.get('b') is not None and e['b'] < len(BLOCKS) else None
    full = addr + ', Brooklyn, NY'
    desc = ('%s at %s in Park Slope, in the Park Slope 5th Avenue BID. '
            'The full lot record: zoning, land use, ownership, community board '
            'and every district line.' % (name, addr))

    rows = []
    if addr:
        rows.append(('Address', esc(addr) + '<br>Brooklyn, NY'))
    if e.get('p'):
        tel = ''.join(ch for ch in e['p'] if ch.isdigit() or ch == '+')
        rows.append(('Phone', '<a href="tel:%s">%s</a>' % (esc(tel), esc(e['p']))))
    if e.get('w'):
        rows.append(('Website',
                     '<a href="%s" target="_blank" rel="noopener">%s &#8599;</a>'
                     % (esc(e['w']), esc(pretty_url(e['w'])))))
    if e.get('h'):
        rows.append(('Hours', '<span class="hrs">%s</span>'
                              '<span class="hsrc">from OpenStreetMap</span>' % esc(e['h'])))
    if cats:
        rows.append(('Listed as', esc(' &middot; '.join(cats)).replace('&amp;', '&')))
    if blk:
        rows.append(('Block', '%s to %s' % (esc(blk['f']), esc(blk['t']))))
    rows.append(('District', '<a href="/bid-park-slope-5th-avenue/">'
                             'Park Slope 5th Avenue BID</a>'))
    kv = ''.join('<li><span class="k">%s</span><span class="v">%s</span></li>' % (k, v)
                 for k, v in rows)

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} &middot; {addr} &mdash; bkcb6.app</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://bkcb6.app/biz-{slug}">
<meta property="og:site_name" content="Brooklyn Community Board 6">
<meta property="og:type" content="website">
<meta property="og:title" content="{name} &middot; {addr}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://bkcb6.app/biz-{slug}">
<meta property="og:image" content="{og}">
<meta property="og:image:secure_url" content="{og}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Park Slope 5th Avenue BID on bkcb6.app">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{og}">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,700;9..40,800;9..40,900&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/biz-profile.css?v=1">
</head>
<body>
<div class="vwrap">
  <div class="vhead">
    <div class="vcrumb"><a href="/">bkcb6.app</a> &middot; <a href="/bid-park-slope-5th-avenue/">Park Slope 5th Avenue BID</a></div>
    <h1>{name}</h1>
    <div class="vsub">{head}</div>
  </div>

  <div class="vdetail">
    <div class="vdt">What the BID lists</div>
    <ul class="kv">{kv}</ul>
  </div>

  <div class="vcard">
    <div class="vsearch">
      <input id="citywide-borough-address-input" type="search">
      <button id="citywide-borough-address-search-btn" type="button">Search</button>
      <div id="citywide-borough-address-search-status" class="status" role="status" aria-live="polite"></div>
    </div>
    <div class="vload" id="vLoad"><span class="vspin"></span>Pulling the lot record</div>
    <div id="citywide-borough-address-search-result" class="result-wrap" hidden></div>
  </div>

  <div class="vfoot">
    <div class="vft">Go on</div>
    <div class="vbtns">
      <a class="vb hot" href="/bid-park-slope-5th-avenue/">Every business in the district</a>
      <a class="vb" href="/citywide-search.html">Search any address in the city</a>
      <a class="vb" href="/zoning">What the zoning means</a>
    </div>
  </div>

  <div class="vsrc">
    Name, address, phone and category come from the <a href="https://parkslopefifthavenuebid.com/business-categories/" target="_blank" rel="noopener">BID&rsquo;s own directory</a>. The block comes from the Department of City Planning street centerline. Opening hours and some websites come from OpenStreetMap, matched by name within 350 feet of the listed address, so they are as current as the last person to edit them there. The lot card below is rendered by the same citywide address search used across the site: districts from Geoclient, zoning and land use from PLUTO, landmark status from the LPC database. A business shown at an address is a marker for that address, not a statement about the whole lot, and not an endorsement by Community Board 6.
  </div>
</div>

<script src="/assets/citywide-full-profile-search.js?{jsv}"></script>
<script>
(function(){{
  var ADDR = "{full}";
  function run(){{
    var input = document.getElementById('citywide-borough-address-input');
    var btn = document.getElementById('citywide-borough-address-search-btn');
    if (!input || !btn) return;
    input.value = ADDR;
    btn.click();
  }}
  var tries = 0;
  (function wait(){{
    var input = document.getElementById('citywide-borough-address-input');
    if (input && input.dataset.fullProfileBound === 'true'){{ run(); watch(); return; }}
    if (tries > 120){{
      document.getElementById('vLoad').innerHTML =
        'The card could not be started. <a href="/citywide-search.html?address=' +
        encodeURIComponent(ADDR) + '">Open it in the citywide search</a>.';
      return;
    }}
    tries++; setTimeout(wait, 100);
  }})();
  function watch(){{
    var res = document.getElementById('citywide-borough-address-search-result');
    var load = document.getElementById('vLoad');
    var n = 0;
    var t = setInterval(function(){{
      n++;
      if (res && !res.hidden && res.innerHTML.length > 200){{ load.style.display = 'none'; clearInterval(t); }}
      else if (n > 80){{
        load.innerHTML = 'The card did not load. <a href="/citywide-search.html?address=' +
          encodeURIComponent(ADDR) + '">Open it in the citywide search</a>.';
        clearInterval(t);
      }}
    }}, 250);
  }}
}})();
</script>
</body>
</html>
""".format(name=esc(name), addr=esc(addr), desc=esc(desc), slug=e['s'], og=OG,
           head=esc(addr + ', Brooklyn, NY 11215') if addr else esc(name),
           kv=kv, full=esc(full), jsv=JSV)


built = 0
for e in D['biz']:
    if 's' not in e:
        continue
    d = os.path.join(ROOT, 'biz-' + e['s'])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(page(e))
    built += 1

print('built', built, 'business profiles')
print('skipped', sum(1 for e in D['biz'] if 's' not in e), 'with no resolvable address')
