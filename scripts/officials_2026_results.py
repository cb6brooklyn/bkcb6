#!/usr/bin/env python3
"""Elected officials' profiles after the November 3, 2026 general election.
1. Moves each official's "In brief" section to the top of the page, right under the name.
2. Rewrites the "next on the ballot" line for every seat that was on the 2026 ballot (Assembly, State Senate, Congress,
   Governor, Lieutenant Governor, Attorney General, State Comptroller), from data/results/2026-general.json (NYC Board of
   Elections unofficial results): re-elected, or who won the seat and when they take office.
Seats partly outside the city (NY-3, NY-16) and the statewide offices are set from the race calls listed in CALLED.
Idempotent. Usage: python3 scripts/officials_2026_results.py"""
import json, os, re, unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
R = json.load(open('data/results/2026-general.json'))
W = {}
for c in R['contests']:
    tot = [0] * len(c['c'])
    for e in c['ed'].values():
        for i, v in enumerate(e['v']): tot[i] += v
    i = max(range(len(tot)), key=lambda j: tot[j])
    W[c['k']] = c['c'][i]['n']
# reported outside the city's count: Hochul, James and DiNapoli re-elected (FOX 5 New York); Suozzi (NY-3) and Latimer
# (NY-16) re-elected (AP via KTAR; Ballotpedia)
CALLED = {'governor': 'reelected', 'attorneygeneral': 'reelected', 'statecomptroller': 'reelected'}
SAME = {'amhermelyn'}    # on the ballot under a shorter name (Rodneyse Bichotte)
O = json.load(open('app/data/civic/officials.json'))
KEY = {'assembly': 'ad', 'senate': 'sd', 'congress': 'cd'}
def last(n):
    n = unicodedata.normalize('NFD', n); n = re.sub(r'[^A-Za-z \-]', '', n).lower(); n = re.sub(r'\b(jr|sr|ii|iii)\b', '', n).split()
    return n[-1] if n else ''
TAIL = ''
SRC = ' <span class="src">Unofficial results.</span>'
moved = rewritten = 0
for o in O:
    p = o['slug'] + '/index.html'
    if not os.path.exists(p): continue
    s = open(p, encoding='utf-8').read(); s0 = s
    # 1. In brief to the top
    m = re.search(r'<div class="sec"><h2>In brief</h2><div class="bio">.*?</div></div>', s, re.S)
    if m and '<!--seatmap-->' in s and s.find('<!--seatmap-->') < m.start():
        blk = m.group(0); s = s[:m.start()] + s[m.end():]
        s = s.replace('<!--seatmap-->', blk + '<!--seatmap-->', 1); moved += 1
    # 2. the 2026 result
    status = None; winner = None; next_y = None; start = 'January 1, 2027'
    if o['type'] in KEY:
        k = KEY[o['type']] + str(o.get('district') or '')
        if k in W:
            winner = W[k]
            status = 'reelected' if (o['slug'] in SAME or last(o['name']) == last(winner) or last(o['name']) in winner.lower()) else 'new'
            next_y = 'November 2028'
            if o['type'] == 'congress': start = 'January 3, 2027'
    elif o['slug'] in CALLED:
        status = CALLED[o['slug']]; next_y = 'November 2030'
    elif o['slug'] == 'lieutenantgovernor':
        status = 'lg'
    if status:
        if status == 'reelected':
            para = ('<p>Re-elected on <b>November 3, 2026</b>. The new term starts ' + start + '. Next on the ballot in <b><a href="/elections.html">'
                    + next_y + '</a></b>.' + TAIL + (SRC if o['type'] in KEY else '') + '</p>')
        elif status == 'new':
            nm = re.sub(r'\s+', ' ', winner)
            para = ('<p><b>' + nm + '</b> won this seat on <b>November 3, 2026</b> and takes office ' + start + '. ' + o['name']
                    + '’s term ends then.' + TAIL + SRC + '</p>')
        else:
            para = ('<p>Governor Hochul was re-elected on <b>November 3, 2026</b> with <b>Adrienne Adams</b> as her running mate. Adams takes office as '
                    'Lieutenant Governor on January 1, 2027, when ' + o['name'] + '’s term ends.' + TAIL + '</p>')
        s2 = re.sub(r'<p>(?:Next on the ballot|The office is next on the ballot|Re-elected on <b>November 3, 2026|<b>[^<]+</b> won this seat on|Governor Hochul was re-elected)[^\n]*?</p>(?=</div></div>)', para, s, count=1)
        if s2 != s: rewritten += 1; s = s2
    if s != s0: open(p, 'w', encoding='utf-8').write(s)
print('In brief moved to the top on', moved, 'pages;', rewritten, 'ballot lines rewritten')
