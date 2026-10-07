#!/usr/bin/env python3
"""The block cards' "On that ballot for this block" lines come from the certified ballot (app/data/civic/nov-ballot.json),
candidate by candidate with their party lines, instead of the district's sitting official. Rewrites ballot26 in every
app/data/civic/blocks/<cd>.json.gz, keeping each block's districts. Re-run after nov-ballot.json changes."""
import json, gzip, glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = json.load(open(os.path.join(ROOT, 'app/data/civic/nov-ballot.json')))
ABBR = {'Democratic': 'D', 'Republican': 'R', 'Conservative': 'C', 'Working Families': 'WF', 'Vote Affordable': 'VA', 'Green': 'G', 'Libertarian': 'L', 'Independence': 'I'}

def candidates(lines):
    """[[party, name], ...] -> 'Name (D, WF), Name (R, C)' in ballot order, each candidate once."""
    order = []; parties = {}
    for row in lines:
        party, name = row[0], row[1]
        if name not in parties: order.append(name); parties[name] = []
        parties[name].append(ABBR.get(party, party))
    return ', '.join(f"{n} ({', '.join(parties[n])})" for n in order)

def rewrite(line):
    m = re.match(r'Assembly District (\d+)', line)
    if m and m.group(1) in B['ad']: return f"Assembly District {m.group(1)}: {candidates(B['ad'][m.group(1)])}"
    m = re.match(r'State Senate District (\d+)', line)
    if m and m.group(1) in B['sd']: return f"State Senate District {m.group(1)}: {candidates(B['sd'][m.group(1)])}"
    m = re.match(r'Congress, NY-(\d+)', line)
    if m and m.group(1) in B['cd']: return f"Congress, NY-{m.group(1)}: {candidates(B['cd'][m.group(1)])}"
    return line

files = sorted(glob.glob(os.path.join(ROOT, 'app/data/civic/blocks/*.json.gz')))
changed = total = 0
for f in files:
    d = json.load(gzip.open(f))
    if 'blocks' not in d: continue   # the address indexes carry no ballot lines
    blocks = d['blocks']; items = blocks.values() if isinstance(blocks, dict) else blocks
    n = 0
    for b in items:
        new = [rewrite(l) for l in b.get('ballot26', [])]
        if new != b.get('ballot26', []): b['ballot26'] = new; n += 1
    total += n
    if n:
        with gzip.open(f, 'wt', encoding='utf-8') as out: json.dump(d, out, ensure_ascii=False, separators=(',', ':'))
        changed += 1
print('blocks rewritten', total, 'in', changed, 'files; source:', B['src'])
