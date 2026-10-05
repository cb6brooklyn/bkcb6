#!/usr/bin/env python3
"""Reader for the 2000 to 2004 NYC Board of Elections "Statement and Return" recap PDFs (pdftotext -layout),
the wide-table format: one row per Assembly district, one column per candidate line, with continuation
pages (PAGE 1A, 1B ...) carrying further columns for the same rows.

parse(path) -> list of (date, kind, office_title, party, county, ad, unit, votes)
"""
import re

BORO_WORDS = {'NEW YORK': 'New York County', 'BRONX': 'Bronx County', 'KINGS': 'Kings County',
              'QUEENS': 'Queens County', 'RICHMOND': 'Richmond County'}
ROW_AD = re.compile(r'^\s*(\d{1,3})(ST|ND|RD|TH)\s+[\d*]')
NUMTOK = re.compile(r'\d[\d,]*')
BALLOT_WORDS = ('PUBLIC', 'COUNTER', 'ABS', 'MIL', 'FED', 'EMERG', 'AFFID', 'AFF', 'BALLOT')
PARTIES = {'REPUBLICAN', 'DEMOCRATIC', 'INDEPENDENCE', 'CONSERVATIVE', 'LIBERAL', 'GREEN', 'WORKING', 'FAMILIES',
           'RIGHT', 'TO', 'LIFE', 'BETTER', 'SCHOOLS', 'AMERICAN', 'DREAM', 'LIBERTARIAN', 'FUSION', 'MARIJUANA', 'REFORM',
           'SOCIALIST', 'WORKERS', 'CONSTITUTION', 'INDEPENDENT', 'CONTINENTAL', 'PEACE', 'AND', 'JUSTICE',
           'UNITY', 'NATURAL', 'LAW', 'PARTY'}
MONTHS = 'JANUARY FEBRUARY MARCH APRIL MAY JUNE JULY AUGUST SEPTEMBER OCTOBER NOVEMBER DECEMBER'.split()


def split_pages(text):
    lines = text.split('\n')
    starts = [i for i, l in enumerate(lines) if re.search(r'PAGE:\s*\w+\s*$', l)]
    pages = []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(lines)
        pages.append(lines[max(0, s - 1):e])
    return pages


def page_meta(pg):
    head = ' '.join(pg[:3])
    m = re.search(r'(\d{4})\s+(GENERAL|PRIMARY|SPECIAL|RUNOFF|RUN-OFF|PRESIDENTIAL PRIMARY|DEMOCRATIC PRESIDENTIAL PRIMARY|REPUBLICAN PRESIDENTIAL PRIMARY)[A-Z ]*ELECTION', head)
    pid = re.search(r'PAGE:\s*(\w+)\s*$', ' '.join(pg[:3]))
    county = None
    for l in pg[:3]:
        for w, c in BORO_WORDS.items():
            if re.search(r'\b' + w + r' COUNTY\b', l):
                county = c
    title = []
    party = ''
    for i, l in enumerate(pg):
        if 'OF THE VOTES FOR THE OFFICE OF' in l:
            j = i + 1
            while j < len(pg) and pg[j].strip() and 'NO. OF CANDIDATES' not in pg[j] and 'R E C A P' not in pg[j] \
                    and not pg[j].strip().startswith('BOROUGH OF') and 'PARTY' not in pg[j]:
                title.append(pg[j].strip())
                j += 1
            break
    for l in pg[:25]:
        if not ('R E C A P' in l or 'BOROUGH OF' in l or re.fullmatch(r'\s*[A-Z ]+ PARTY\s*', l)):
            continue
        if 'TOTAL' in l:
            continue  # column headings ("TOTAL ... GREEN PARTY ..."), not the page's party
        mp = re.search(r'\b([A-Z][A-Z ]*?) PARTY\b', l)
        if mp and 'R E C A P' not in mp.group(1):
            ws = mp.group(1).split()
            k = len(ws)
            while k > 0 and ws[k - 1] in PARTIES:
                k -= 1
            if ws[k:]:
                party = ' '.join(ws[k:])
                break
    return (m.group(1) if m else None, m.group(2) if m else None, pid.group(1) if pid else '1', ' / '.join(title), party, county)


def columns(pg):
    """Find data rows and the right edge of each numeric column."""
    rows = []
    for i, l in enumerate(pg):
        if ROW_AD.match(l) and NUMTOK.search(l[8:]):
            rows.append(i)
    if not rows:
        return None
    edges = {}
    for i in rows:
        for m in re.finditer(r'\d[\d,]*', pg[i]):
            if m.start() < 6:
                continue
            e = m.end()
            hit = None
            for k in list(edges):
                if abs(k - e) <= 2:
                    hit = k
                    break
            if hit is None:
                edges[e] = 1
            else:
                edges[hit] += 1
    cols = sorted(edges)
    return rows, cols


def header_cols(pg, first_row, cols):
    """Text above the data rows, assigned to the nearest column by right edge."""
    start = 0
    for i in range(first_row - 1, -1, -1):
        if 'R E C A P' in pg[i] or 'COUNCILMANIC DISTRICT' == pg[i].strip() or re.match(r'^\s*$', pg[i]) and i < first_row - 8:
            start = i + 1
            break
    hdr = {c: [] for c in cols}
    for l in pg[start:first_row]:
        if not l.strip() or set(l.strip()) <= set('-* '):
            continue
        for m in re.finditer(r'\S+(?: \S+)*', l):
            tok = m.group(0).replace('*', '').strip()
            if not tok:
                continue
            e = m.end()
            # split multi-word runs that span several columns
            near = min(cols, key=lambda c: abs(c - e))
            if abs(near - e) <= 6:
                hdr[near].append(tok)
    return hdr


def parse(path):
    text = open(path, encoding='utf-8', errors='replace').read()
    out = []
    for pg in split_pages(text):
        year, kind, pid, title, party, county = page_meta(pg)
        if not year or not title:
            continue
        hdr_text = ' '.join(pg[:40])
        if not re.search(r'ASSEM|AD #S|ASSEMBLY', hdr_text):
            continue  # county or citywide recap pages, not by Assembly district
        cr = columns(pg)
        if not cr:
            continue
        rows, cols = cr
        hdr = header_cols(pg, rows[0], cols)
        # fine-split header runs: re-tokenize words so each column gets the words ending nearest it
        hdr = {c: [] for c in cols}
        first = rows[0]
        j = first - 1
        rowlike = re.compile(r'^\s*\d{1,3}(ST|ND|RD|TH)\s')  # includes "NOT USED" rows
        while j >= 0 and (not pg[j].strip() or set(pg[j].strip()) <= set('* ') or rowlike.match(pg[j])):
            j -= 1
        block = []
        while j >= 0 and pg[j].strip():
            l = pg[j]
            if 'R E C A P' in l or 'PARTY' in l or re.match(r'^\S.*(DISTRICT|COUNTY|CITY OF NEW YORK)\s*$', l):
                break
            block.insert(0, l)
            j -= 1
        # header words go to the column whose span (previous edge, edge] holds the word's right end; the
        # numbers are right-aligned, and so are the headings above them. Each line in a column is one cell.
        for l in block:
            if set(l.strip()) <= set('-* ') or re.match(r'^\s*\d{1,3}(ST|ND|RD|TH)\s', l):
                continue
            ws = [w for w in l[9:].split() if w.replace('*', '')]
            partyline = bool(ws) and all(w in PARTIES or w == 'TOTAL' or re.fullmatch(r'\d+[A-Z]', w) for w in ws)
            # a header cell is a run of words separated by single spaces, aligned on its column's right edge;
            # a run that reaches back past the previous column's edge is two cells run together
            for m in re.finditer(r'\S+(?: \S+)*', l):
                words = [(m.start() + w.start(), m.start() + w.end(), w.group(0).replace('*', ''))
                         for w in re.finditer(r'\S+', m.group(0))]
                words = [x for x in words if x[0] >= 9 and x[2] and not set(x[2]) <= set('-')
                         and not (partyline and (x[2] in PARTIES or re.fullmatch(r'\d+[A-Z]', x[2])))]
                while words:
                    e = words[-1][1]
                    near = min(cols, key=lambda c: abs(c - e))
                    prev = [c for c in cols if c < near]
                    cut = 0
                    if prev and len(words) > 1 and words[0][0] < prev[-1] - 1:
                        cut = min(range(1, len(words)), key=lambda k: abs(words[k - 1][1] - prev[-1]))
                    part = words[cut:]
                    if abs(near - e) <= 8:
                        hdr[near].append(' '.join(x[2] for x in part))
                    words = words[:cut]
        ed_mode = any(re.match(r'^\s*ELEC', l) for l in block) or any(re.match(r'^\s*ELEC', l) for l in pg[max(0, rows[0] - 8):rows[0]])
        page_ad = None
        if ed_mode:
            for l in pg[:rows[0]]:
                ma = re.match(r'^\s*(\d{1,2})(?:ST|ND|RD|TH) ASSEMBLY DISTRICT\s*$', l)
                if ma:
                    page_ad = int(ma.group(1))
            if page_ad is None:
                continue
        kinds = {}
        ticket = ' AND ' in title.split(' / ')[0]
        for c in cols:
            cells = hdr[c]
            words = ' '.join(cells).split()
            w = ' '.join(words)
            if any(x in words for x in ('PUBLIC', 'COUNTER', 'ABS/', 'ABS', 'FED', 'EMERG', 'AFFID', 'AFF')) or w.endswith('BALLOT') or w in ('BALLOT', 'MIL BALLOT'):
                kinds[c] = ('ballot', w)
            elif 'OFFICE' in words or 'THIS' in words:
                kinds[c] = ('total', w)
            elif 'UNRE' in words or 'CORD' in words:
                kinds[c] = ('unrec', w)
            elif words[-1:] == ['VOTE'] and ('SCAT' in words):
                kinds[c] = ('cand', 'Write-in')
            else:
                cells = [x for x in cells if not re.fullmatch(r'\d+[A-Z]', x)]
                kinds[c] = ('cand', (' / ' if ticket else ' ').join(cells)) if cells else ('skip', w)
        # a column of numbers printed a few characters off its neighbours, with no heading of its own,
        # belongs to the headed column next to it
        for c in cols:
            if kinds[c][0] == 'skip' and not hdr[c]:
                nb = [d for d in cols if d != c and hdr[d] and abs(d - c) <= 5]
                if nb:
                    kinds[c] = kinds[min(nb, key=lambda d: abs(d - c))]
        county_cur = county
        for i in range(rows[0], len(pg)):
            l = pg[i]
            s = l.strip()
            if s in BORO_WORDS:
                county_cur = BORO_WORDS[s]
                continue
            m = ROW_AD.match(l)
            if not m:
                continue
            ad = int(m.group(1))
            ed = None
            if ed_mode:
                ed, ad = ad, page_ad
            nums = [(x.end(), int(x.group(0).replace(',', ''))) for x in re.finditer(r'\d[\d,]*', l) if x.start() >= 6]
            for e, v in nums:
                near = min(cols, key=lambda c: abs(c - e))
                if abs(near - e) > 3:
                    continue
                k, name = kinds[near]
                if k == 'skip':
                    continue
                unit = {'ballot': '__ballot:' + name, 'total': '__total', 'unrec': '__unrec'}.get(k, name)
                out.append((year, kind, title, party, county_cur, ad, unit, v, pid, ed))
    return out


def county_totals(path):
    """From the recap pages (one row per county), each county's printed "total vote this office"."""
    text = open(path, encoding='utf-8', errors='replace').read()
    out = {}
    for pg in split_pages(text):
        year, kind, pid, title, party, county = page_meta(pg)
        if not year or not title or re.search(r'ASSEM|AD #S|ASSEMBLY', ' '.join(pg[:40])):
            continue
        for l in pg:
            m = re.match(r'^\s*(NEW YORK|BRONX|KINGS|QUEENS|RICHMOND)\s+[\d,]+.*?\*\s*([\d,]+)\s*\*', l)
            if m:
                out[(title, party, BORO_WORDS[m.group(1)])] = int(m.group(2).replace(',', ''))
    return out


if __name__ == '__main__':
    import sys, collections
    rows = parse(sys.argv[1])
    print(len(rows))
    flt = sys.argv[2] if len(sys.argv) > 2 else ''
    for r in rows:
        if flt in r[2]:
            print(r)
