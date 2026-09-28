#!/usr/bin/env python3
"""Put the App Store badge banner at the top of every bkcb6.app page (idempotent)."""
import os, re, sys
BANNER = ('<a id="asb" href="https://apps.apple.com/us/app/bkcb6/id6813967208" target="_blank" rel="noopener" '
          'style="display:block;background:#0d1b4b;text-align:center;padding:8px 0;line-height:0;text-decoration:none">'
          '<img src="/appstore-badge.png" alt="Download BKCB6 on the App Store" width="121" height="40" '
          'style="height:40px;width:auto;border:0;display:inline-block"></a>')
BODY = re.compile(rb'<body\b[^>]*>', re.I)
def inject(b):
    if b'id="asb"' in b: return None
    m = BODY.search(b)
    if not m: return None
    return b[:m.end()] + BANNER.encode() + b[m.end():]
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
