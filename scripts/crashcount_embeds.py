#!/usr/bin/env python3
"""CrashCount's crash map and crash counter on every council, Assembly, Senate and community board profile.

Each of those profiles already links to its district on crashcount.nyc in its traffic crashes section. This adds,
right under that link, the CrashCount block (assets/crashcount-embed.js): the district's crash map and CrashCount's
published counter embed, loaded when it is opened. Idempotent: run again after rebuilding a profile.
"""
import glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYER = {'council-district': 'council', 'assembly-district': 'assembly', 'senate-district': 'senate', 'community-board': 'community'}
LINK = re.compile(r'<a href="https://crashcount\.nyc/(council-district|assembly-district|senate-district|community-board)/(\d+)/\?source=bkcb6\.app"[^>]*>.*?</a>(\.?)</p>', re.S)
TAG = '<script src="/assets/crashcount-embed.js?v=20261113"></script>'

files = []
for pat in ('am*/index.html', 'sen*/index.html', 'cm*/index.html', 'cb-*.html', 'bk/cb-*.html'):
    files += glob.glob(os.path.join(ROOT, pat))
done = 0
for p in sorted(files):
    s = open(p, encoding='utf-8').read()
    if 'data-crashcount' in s:
        continue
    m = LINK.search(s)
    if m:
        path, n = m.group(1), m.group(2)
        block = '<div data-crashcount data-layer="%s" data-id="%s" data-path="%s/%s/"></div>' % (LAYER[path], n, path, n)
        s = s[:m.end()] + block + s[m.end():]
    else:
        # the older board pages: CrashCount is a row in the header card; the block goes right after that card
        m = re.search(r'href="https://crashcount\.nyc/community-board/(\d+)/"', s)
        h = s.find('<div class="cb-hero">')
        if not m or h < 0:
            continue
        depth, i = 0, h
        for t in re.finditer(r'<div\b|</div>', s[h:]):
            depth += 1 if t.group(0) == '<div' else -1
            if depth == 0:
                i = h + t.end(); break
        mw = s.find('<div class="map-wrap" id="sec-map">', i)
        if mw >= 0:   # after the board's own map, which stays first
            depth = 0
            for t in re.finditer(r'<div\b|</div>', s[mw:]):
                depth += 1 if t.group(0) == '<div' else -1
                if depth == 0:
                    i = mw + t.end(); break
        n = m.group(1)
        block = ('<div class="ccsec" style="margin:18px 0"><h2 style="font-size:1.15rem;font-weight:800;color:#0d1b4b;margin:0 0 4px">Traffic crashes</h2>'
                 '<div data-crashcount data-layer="community" data-id="%s" data-path="community-board/%s/"></div></div>') % (n, n)
        s = s[:i] + block + s[i:]
    if TAG not in s:
        s = s.replace('</body>', TAG + '\n</body>', 1)
    open(p, 'w', encoding='utf-8').write(s)
    done += 1
print('profiles with the CrashCount block:', done)
