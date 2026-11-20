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
PROPS = {q['n']: q['t'] for q in json.load(open(os.path.join(ROOT, 'app/data/civic/nov-props.json')))['q']}
def short(c, n):
    """The name used in the count lines: the candidate for Governor for the ticket, Yes/No for a proposal."""
    return name(c, n)
def ticket(c, n):
    """The name as it was on the ballot: the Governor ticket reads 'Kathy C. Hochul and Adrienne E. Adams'."""
    if c['k'] == 'gov':
        g = name(c, n)
        if g != n and n.startswith(g): return '%s and %s' % (g, n[len(g):].strip())
    return n
def count(c, v):
    tot = sum(v)
    return ', '.join('%s %s (%d%%)' % (short(c, c['c'][i]['n']), format(v[i], ','), round(100 * v[i] / tot))
                     for i in range(min(len(v), len(c['c']))) if not (c['c'][i]['n'] == 'Write-in' and v[i] == 0))
CITY = {}
for c in R['contests']:
    if not KEEP.match(c['k']): continue
    t = [0] * len(c['c'])
    for e in c['ed'].values():
        for i, x in enumerate((e.get('v') or [])[:len(t)]): t[i] += x
    CITY[c['k']] = t
def lines(key):
    """One paragraph per contest: what it was, who was on the ballot, how this election district voted, and the count
    across every New York City election district in the race."""
    out = []
    for c in contests:
        e = c['ed'].get(key)
        if not e: continue
        v = e.get('v') or []; tot = sum(v)
        if not tot: continue
        k = c['k']
        if k.startswith('q'):
            n = int(re.sub(r'\D', '', k))
            head = 'Proposal %d: %s' % (n, PROPS.get(n, '')) if PROPS.get(n) else label(c)
            who = ''
        else:
            head = 'Governor and Lieutenant Governor' if k == 'gov' else label(c)
            who = 'On the ballot: ' + '; '.join('%s (%s)' % (ticket(c, x['n']), x['p']) for x in c['c'] if x['n'] != 'Write-in' and x['p'])
        para = [head]
        if who: para.append(who)
        para.append('This election district: ' + count(c, v))
        if sum(CITY[k]): para.append(('Citywide: ' if k.startswith('q') else 'All New York City election districts in this race: ') + count(c, CITY[k]))
        out.append('\n'.join(para))
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
            if ls: txt.append(('Election District %d in Assembly District %d. General election, November 3, 2026. %s count from the NYC Board of Elections.\n\n' % (e['ed'], e['ad'], 'Certified' if R.get('final') else 'Unofficial election night')) + '\n\n'.join(ls))
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
