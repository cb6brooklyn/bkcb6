#!/usr/bin/env python3
"""Put the site bar script on every bkcb6.app page that carries the App Store banner (idempotent).

The bar (assets/site-bar.js) replaces the banner at runtime: logo, the page's section, site search, App Store.
It hides itself inside the apps, in frames and on ?embed= pages. Pages without the banner (app/, press/,
old app copies) are left alone. Run from the repo root: python3 tools/add_site_bar.py [dir]
"""
import os, re, sys
TAG = b'<script src="/assets/site-bar.js?v=1" defer></script>'
BODY = re.compile(rb'<body\b[^>]*>', re.I)
def inject(b):
    if b'site-bar.js' in b or b'id="asb"' not in b: return None
    m = BODY.search(b)
    if not m: return None
    return b[:m.end()] + TAG + b[m.end():]
if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    n = 0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ('.git', 'node_modules')]
        for f in fn:
            if not f.endswith('.html'): continue
            p = os.path.join(dp, f)
            with open(p, 'rb') as fh: b = fh.read()
            out = inject(b)
            if out is not None:
                with open(p, 'wb') as fh: fh.write(out)
                n += 1
    print('updated', n)
