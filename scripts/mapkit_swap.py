#!/usr/bin/env python3
"""Swap Leaflet for Apple MapKit JS site-wide.

Every page keeps its Leaflet map code; /assets/mapkit-leaflet.js provides the Leaflet API on MapKit.
Replaces the Leaflet script tag (CDN, vendored or inlined) with the MapKit JS script plus the adapter,
and drops Leaflet plugin scripts the adapter covers (markercluster). Leaflet's CSS stays: it styles
popups, tooltips, controls and div icons.

Run from the repo root: python3 scripts/mapkit_swap.py [--dry]
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MK = '<script src="https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.js"></script><script src="/assets/mapkit-leaflet.js"></script>'
SKIP_DIRS = {'node_modules', '.git', '.github'}
SKIP_PATHS = ('assets/vendor/', 'app/data/site/vendor/')
PATTERNS = [
    (re.compile(r'<script src="https://unpkg\.com/leaflet@1\.9\.4/dist/leaflet\.js"[^>]*>[^<]{0,80}</script>'), MK),
    (re.compile(r'<script src="https://cdnjs\.cloudflare\.com/ajax/libs/leaflet/1\.9\.4/leaflet(?:\.min)?\.js"[^>]*></script>'), MK),
    (re.compile(r'<script src="/assets/vendor/leaflet-1\.9\.4/leaflet\.js"[^>]*></script>'), MK),
    (re.compile(r'<script src="https://unpkg\.com/leaflet\.markercluster@1\.5\.3/dist/leaflet\.markercluster\.js"[^>]*></script>\s*'), ''),
    # Leaflet source pasted into the page
    (re.compile(r'<script>\s*(?:/\* Leaflet 1\.9\.4 inlined \*/\s*)?/\* @preserve\s*\n \* Leaflet 1\.9\.4,[\s\S]*?//# sourceMappingURL=leaflet\.js\.map\s*</script>'), MK),
]
GENERATORS = ['scripts/build_app_web.py', 'scripts/build_sales_pages.py', 'scripts/build_gowanus_buildings.py',
              'scripts/build_atlanticyards_profiles.py', 'tools/build_cb6_directory.py', 'tools/bqe_kit/kit_main.js',
              'build_bid_businesses.py', 'build_culture_profiles.py', 'build_org_pages.py', 'make_venue_cards.py']

def swap(text):
    n = 0
    for rx, rep in PATTERNS:
        text, k = rx.subn(rep, text)
        n += k
    return text, n

def main():
    dry = '--dry' in sys.argv
    files = []
    for d, dirs, fs in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        rel = os.path.relpath(d, ROOT).replace(os.sep, '/') + '/'
        if any(rel.startswith(p) for p in SKIP_PATHS): continue
        for f in fs:
            if f.endswith('.html'): files.append(os.path.join(d, f))
    files += [os.path.join(ROOT, g) for g in GENERATORS if os.path.exists(os.path.join(ROOT, g))]
    changed = 0; tags = 0
    for f in files:
        try: s = open(f, encoding='utf-8').read()
        except UnicodeDecodeError: continue
        if 'leaflet' not in s: continue
        t, n = swap(s)
        if n:
            changed += 1; tags += n
            if not dry: open(f, 'w', encoding='utf-8').write(t)
    print(f'{"would change" if dry else "changed"} {changed} files, {tags} tags')
    left = []
    for f in files:
        try: s = open(f, encoding='utf-8').read()
        except UnicodeDecodeError: continue
        if dry: s = swap(s)[0]
        if re.search(r'<script[^>]*(leaflet@1\.9\.4/dist/leaflet|leaflet-1\.9\.4/leaflet\.js|libs/leaflet/1\.9\.4/leaflet|markercluster)', s) or 'Leaflet 1.9.4, a JS library' in s: left.append(os.path.relpath(f, ROOT))
    if left: print('still reference a Leaflet script:', len(left)); [print('  ' + x) for x in left[:20]]

if __name__ == '__main__': main()
