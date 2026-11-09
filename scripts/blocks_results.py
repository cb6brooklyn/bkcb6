#!/usr/bin/env python3
"""Each block card's "results26": how the block's election district voted on November 3, 2026, from the Board of
Elections' results by election district (data/results/2026-general.json): Governor, Comptroller, Attorney General,
Congress, State Senate, Assembly, City Council where there was a race, and the five proposals. A block that sits in two
election districts gets both. Written into every app/data/civic/blocks/<cd>.json.gz; the apps' Your block card shows it
as the row {"id": "field:results26"} (lists.json "MyBlock.rows"). Also empties ballot26 (the "On your ballot" lines), now that the election is over. Re-run whenever the results file changes."""
import json, gzip, glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, 'data/results/2026-general.json')))
KEEP = re.compile(r'^(gov|comp|ag|cd\d+|sd\d+|ad\d+|cc\d+|q\d+)$')
ORDER = lambda k: (['gov', 'comp', 'ag'].index(k) if k in ('gov', 'comp', 'ag') else 3 + ['cd', 'sd', 'ad', 'cc', 'q'].index(re.match(r'[a-z]+', k).group(0)), int(re.sub(r'\D', '', k) or 0))
def label(c):
    k = c['k']
    if k == 'gov': return 'Governor'
    if k == 'comp': return 'State Comptroller'
    if k == 'ag': return 'Attorney General'
    n = re.sub(r'\D', '', k)
    if k.startswith('cd'): return 'Congress, NY-%s' % n
    if k.startswith('sd'): return 'State Senate District %s' % n
    if k.startswith('ad'): return 'Assembly District %s' % n
    if k.startswith('cc'): return 'City Council District %s' % n
    return 'Proposal %s' % n
def name(c, n):
    if c['k'] == 'gov':
        # the ticket's first name: the candidate for Governor
        for g in ('Kathy C. Hochul', 'Bruce A. Blakeman'):
            if n.startswith(g): return g
    if c['k'].startswith('q'): return n.capitalize()
    return n
contests = sorted([c for c in R['contests'] if KEEP.match(c['k'])], key=lambda c: ORDER(c['k']))
def lines(key):
    out = []
    for c in contests:
        e = c['ed'].get(key)
        if not e: continue
        v = e.get('v') or []; tot = sum(v)
        if not tot: continue
        parts = ['%s %s (%d%%)' % (name(c, c['c'][i]['n']), format(v[i], ','), round(100 * v[i] / tot))
                 for i in range(min(len(v), len(c['c']))) if not (c['c'][i]['n'] == 'Write-in' and v[i] == 0)]
        out.append('%s: %s' % (label(c), ', '.join(parts)))
    return out
nb = nw = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'app/data/civic/blocks/*.json.gz'))):
    d = json.load(gzip.open(f)); ch = False
    for b in d.get('blocks', {}).values():
        seen = []; txt = []
        for e in b.get('eds') or []:
            key = '%02d%03d' % (e.get('ad', 0), e.get('ed', 0))
            if key in seen: continue
            seen.append(key); ls = lines(key)
            if ls: txt.append(('Election District %d in Assembly District %d\n' % (e['ed'], e['ad'])) + '\n'.join(ls))
        new = '\n\n'.join(txt)
        nb += 1; nw += bool(new)
        # the election is over: the sample ballot lines come off the block cards
        if b.get('ballot26'): b['ballot26'] = []; ch = True
        if new:
            if b.get('results26') != new: b['results26'] = new; ch = True
        elif 'results26' in b: del b['results26']; ch = True
    if ch:
        with gzip.open(f, 'wt', encoding='utf-8') as out: json.dump(d, out, ensure_ascii=False, separators=(',', ':'))
print('blocks', nb, 'with results', nw)
