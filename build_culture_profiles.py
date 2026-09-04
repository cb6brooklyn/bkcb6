#!/usr/bin/env python3
"""Write a /c/ profile page for any culture place that has a logo and an address
but no profile yet. The template is copied from the pages already on the site so
new pages are indistinguishable from the existing ones."""
import json, os, re, html, urllib.parse

TYPE_LINE = {
    'museum': ('&#127963; Museum', 'A museum. Collections, exhibitions and public programming.'),
    'library': ('&#128218; Library', 'A public library branch.'),
    'film': ('&#127916; Movie theater', 'A movie theater.'),
    'theatre': ('&#127917; Theatre', 'A theatre.'),
    'performing arts': ('&#127925; Performing arts', 'A performing arts venue.'),
    'park': ('&#127795; Park', 'A park or open space.'),
}
BORO_LONG = {'Bronx': 'The Bronx', 'Brooklyn': 'Brooklyn', 'Manhattan': 'Manhattan',
             'Queens': 'Queens', 'Staten Island': 'Staten Island'}
BORO_DIGIT = {'MN': '1', 'BX': '2', 'BK': '3', 'QN': '4', 'SI': '5'}
CD_FILES = set(f[3:-8] for f in os.listdir('data/districts') if f.startswith('cb-') and f.endswith('.geojson'))
CB_LONG = {'BX': 'The Bronx', 'BK': 'Brooklyn', 'MN': 'Manhattan',
           'QN': 'Queens', 'SI': 'Staten Island'}


def slug(name):
    s = name.lower()
    s = s.replace('&', ' and ')
    s = re.sub(r"[’']", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


def kv(k, v):
    return '<li><span class="k">%s</span><span class="v">%s</span></li>' % (k, v)


def page(p):
    e = html.escape
    name = e(p['name'])
    addr = e(p.get('address', ''))
    sl = slug(p['name'])
    icon, blurb = TYPE_LINE.get(p['type'], ('&#128205; Place', 'A cultural place.'))
    boro = BORO_LONG.get(p.get('boro_name'), p.get('boro_name', ''))
    desc = '%s at %s.' % (name, addr)

    rows = [kv('Address', addr)]
    if p.get('aka_line'):
        rows.append(kv('Also known as', e(p['aka_line'])))
    if p.get('tel'):
        rows.append(kv('Phone', '<a href="tel:%s">%s</a>' %
                       (re.sub(r'\D', '', p['tel']), e(p['tel']))))
    if p.get('url'):
        host = re.sub(r'^https?://(www\.)?', '', p['url']).rstrip('/')
        rows.append(kv('Website', '<a href="%s" target="_blank" rel="noopener">%s &#8599;</a>'
                       % (e(p['url']), e(host))))
    cb = p.get('cb', '')
    if cb:
        m = re.match(r'([A-Z]{2})CB(\d+)', cb)
        if m:
            rows.append(kv('District', '%s Community Board %s'
                           % (CB_LONG.get(m.group(1), ''), m.group(2))))
    if p.get('zoning'):
        rows.append(kv('Zoned', e(p['zoning'])))
    if p.get('land_use_label'):
        rows.append(kv('Land use', e(p['land_use_label'])))
    if p.get('year_built'):
        rows.append(kv('Built', str(p['year_built'])))
    if p.get('owner'):
        rows.append(kv('Owner', e(p['owner'])))

    chips = []
    if p.get('lot'):
        chips.append('<a class="chip hot" href="%s">Zoning and land use for this lot</a>' % e(p['lot']))
    if p.get('url'):
        chips.append('<a class="chip" href="%s" target="_blank" rel="noopener">Official site &#8599;</a>' % e(p['url']))
    chips.append('<a class="chip" href="/culture-map.html">The culture map</a>')
    chips.append('<a class="chip" href="/citywide-search.html">Search an address</a>')

    logo = ''
    if p.get('logo'):
        logo = ('<div class="sec"><img src="%s" alt="%s" '
                'style="max-height:96px;max-width:min(100%%,320px);width:auto;display:block;'
                'object-fit:contain;border-radius:6px"></div>') % (e(p['logo']), name)

    # A handful of large parks carry a joint-interest-area code in `cd` that has
    # no boundary file, so fall back to the board in `cb`, then to no boundary.
    cd_code = str(p.get('cd') or '')
    if cd_code not in CD_FILES:
        m = re.match(r'([A-Z]{2})S?CB(\d+)', p.get('cb', '') or '')
        cd_code = (BORO_DIGIT.get(m.group(1), '') + m.group(2).zfill(2)) if m else ''
    if cd_code not in CD_FILES:
        cd_code = ''

    mapsec = ''
    if p.get('lat') and p.get('lng'):
        icon_attr = ''
        if p.get('logo'):
            icon_attr = (' data-point-icon="%s" data-point-icon-w="200" data-point-icon-h="200"'
                         % e(p['logo']))
        mapsec = (
            '  <div class="sec"><h2>Where it is</h2>'
            '<details class="mapwrap" open><summary>Map of the block'
            '<span class="msub">zoning, boundary, overlaps, land use</span>'
            '<span class="marr2">&#9660;</span></summary><div class="mapinner">'
            '<div class="mapttl">%(addr)s <span>the place, its block and the zoning around it</span></div>'
            '<div class="msearch"><input type="search" placeholder="Search an address to drop a pin" autocomplete="off">'
            '<button type="button">Find</button>'
            '<button type="button" class="mreset" data-map-reset>Reset</button></div>'
            '<div class="pmap" id="map" data-profile-map%(dist)s '
            'data-start-zoning="1" data-point-lat="%(lat)s" data-point-lng="%(lng)s" '
            'data-point-zoom="17"%(icon)s></div>'
            '<div class="mstat" data-map-status></div>'
            '<button type="button" class="mtoggle" aria-expanded="false" data-map-toggle-btn>'
            '<span style="flex:1;text-align:left">Add to the map</span><span class="marr">&#9660;</span></button>'
            '<div class="mtools" data-map-toggles hidden></div>'
            '<div class="mhint">Tap the map anywhere to drop a pin and open that lot.</div>'
            '</div></details></div>\n'
        ) % dict(addr=addr, lat=p['lat'], lng=p['lng'], icon=icon_attr,
                 dist=(' data-chamber="cb" data-district="%s"' % cd_code) if cd_code else '')

    cal_q = urllib.parse.quote(p['name'])
    events = (
        '  <div class="sec"><h2>Events</h2><div class="bio">'
        '<p>Upcoming events at %(n)s, filtered out of the bkcb6.app calendar. '
        'The calendar covers community board meetings, public hearings and neighbourhood '
        'programming across the five boroughs.</p>'
        '<div class="chips">'
        '<a class="chip hot" href="/calendar.html?q=%(q)s">Events at %(n)s</a>'
        '<a class="chip" href="/calendar.html">The full bkcb6.app calendar</a>'
        '</div></div></div>\n'
    ) % dict(n=name, q=cal_q)

    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(name)s &mdash; bkcb6.app</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="https://bkcb6.app/c/%(slug)s">
<meta property="og:site_name" content="Brooklyn Community Board 6"><meta property="og:type" content="website">
<meta property="og:title" content="%(name)s"><meta property="og:description" content="%(desc)s">
<meta property="og:url" content="https://bkcb6.app/c/%(slug)s">
<meta property="og:image" content="https://bkcb6.app/og-culture.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://bkcb6.app/og-culture.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>\n<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>\n<link rel="stylesheet" href="/assets/place-profile.css?v=2">
</head><body>
<div class="pwrap">
  <div class="phead">
    <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/culture-map.html" style="color:inherit">Culture</a></div>
    <h1>%(name)s</h1>
    <div class="pseat">%(icon)s &middot; %(boro)s</div>
  </div>
%(logo)s%(mapsec)s  <div class="sec"><h2>What it is</h2><div class="bio"><p>%(blurb)s</p></div></div>
  <div class="sec"><h2>Details</h2><div class="bio"><ul class="kv">%(rows)s</ul><div class="chips">%(chips)s</div></div></div>
%(events)s  <div class="pfoot">Location and category from the culture dataset behind the bkcb6.app culture map. Zoning, land use and ownership come from the Department of City Planning and are shown on the lot page.<br>
  <a href="/culture-map.html">The culture map</a> &middot; <a href="/citywide-search.html">Search any address</a> &middot; <a href="/">bkcb6.app</a></div>
</div>
<script src="/assets/profile-map.js?v=20260904b"></script>
</body></html>""" % dict(name=name, desc=e(desc), slug=sl, icon=icon, boro=boro,
                         blurb=blurb, rows=''.join(rows), chips=''.join(chips), logo=logo,
                         events=events, mapsec=mapsec)


def main():
    path = 'data/culture-places.json'
    d = json.load(open(path))
    made = []
    for p in d:
        if not p.get('logo') or not p.get('address'):
            continue
        sl = slug(p['name'])
        out = 'c/%s.html' % sl
        with open(out, 'w') as f:
            f.write(page(p))
        p['profile'] = '/c/%s' % sl
        made.append(out)
    json.dump(d, open(path, 'w'), ensure_ascii=False, indent=1)
    print('wrote %d profile pages' % len(made))
    for m in made:
        print('  ', m)


if __name__ == '__main__':
    main()
