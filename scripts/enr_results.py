#!/usr/bin/env python3
"""Election night results from the NYC Board of Elections' unofficial reporting site (enr.boenyc.gov),
by election district, written to data/results/2026-general.json for bkcb6.app/results/.

The site is a set of static HTML pages: a contest list, one page per contest, an "AD details" page per
contest listing Assembly Districts, and one page per Assembly District listing every election district.
Election districts are keyed AADDD (assembly district, election district), the same keys as
electionexplainer/map/eds.geojson, so the page adds them up by community district.

Run: python3 scripts/enr_results.py [--start URL] [--dry]
Writes nothing if no contest with election district rows is found, so a bad parse never blanks the page.
"""
import json, os, re, sys, time, html, urllib.request, urllib.parse
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data/results/2026-general.json')
BASE = 'https://enr.boenyc.gov/'
UA = {'User-Agent': 'bkcb6.app election results (community board breakdown)'}

def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
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
            self.stack[-1][-1].append((re.sub(r'\s+', ' ', self.cell).strip(), self.href)); self.cell = None
        elif t == 'table' and self.stack:
            self.tables.append(self.stack.pop())
    def handle_data(self, d):
        if self.cell is not None: self.cell += d

def parse(src):
    p = Tables(); p.feed(src); return p

def num(s):
    s = s.replace(',', '').strip()
    return int(s) if re.fullmatch(r'\d+', s) else None

def text(src):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', src))).strip()

def contest_links(start):
    url, src = get(start)
    p = parse(src)
    out = []
    for h in p.links:
        full = urllib.parse.urljoin(url, h)
        if re.search(r'/CD\d+0\.html$', full) and full not in out: out.append(full)
    return url, out

def title_of(src):
    m = re.search(r'<title>(.*?)</title>', src, re.S | re.I)
    return text(m.group(1)) if m else ''

def ed_rows(page_url, src, ad):
    """Rows of an AD page: each ED with votes per candidate column. Returns (candidate names, {edkey: {'r':bool,'v':[...] }})."""
    p = parse(src)
    best = None
    for tb in p.tables:
        rows = [r for r in tb if r]
        if len(rows) < 2: continue
        eds = [r for r in rows if r and re.match(r'^(ED\s*)?\d{1,3}$', r[0][0].replace('ED', 'ED ').strip(), re.I)]
        if len(eds) >= 1 and (best is None or len(eds) > len(best[1])): best = (rows, eds)
    if not best: return None, {}
    rows, eds = best
    head = None
    for r in rows:
        if r in eds: break
        if len(r) >= 3: head = r
    names = [c[0] for c in (head or [])]
    out = {}
    for r in eds:
        m = re.search(r'(\d{1,3})$', r[0][0]); ed = int(m.group(1))
        vals = [num(c[0]) for c in r[1:]]
        rep = not any(c[0] == '' for c in r[1:]) and any(v is not None for v in vals)
        pct_col = [i for i, c in enumerate(r[1:]) if c[0].endswith('%')]
        votes = [v for i, v in enumerate(vals) if i not in pct_col]
        out['%02d%03d' % (ad, ed)] = {'r': rep, 'v': [v or 0 for v in votes]}
    return names, out

def scrape(start):
    idx, links = contest_links(start)
    print('contest pages', len(links), file=sys.stderr)
    contests = []
    for cu in links:
        _, csrc = get(cu)
        name = title_of(csrc) or text(csrc)[:80]
        p = parse(csrc)
        adi = [urllib.parse.urljoin(cu, h) for h in p.links if re.search(r'ADI\d*\.html$', h)]
        if not adi: continue
        _, asrc = get(adi[0]); ap = parse(asrc)
        adpages = []
        for tb in ap.tables:
            for r in tb:
                if r and r[0][1] and re.search(r'(\d{2})', r[0][0]):
                    adpages.append((int(re.search(r'(\d{2})', r[0][0]).group(1)), urllib.parse.urljoin(adi[0], r[0][1])))
        cands, eds = None, {}
        for ad, au in adpages:
            _, s = get(au)
            n, e = ed_rows(au, s, ad)
            if n and not cands: cands = n
            eds.update(e)
        if not eds: continue
        cnames = [c for c in (cands or [])[1:] if c and not c.endswith('%') and not re.match(r'^(ED|Reported|% ?Reported)', c, re.I)]
        width = max(len(v['v']) for v in eds.values())
        cnames = (cnames + ['Candidate %d' % (i + 1) for i in range(width)])[:width]
        cid = re.search(r'CD(\d+)', cu).group(1)
        contests.append({'id': cid, 'name': name, 'c': [{'n': c, 'p': ''} for c in cnames], 'ed': eds})
        print('contest', cid, name, len(eds), 'EDs', file=sys.stderr)
    return contests

def main():
    start = BASE
    if '--start' in sys.argv: start = sys.argv[sys.argv.index('--start') + 1]
    contests = scrape(start)
    if not contests:
        print('no contests parsed; leaving', OUT, 'unchanged', file=sys.stderr); return 1
    data = {'updated': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'final': False, 'source': start, 'contests': contests}
    if '--dry' in sys.argv:
        print(json.dumps({'contests': len(contests), 'eds': sum(len(c['ed']) for c in contests)})); return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, 'w'), separators=(',', ':'))
    print('wrote', OUT, len(contests), 'contests', file=sys.stderr)
    return 0

if __name__ == '__main__':
    sys.exit(main())
