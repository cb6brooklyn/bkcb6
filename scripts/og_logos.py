#!/usr/bin/env python3
"""Every page that is a Directory listing shares with its own logo: og:image and twitter:image point at the listing's
Directory tile (app/data/civic/icons/<cover>), and the card is a square 'summary'. Run last, after directory_grid.py."""
import json, os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
ICON = {os.path.splitext(f)[0]: f for f in os.listdir('app/data/civic/icons')}
def path_for(h):
    h = h.split('#')[0].split('?')[0]
    if not h.startswith('/'): return None
    p = h[1:]
    for c in ([p] if p.endswith('.html') else [p + 'index.html'] if p.endswith('/') else [p + '.html', p + '/index.html']):
        if c and os.path.isfile(c): return c
def main():
    d = json.load(open('profiles/dir.json')); done = 0; seen = set()
    for r in d['E']:
        f = path_for(r[1]); fn = ICON.get(r[2])
        if not f or not fn or f in seen: continue
        seen.add(f); url = 'https://bkcb6.app/app/data/civic/icons/' + fn
        t = open(f, encoding='utf-8', errors='surrogateescape').read(); u = t
        if 'property="og:image"' in u: u = re.sub(r'(<meta property="og:image" content=")[^"]*(")', r'\g<1>' + url + r'\2', u, count=1)
        elif '</head>' in u: u = u.replace('</head>', '<meta property="og:image" content="%s">' % url, 1)
        if 'name="twitter:image"' in u: u = re.sub(r'(<meta name="twitter:image" content=")[^"]*(")', r'\g<1>' + url + r'\2', u, count=1)
        else: u = u.replace('</head>', '<meta name="twitter:image" content="%s">' % url, 1)
        u = re.sub(r'(<meta name="twitter:card" content=")summary_large_image(")', r'\1summary\2', u, count=1)
        if 'name="twitter:card"' not in u: u = u.replace('</head>', '<meta name="twitter:card" content="summary">', 1)
        if u != t: open(f, 'w', encoding='utf-8', errors='surrogateescape').write(u); done += 1
    print('pages sharing their own logo:', len(seen), '(changed now:', done, ')')
if __name__ == '__main__': main()
