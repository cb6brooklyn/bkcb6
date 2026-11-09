#!/usr/bin/env python3
"""Every school's profile (school/*.html) gets the map the other profiles have: the school pinned in its school district,
with the district's overlaps, zoning and land use, and every section but the bio and the map folded (assets/fold-secs.js).
The school's place comes from its DBN in data/nyc_school_points.json (NYC Department of Education), else
data/nyc-schools.geojson; a school with neither keeps no map. The school district line links to the district's and its
Community Education Council's profiles. Idempotent. Usage: python3 scripts/school_maps.py"""
import glob, html, json, os, re
from shapely.geometry import shape
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
pts = {}
for r in json.load(open('data/nyc_school_points.json')):
    if r.get('dbn') and r.get('lat'): pts[r['dbn'].upper()] = (r['lat'], r['lon'], r.get('school_district'))
for f in json.load(open('data/nyc-schools.geojson'))['features']:
    k = (f['properties'].get('ats') or '').upper()
    if k and k not in pts and f.get('geometry'):
        c = shape(f['geometry']).centroid; pts[k] = (round(c.y, 6), round(c.x, 6), str(int(k[:2])) if k[:2].isdigit() else None)
HEADADD = ('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>\n'
           '<script src="https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.js"></script><script src="/assets/mapkit-leaflet.js"></script>\n')
MAP = ('  <div class="sec"><h2>Where it is</h2><div class="bio"><div class="mapinner"><div class="mapttl">%s <span>the school and School District %s</span></div>'
       '<div class="msearch"><input type="search" placeholder="Search an address to drop a pin" autocomplete="off"><button type="button">Find</button><button type="button" class="mreset" data-map-reset>Reset</button></div>'
       '<div class="pmap" data-profile-map data-chamber="school" data-district="%s" data-point-lat="%.6f" data-point-lng="%.6f" data-point-zoom="17"></div>'
       '<div class="mstat" data-map-status></div><button type="button" class="mtoggle" aria-expanded="false" data-map-toggle-btn><span style="flex:1;text-align:left">Add to the map</span><span class="marr">&#9660;</span></button>'
       '<div class="mtools" data-map-toggles hidden></div><div class="mhint">Tap the map anywhere to drop a pin and open that lot.</div></div></div></div>\n')
n_map = n_fold = n_nopt = 0
for p in sorted(glob.glob('school/*.html')):
    s = open(p, encoding='utf-8').read(); s0 = s
    if 'data-profile-map' not in s:
        m = re.search(r'<span class="k">DBN</span><span class="v">([0-9A-Z]{5,6})</span>', s)
        pt = pts.get(m.group(1).upper()) if m else None
        sd = re.search(r'<span class="k">School district</span><span class="v">(\d+)</span>', s)
        dist = (sd.group(1) if sd else None) or (pt[2] if pt else None)
        if pt and dist and os.path.exists('data/districts/school-%s.geojson' % int(dist)):
            ad = re.search(r'<span class="k">Address</span><span class="v">([^<,]+)', s)
            first = re.search(r'<div class="sec">.*?</div></div>\n?', s, re.S)
            if first:
                s = s[:first.end()] + ('\n' if not first.group(0).endswith('\n') else '') + MAP % (ad.group(1) if ad else '', int(dist), int(dist), pt[0], pt[1]) + s[first.end():]
                s = s.replace('/assets/place-profile.css?v=1', '/assets/place-profile.css?v=2')
                if 'mapkit-leaflet.js' not in s: s = s.replace('</head>', HEADADD + '</head>', 1)
                if 'profile-map.js' not in s: s = s.replace('</body>', '<script src="/assets/profile-map.js?v=20261109a"></script>\n</body>', 1)
                n_map += 1
        else:
            n_nopt += 1
    if sd := re.search(r'<span class="k">School district</span><span class="v">(\d+)</span>', s):
        k = int(sd.group(1))
        if 1 <= k <= 32:
            s = s.replace(sd.group(0), '<span class="k">School district</span><span class="v"><a href="/school-district-%d/">District %d</a> &middot; <a href="/cec-district-%d/">CEC %d</a></span>' % (k, k, k, k), 1)
    if 'fold-secs.js' not in s:
        s = s.replace('</body>', '<script src="/assets/fold-secs.js?v=20261109a"></script>\n</body>', 1); n_fold += 1
    if s != s0: open(p, 'w', encoding='utf-8').write(s)
print(n_map, 'maps added;', n_nopt, 'schools with no place in the data (no map);', n_fold, 'pages folded')
