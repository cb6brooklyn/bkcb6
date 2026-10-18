#!/usr/bin/env python3
"""Every elected official's page and every community board's page get the same election and representation features.

Elected officials (data/profile-index.json, kind "official"):
  - the district map is the first thing under the header (moved up from below the events cards); Borough
    Presidents and District Attorneys get their borough's map and the Mayor, Public Advocate and Comptroller the
    city's, with the same layers (assets/profile-map.js);
  - "Who has held this seat" right under the map (assets/rep-history.js): every holder of a Council, Assembly,
    State Senate or Congressional district term by term with the community boards it covered, or every holder of a
    borough, city, state or federal office.
Community boards (kind "board"): "Who represented <board> on <date>" (any date since 2000) and a link to every
election in the board by election district (/electionhistory/?cb=<code>).
Idempotent: each block sits between markers and is rebuilt on every run. python3 scripts/profile_extras.py"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = '20261018b'
pages = json.load(open(os.path.join(ROOT, 'data/profile-index.json')))['pages']
BORON = {'1': 'Manhattan', '2': 'the Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
# offices with no district map: what map they get and what seat history
AT_LARGE = {
    'bpmanhattan': ('borough', '1', 'bp'), 'bpbronx': ('borough', '2', 'bp'), 'bpbrooklyn': ('borough', '3', 'bp'),
    'bpqueens': ('borough', '4', 'bp'), 'bpstatenisland': ('borough', '5', 'bp'),
    'dabragg': ('borough', '1', None), 'daclark': ('borough', '2', None), 'dagonzalez': ('borough', '3', None),
    'dakatz': ('borough', '4', None), 'damcmahon': ('borough', '5', None),
    'mayor': ('city', 'nyc', 'mayor'), 'publicadvocate': ('city', 'nyc', 'pa'), 'comptroller': ('city', 'nyc', 'comptroller'),
    'governor': (None, None, 'governor'), 'lieutenantgovernor': (None, None, 'lg'), 'attorneygeneral': (None, None, 'ag'),
    'statecomptroller': (None, None, 'statecomp'), 'ussenschumer': (None, None, 'ussenate:0'), 'ussengillibrand': (None, None, 'ussenate:1'),
}


def block_end(s, start):
    """index just past the </div> that closes the <div ...> opening at start"""
    depth, i = 0, start
    tag = re.compile(r'<(/?)div\b[^>]*>', re.I)
    for m in tag.finditer(s, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return m.end()
    raise ValueError('unbalanced div')


def strip_block(s, a, b):
    i = s.find(a)
    if i < 0:
        return s, None
    k = s.find(b, i)
    j = i
    while j > 0 and s[j - 1] == '\n':
        j -= 1
    return s[:j] + s[k + len(b):], s[i + len(a):k]


def add_script(s, src):
    base = src.split('?')[0]
    s = re.sub(r'<script src="' + re.escape(base) + r'\?v=[^"]*"></script>\s*', '', s)
    return s.replace('</body>', '<script src="%s"></script>\n</body>' % src, 1)


def map_html(chamber, district, title, sub):
    return ('<div class="sec"><h2>The district</h2><div class="mapttl">%s <span>%s</span></div>'
            '<div class="msearch"><input type="search" placeholder="Search an address to drop a pin" autocomplete="off"><button type="button">Find</button>'
            '<button type="button" class="mreset" data-map-reset>Reset</button></div>'
            '<div class="pmap" id="map" data-profile-map data-chamber="%s" data-district="%s"></div><div class="mstat" data-map-status></div>'
            '<button type="button" class="mtoggle" aria-expanded="false" data-map-toggle-btn><span style="flex:1;text-align:left">Add to the map</span><span class="marr">&#9660;</span></button>'
            '<div class="mtools" data-map-toggles hidden></div><div class="mhint">Tap the map anywhere to drop a pin and open that lot.</div></div>') % (title, sub, chamber, district)


done = {'official': 0, 'board': 0}
for path, kind in pages.items():
    k, _, ident = kind.partition(':')
    if k not in ('official', 'board'):
        continue
    slug = path.strip('/')
    f = os.path.join(ROOT, slug, 'index.html') if k == 'official' else os.path.join(ROOT, slug + '.html')
    s = open(f, encoding='utf-8').read()
    if k == 'official':
        # put any map block from an earlier run back where a fresh run expects it
        s, old = strip_block(s, '<!--seatmap-->', '<!--/seatmap-->')
        s, _ = strip_block(s, '<!--seathistory-->', '<!--/seathistory-->')
        h = s.find('<div class="phead')
        assert h >= 0, f
        if old is not None and 'data-added="1"' not in old:
            mapsec = old
        else:
            mapsec = None
            i = s.find('<h2>The district</h2>')
            if i >= 0:
                a = s.rfind('<div class="sec">', 0, i)
                b = block_end(s, a)
                mapsec, s = s[a:b], s[:a] + s[b:]
        h = s.find('<div class="phead')
        he = block_end(s, h)
        m = re.search(r'data-profile-map data-chamber="([^"]*)" data-district="([^"]*)"', mapsec or '')
        name = re.search(r'<h1>(.*?)</h1>', s).group(1)
        seat = re.search(r'<div class="pseat">(.*?)</div>', s).group(1)
        if m:
            seatdiv = '<div data-rep-seat="%s" data-district="%s"></div>' % (m.group(1), m.group(2))
            mapblock = mapsec
        else:
            ch, dist, office = AT_LARGE[slug]
            mapblock = ''
            if ch == 'borough':
                mapblock = map_html('borough', dist, 'The borough of ' + BORON[dist].replace('the Bronx', 'the Bronx'), seat).replace('<div class="sec">', '<div class="sec" data-added="1">', 1)
            elif ch == 'city':
                mapblock = map_html('city', 'nyc', 'New York City', seat).replace('<div class="sec">', '<div class="sec" data-added="1">', 1)
            if office is None:
                seatdiv = ''
            elif office.startswith('ussenate'):
                seatdiv = '<div data-rep-seat="ussenate" data-seat="%s"></div>' % office.split(':')[1]
            elif office == 'bp':
                seatdiv = '<div data-rep-seat="bp" data-boro="%s"></div>' % dist
            else:
                seatdiv = '<div data-rep-seat="%s"></div>' % office
        ins = ''
        if mapblock:
            ins += '<!--seatmap-->' + mapblock + '<!--/seatmap-->'
        if seatdiv:
            ins += '<!--seathistory--><div class="sec"><h2>Who has held this seat</h2>' + seatdiv + '</div><!--/seathistory-->'
        s = s[:he] + '\n' + ins + s[he:]  # the newline goes with the block (strip_block removes it)
        assert s.count('data-profile-map') <= 1, f
    else:
        s, _ = strip_block(s, '<!--rephistory-->', '<!--/rephistory-->')
        s, _ = strip_block(s, '<!--atlas-->', '<!--/atlas-->')
        while '<!--compplan-->' in s:
            s, _ = strip_block(s, '<!--compplan-->', '<!--/compplan-->')
        i = s.find('id="sec-results"')
        if i < 0:
            i = s.find('id="sec-health-profile"')
        a = s.rfind('<div', 0, i)
        blk = ('<!--rephistory--><div id="sec-rephistory" style="max-width:1400px;margin:16px auto;padding:0 16px">'
               '<div data-rep-board="%s"></div></div><!--/rephistory-->\n' % ident)
        atl = ('<!--atlas--><div id="sec-atlas" style="max-width:1400px;margin:16px auto;padding:0 16px">'
               '<h2 style="font-family:\'DM Sans\',sans-serif;font-weight:800;color:#0d1b4b;font-size:1.25rem;margin:0 0 8px">The district in numbers</h2>'
               '<iframe id="atlasFrame" src="/atlas/?embed=1&amp;cb=%s" title="Census Atlas: %s" loading="lazy" '
               'style="width:100%%;height:1150px;border:1px solid #e5e2db;border-radius:12px;background:#f8f7f4;display:block"></iframe>'
               '<script>window.addEventListener("message",function(e){if(e.data&&e.data.atlasH){var f=document.getElementById("atlasFrame");if(f&&e.source===f.contentWindow)f.style.height=(e.data.atlasH+4)+"px";}});</script>'
               '</div><!--/atlas-->\n') % (ident, ident)
        cpb = ''
        if ident.startswith('3') and int(ident[1:]) <= 18:
            lbl = 'CB6' if ident == '306' else 'BKCB%d' % int(ident[1:])
            cpb = ('<!--compplan--><div id="sec-compplan" style="max-width:1400px;margin:16px auto;padding:0 16px">'
                   '<h2 style="font-family:\'DM Sans\',sans-serif;font-weight:800;color:#0d1b4b;font-size:1.25rem;margin:0 0 8px">%s in the Comprehensive Plan for Brooklyn</h2>'
                   '<iframe id="cpFrame" src="/bkcompplan/?embed=1&amp;cb=%s" title="%s in the Comprehensive Plan for Brooklyn" loading="lazy" '
                   'style="width:100%%;height:2600px;border:1px solid #e5e2db;border-radius:12px;background:#fff;display:block"></iframe>'
                   '<script>window.addEventListener("message",function(e){if(e.data&&e.data.cpH){var f=document.getElementById("cpFrame");if(f&&e.source===f.contentWindow)f.style.height=(e.data.cpH+4)+"px";}});</script>'
                   '</div><!--/compplan-->\n') % (lbl, ident, lbl)
        s = s[:a] + atl + cpb + blk + s[a:]
    s = add_script(s, '/assets/rep-history.js?v=' + V)
    s = re.sub(r'/assets/profile-map\.js\?v=[0-9a-z]+', '/assets/profile-map.js?v=' + V, s)
    open(f, 'w', encoding='utf-8').write(s)
    done[k] += 1
# the five borough pages: the borough in the Census Atlas, before the description
for d, slug in (('1', 'manhattan'), ('2', 'bronx'), ('3', 'brooklyn'), ('4', 'queens'), ('5', 'statenisland')):
    f = os.path.join(ROOT, slug + '.html')
    s = open(f, encoding='utf-8').read()
    s, _ = strip_block(s, '<!--atlas-->', '<!--/atlas-->')
    i = s.find('id="sec-description"')
    a = s.rfind('<', 0, i)
    nm = BORON[d].replace('the Bronx', 'The Bronx')
    atl = ('<!--atlas--><div id="sec-atlas" style="max-width:1400px;margin:16px auto;padding:0 16px">'
           '<h2 style="font-family:\'DM Sans\',sans-serif;font-weight:800;color:#0d1b4b;font-size:1.25rem;margin:0 0 8px">%s in numbers</h2>'
           '<iframe id="atlasFrame" src="/atlas/?embed=1&amp;boro=%s" title="Census Atlas: %s" loading="lazy" '
           'style="width:100%%;height:1150px;border:1px solid #e5e2db;border-radius:12px;background:#f8f7f4;display:block"></iframe>'
           '<script>window.addEventListener("message",function(e){if(e.data&&e.data.atlasH){var f=document.getElementById("atlasFrame");if(f&&e.source===f.contentWindow)f.style.height=(e.data.atlasH+4)+"px";}});</script>'
           '</div><!--/atlas-->\n') % (nm, d, nm)
    s = s[:a] + atl + s[a:]
    open(f, 'w', encoding='utf-8').write(s)
    done['borough'] = done.get('borough', 0) + 1
print(done)
