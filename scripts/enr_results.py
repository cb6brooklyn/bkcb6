#!/usr/bin/env python3
"""Election night results from the NYC Board of Elections' unofficial reporting site (enr.boenyc.gov),
by election district, written to data/results/2026-general.json for bkcb6.app/results/, /edresults/ and /ed/<AADDD>/.

Site structure (November 3, 2026):
  index.html                 contest list: name, Summary (OF…CY….html), AD Details (CD<id>ADI0.html for one contest,
                             or OF<n>AD0PY<k>.html listing a district race's contests, each CD<id>ADI0.html)
  CD<id>ADI0.html            one contest: a row per borough with a link CD<id>AD<b>.html (b = 1 New York … 5 Richmond)
  CD<id>AD<b>.html           rows per Assembly District, each a link CD<id>AD<ad><b>.html
  CD<id>AD<ad><b>.html       rows per election district: 'ED n', '% reported', then votes per candidate column;
                             the header rows give the candidate per column and the party line in parentheses
Candidates are summed across their party lines. ED keys are AADDD, matching electionexplainer/map/eds.geojson.
Each contest gets the race key k used by data/results/ed-ballots.json (race_key in scripts/boe_edlevel.py).

Run: python3 scripts/enr_results.py [--start URL] [--dry] [--out PATH]
Writes nothing if no contest with election district rows is found, so a bad parse never blanks the page.
"""
import json, os, re, sys, time, html, urllib.request, urllib.parse
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boe_edlevel import race_key as base_race_key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data/results/2026-general.json')
BASE = 'https://enr.boenyc.gov/'
UA = {'User-Agent': 'bkcb6.app election results (community board breakdown)'}

def race_key(name):
    m = re.search(r'Proposal(?: Number)?\s*(\d+)', name, re.I)
    if m: return 'q' + m.group(1)
    return base_race_key(name)

def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.geturl(), r.read().decode('utf-8', 'ignore')
        except Exception as e:
            if i == tries - 1:
                print('fetch failed', url, e, file=sys.stderr)
                return url, ''
            time.sleep(2)

class Tables(HTMLParser):
    """Every table as rows of (text, href) cells."""
    def __init__(self):
        super().__init__(); self.tables = []; self.stack = []; self.cell = None; self.href = None; self.links = []
    def handle_starttag(self, t, a):
        a = dict(a)
        if t == 'table': self.stack.append([])
        elif t == 'tr' and self.stack: self.stack[-1].append([])
        elif t in ('td', 'th') and self.stack and self.stack[-1]: self.cell = ''; self.href = None
        elif t == 'a' and a.get('href'):
            self.links.append(a['href'])
            if self.cell is not None and self.href is None: self.href = a['href']
    def handle_endtag(self, t):
        if t in ('td', 'th') and self.cell is not None and self.stack and self.stack[-1]:
            self.stack[-1][-1].append((re.sub(r'\s+', ' ', html.unescape(self.cell)).strip(), self.href)); self.cell = None
        elif t == 'table' and self.stack:
            self.tables.append(self.stack.pop())
    def handle_data(self, d):
        if self.cell is not None: self.cell += d

def parse(src):
    p = Tables(); p.feed(src); return p

def num(s):
    s = (s or '').replace(',', '').strip()
    return int(s) if re.fullmatch(r'-?\d+', s) else None

def pct(s):
    m = re.match(r'^\s*([\d.]+)\s*%', s or '')
    return float(m.group(1)) if m else None

def link_rows(src):
    out = []
    for tb in parse(src).tables:
        for r in tb:
            if r and any(c[1] for c in r): out.append(r)
    return out

def contest_list(start):
    """[(name, ADI url)] for every contest on the site."""
    url, src = get(start)
    out = []
    for r in link_rows(src):
        cells = [c for c in r if c[0] or c[1]]
        name = next((c[0] for c in cells if c[0] and not c[1] and not re.fullmatch(r'\d+', c[0])), None)
        adi = next((c[1] for c in cells if c[1] and re.search(r'ADI0\.html$', c[1])), None)
        ofl = next((c[1] for c in cells if c[1] and re.search(r'^OF\d+AD0PY\d+\.html$', c[1])), None)
        if not name: continue
        if adi:
            full = urllib.parse.urljoin(url, adi)
            if race_key(name) is None:  # the index names the office only; the contest page's title names the district
                _, s2 = get(full); m = re.search(r'<title>(.*?)</title>', s2, re.S)
                if m and m.group(1).strip(): name = re.sub(r'\s+', ' ', html.unescape(m.group(1))).strip()
            out.append((name, full))
        elif ofl:
            u2, s2 = get(urllib.parse.urljoin(url, ofl))
            for r2 in link_rows(s2):
                for c in r2:
                    if c[1] and re.search(r'ADI0\.html$', c[1]) and c[0]:
                        out.append((c[0], urllib.parse.urljoin(u2, c[1])))
    return out

def ad_pages(adi_url):
    """AD page urls for a contest: CD<id>AD<ad><b>.html, found through the borough pages."""
    _, src = get(adi_url)
    boro = [urllib.parse.urljoin(adi_url, h) for h in re.findall(r'href="(CD\d+AD[1-5]\.html)"', src)]
    out = []
    for bu in boro:
        _, bs = get(bu)
        for h in re.findall(r'href="(CD\d+AD\d{3}\.html)"', bs):
            out.append(urllib.parse.urljoin(bu, h))
    return sorted(set(out))

def ed_rows(src, ad):
    """(columns [(candidate, party)], {edkey: {'r': reported?, 'p': pct reported, 'v': [votes per column]}})."""
    p = parse(src)
    if not p.tables: return [], {}
    tb = [r for r in p.tables[0] if r]
    eds = [r for r in tb if r and re.match(r'^ED\s*\d+$', r[0][0], re.I)]
    if not eds: return [], {}
    first = tb.index(eds[0])
    names_row = tb[first - 2] if first >= 2 else []
    party_row = tb[first - 1] if first >= 1 else []
    vote_idx = [i for i, c in enumerate(eds[0]) if i >= 2 and num(c[0]) is not None]
    nm_vals = [c[0] for c in names_row if c[0] and c[0].lower() != 'reported *']
    pr_vals = [c[0] for c in party_row if c[0] and c[0].lower() != 'reported *']
    cols = []
    for i, n in enumerate(nm_vals):
        party = re.sub(r'^\((.*)\)$', r'\1', pr_vals[i] if i < len(pr_vals) else '').strip()
        cols.append((n, party))
    if len(cols) != len(vote_idx):
        cols = (cols + [('Candidate %d' % (i + 1), '') for i in range(len(vote_idx))])[:len(vote_idx)]
    out = {}
    for r in eds:
        ed = int(re.match(r'^ED\s*(\d+)$', r[0][0], re.I).group(1))
        pc = pct(r[1][0]) if len(r) > 1 else None
        votes = [num(r[i][0]) if i < len(r) else None for i in vote_idx]
        votes = [v or 0 for v in votes]
        out['%02d%03d' % (ad, ed)] = {'r': bool(pc and pc > 0 and sum(votes) > 0), 'p': pc, 'v': votes}
    return cols, out

def scrape(start):
    contests = contest_list(start)
    print('contests', len(contests), file=sys.stderr)
    result = []
    with ThreadPoolExecutor(8) as ex:
        pages = list(ex.map(lambda c: ad_pages(c[1]), contests))
        for (name, adi), urls in zip(contests, pages):
            if not urls: print('no AD pages', name, file=sys.stderr); continue
            srcs = list(ex.map(lambda u: get(u)[1], urls))
            cols, eds = None, {}
            for u, s in zip(urls, srcs):
                m = re.search(r'AD(\d{2})(\d)\.html$', u)
                if not m or not s: continue
                c, e = ed_rows(s, int(m.group(1)))
                if c and not cols: cols = c
                eds.update(e)
            if not eds or not cols: print('no ED rows', name, file=sys.stderr); continue
            order, party, idx = [], {}, []
            for n, pl in cols:
                key = re.sub(r'\s+', ' ', n).strip()
                if re.fullmatch(r'write-?in', key, re.I): key = 'Write-in'
                if key not in party: party[key] = []; order.append(key)
                if pl and pl not in party[key]: party[key].append(pl)
                idx.append(order.index(key))
            merged = {}
            for k, e in eds.items():
                v = [0] * len(order)
                for i, n in zip(idx, e['v']): v[i] += n
                merged[k] = {'r': bool(e['p'] and e['p'] > 0 and sum(v) > 0), 'p': e['p'], 'v': v}
            cid = re.search(r'CD(\d+)ADI0', adi).group(1)
            k = race_key(name)
            result.append({'id': cid, 'k': k, 'name': name, 'c': [{'n': n, 'p': ' / '.join(party[n])} for n in order], 'ed': merged})
            print('contest', cid, k, name, len(merged), 'EDs', sum(1 for e in merged.values() if e['r']), 'reporting', file=sys.stderr)
    return result

def main():
    start = BASE
    if '--start' in sys.argv: start = sys.argv[sys.argv.index('--start') + 1]
    out = OUT
    if '--out' in sys.argv: out = sys.argv[sys.argv.index('--out') + 1]
    contests = scrape(start)
    if not contests:
        print('no contests parsed; leaving', out, 'unchanged', file=sys.stderr); return 1
    data = {'updated': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'final': False, 'source': start, 'contests': contests}
    if '--dry' in sys.argv:
        print(json.dumps({'contests': len(contests), 'eds': sum(len(c['ed']) for c in contests), 'keys': [c['k'] for c in contests]})); return 0
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(data, open(out, 'w'), separators=(',', ':'))
    print('wrote', out, len(contests), 'contests', file=sys.stderr)
    return 0

if __name__ == '__main__':
    sys.exit(main())
