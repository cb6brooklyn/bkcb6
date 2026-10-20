"""Read a NYC Board of Elections poll site list (pdftotext -layout output): {'AADDD': [site name, site address]}.
The lists run ten Assembly District columns across the page, each with ED / SITE NAME / SITE ADDRESS. A district can
start partway down a page (its own heading and column header in one column while the others keep running), an ED
number can sit on its own line with the site on the next, and a heading can share a line with other columns' rows."""
import re
def _entry(seg):
    m = re.match(r'^\s*(\d{2,3})(?:\s+(.+?))?\s*$', seg)
    if not m:
        return None
    return int(m.group(1)), (m.group(2) or '')
def _split(rest):
    mm = re.match(r'^(.*?)\.{2,}\s*(.+)$', rest)
    if mm:
        return mm.group(1).strip(), mm.group(2).strip()
    mm = re.match(r'^(.*?)\s+(\d[\w-]*\s.+)$', rest)
    return (mm.group(1).strip(), mm.group(2).strip()) if mm else None
def parse(path):
    out = {}
    lines = open(path, errors='replace').read().split('\n')
    cols, ads, adlab, pending = [], [], [], {}
    for ln in lines:
        skip = set()
        labs = [(m.start(), int(m.group(1))) for m in re.finditer(r'(\d{2})\s?(?:st|nd|rd|th)\s+Assembly District', ln, re.I)]
        if labs:
            # keep earlier labels that are not replaced (a heading over one column only)
            adlab = sorted([(p, a) for p, a in adlab if all(abs(p - q) > 40 for q, _ in labs)] + labs)
            for p, a in labs:
                skip.add(p)
        nc = [m.start() for m in re.finditer(r'\bED\b(?=\s+SITE)', ln)]
        if nc:
            na = []
            for i, c in enumerate(nc):
                end = nc[i + 1] if i + 1 < len(nc) else 10**6
                cand = [a for p, a in adlab if c - 15 <= p < end - 15]
                na.append(cand[0] if cand else None)
            keep = [(c, a) for c, a in zip(cols, ads) if all(abs(c - x) > 40 for x in nc)]
            pairs = sorted(keep + list(zip(nc, na)))
            cols = [c for c, a in pairs]; ads = [a for c, a in pairs]
            for c in nc:
                pending.pop(c, None)
        if not cols:
            continue
        for i, c in enumerate(cols):
            if c in nc or ads[i] is None:
                continue
            start = max(0, c - 3); end = cols[i + 1] - 3 if i + 1 < len(cols) else len(ln)
            seg = ln[start:end]
            if any(start <= p < end for p in skip):
                continue
            e = _entry(seg)
            if e and e[1]:
                sp = _split(e[1])
                if sp:
                    out['%d%03d' % (ads[i], e[0])] = list(sp)
                pending.pop(c, None)
            elif e:
                pending[c] = (ads[i], e[0])
            elif seg.strip() and c in pending:
                sp = _split(seg.strip())
                if sp:
                    a, ed = pending.pop(c)
                    out['%d%03d' % (a, ed)] = list(sp)
    return out
if __name__ == '__main__':
    import sys, collections
    for p in sys.argv[1:]:
        o = parse(p)
        print(p, len(o))
