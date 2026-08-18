#!/usr/bin/env python3
"""
Adds a farmers markets section to every district and borough parks page.

Each page gets only the markets in its own scope, read from
data/farmers-markets.json, in the same collapsible format the page already uses
for its park directory. Pages whose scope has no markets are left untouched
rather than given an empty section.

Usage: python3 scripts/add_market_sections.py
"""
import glob
import html
import json
import os
import re

DATA = 'data/farmers-markets.json'
DISTRICT = re.compile(r'parks/(bk|mn|qn|bx|si)-\d+\.html$')
BOROUGH = {
    'parks/brooklyn.html': '3',
    'parks/manhattan.html': '1',
    'parks/queens.html': '4',
    'parks/bronx.html': '2',
    'parks/statenisland.html': '5',
}

CSS = (
    "\n.mkt-row{display:grid;grid-template-columns:1fr;gap:2px;padding:10px 0;"
    "border-top:1px solid #eceae4}\n"
    ".mkt-row:first-child{border-top:0}\n"
    ".mkt-row .mn{font-weight:800;color:#0d1b4b}\n"
    ".mkt-row .mn a{color:inherit;text-decoration:underline;text-underline-offset:2px;"
    "text-decoration-color:#c1121f;text-decoration-thickness:2px}\n"
    ".mkt-row .mw{font-family:'DM Mono',monospace;font-size:.72rem;color:#6b6760}\n"
    ".mkt-row .mt b{display:inline-block;font-family:'DM Mono',monospace;font-size:.62rem;"
    "font-weight:500;color:#fff;background:#7bc043;border-radius:3px;padding:1px 6px;"
    "margin:3px 4px 0 0}\n"
    ".mkt-row .mt b.ebt{background:#c1121f}\n"
)


def rows_for(markets, scope_href):
    out = []
    for m in sorted(markets, key=lambda x: x['n'].lower()):
        when = ', '.join(x for x in (m.get('d'), m.get('h')) if x)
        tags = ''
        if m.get('yr'):
            tags += '<b>open year round</b>'
        if m.get('ebt'):
            tags += '<b class="ebt">accepts EBT</b>'
        out.append(
            '<div class="mkt-row"><div class="mn">'
            '<a href="../activities.html?%s&amp;at=%.5f,%.5f" target="_blank" rel="noopener">%s</a>'
            '</div><div class="mw">%s</div><div class="mt">%s</div></div>'
            % (scope_href, m['y'], m['x'], html.escape(m['n']),
               html.escape(', '.join(x for x in (m.get('ad'), when) if x)), tags))
    return ''.join(out)


def section(markets, scope_href, where):
    n = len(markets)
    word = 'market' if n == 1 else 'markets'
    return (
        '\n  <details class="drop">\n'
        '    <summary>%d farmers %s in %s</summary>\n'
        '    <div class="drop-body">%s</div>\n'
        '  </details>\n'
        % (n, word, html.escape(where), rows_for(markets, scope_href)))


def where_from(path, page):
    m = re.search(r'<title>([^<]*)</title>', page)
    t = m.group(1) if m else ''
    t = t.split('—')[0].split('|')[0].strip()
    return t or os.path.basename(path)


def main():
    markets = json.load(open(DATA))['markets']
    touched = skipped = 0
    for f in sorted(glob.glob('parks/*.html')):
        s = open(f, encoding='utf-8', errors='replace').read()
        if 'farmers ' in s and 'mkt-row' in s:
            continue                                    # already done
        if DISTRICT.search(f):
            m = re.search(r'activities\.html\?cd=(\d+)', s)
            if not m:
                continue
            cd = m.group(1)
            mine = [x for x in markets if x['c'] == cd]
            scope = 'cd=' + cd
        elif f in BOROUGH:
            b = BOROUGH[f]
            mine = [x for x in markets if str(x['c'])[:1] == b]
            scope = 'boro=' + b
        else:
            continue

        if not mine:
            skipped += 1
            continue

        # District pages label this "Park sites in ..."; borough pages label it
        # "Community districts in ...". Anchor after whichever directory exists.
        anchor = re.search(
            r'<details class="drop">\s*<summary>[^<]*(?:[Pp]ark sites|Every park|'
            r'Community districts)[^<]*</summary>.*?</details>', s, re.S)
        if not anchor:
            skipped += 1
            continue
        s = s[:anchor.end()] + section(mine, scope, where_from(f, s)) + s[anchor.end():]
        if '.mkt-row{' not in s:
            i = s.index('</style>')
            s = s[:i] + CSS + s[i:]
        open(f, 'w').write(s)
        touched += 1
        print('  %-28s %d markets' % (f, len(mine)))
    print('pages updated: %d | skipped (no markets in scope): %d' % (touched, skipped))


if __name__ == '__main__':
    main()
