#!/usr/bin/env python3
"""New Yorkers for Parks' open space profile on every community board and City Council profile.

Community boards get NY4P's 2021 Open Space Profile of their district; Council members get NY4P's 2015 City Council
District Profile of their district number (assets/ny4p-embed.js). The block goes right after the CrashCount block that
every one of these profiles carries. Idempotent: run again after rebuilding a profile.
"""
import glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = '<script src="/assets/ny4p-embed.js?v=20261114"></script>'
BORO = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
CC = re.compile(r'<div data-crashcount data-layer="(council|community)" data-id="(\d+)"[^>]*></div>')
done, skipped = 0, []
files = sorted(glob.glob(os.path.join(ROOT, 'cm*/index.html')) + glob.glob(os.path.join(ROOT, 'cb-*.html')) + glob.glob(os.path.join(ROOT, 'bk/cb-*.html')))
for p in files:
    s = open(p, encoding='utf-8').read()
    if 'data-ny4p' in s: done += 1; continue
    m = CC.search(s)
    if not m: skipped.append(os.path.relpath(p, ROOT)); continue
    layer, n = m.groups()
    if layer == 'council':
        block = '<div data-ny4p data-cc="%s"></div>' % n
    else:
        if len(n) != 3 or n[0] not in BORO: skipped.append(os.path.relpath(p, ROOT)); continue
        block = '<div data-ny4p data-cd="%s%s"></div>' % (BORO[n[0]], n[1:])
    # after the CrashCount block (and its wrapper, on the older board pages)
    end = m.end()
    w = s.rfind('<div class="ccsec"', 0, m.start())
    if w >= 0 and s.find('</div></div>', m.start()) == m.end():
        end = m.end() + len('</div>')
    s = s[:end] + block + s[end:]
    if TAG not in s: s = s.replace('</body>', TAG + '\n</body>', 1)
    open(p, 'w', encoding='utf-8').write(s); done += 1
print('profiles with the NY4P block:', done, '| no CrashCount block to follow:', len(skipped), skipped[:12])
