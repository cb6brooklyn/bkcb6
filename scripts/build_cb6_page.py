#!/usr/bin/env python3
"""Build rentcb6/index.html as one page, with the CB6 neighborhood map built in (no iframe).

    inputs:  rent-map-cb6.html               the CB6 neighborhood map page (map, legend, report, rankings)
             scripts/src/rentcb6-parts.html  the CB6 rent page as it was with the map in an iframe:
                                             title block, glance cards, trends, table, neighborhood
                                             panels, rent vs inventory, every-area and every-month sections
    output:  rentcb6/index.html

The map page is the base, so the map comes first, in the same colours. The CB6 page's sections follow the
map inside <div class="cb6x">, with their styles scoped to that wrapper so the two pages' styles cannot
collide. The map page's unit-size buttons drive both. Run scripts/build_sales_pages.py afterwards to
rebuild /salescb6 from this page.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def die(m): sys.exit('build_cb6_page: ' + m)


def scope_css(css, pre='.cb6x'):
    """prefix every selector with pre; drop rules for the page itself (html, body, *) and ones the base owns"""
    out, i, n = [], 0, len(css)
    skip = re.compile(r'^\s*(html|body|\*|:root|#nowbar|\.mrnote|\.datastamp|\.rs-toggle)')
    while i < n:
        if css.startswith('@import', i):
            j = css.index(';', i) + 1; i = j; continue
        if css.startswith('@media', i) or css.startswith('@supports', i):
            j = css.index('{', i); depth, k = 1, j + 1
            while depth:
                depth += {'{': 1, '}': -1}.get(css[k], 0); k += 1
            out.append(css[i:j + 1] + scope_css(css[j + 1:k - 1], pre) + '}'); i = k; continue
        if css.startswith('@keyframes', i) or css.startswith('@font-face', i):
            j = css.index('{', i); depth, k = 1, j + 1
            while depth:
                depth += {'{': 1, '}': -1}.get(css[k], 0); k += 1
            out.append(css[i:k]); i = k; continue
        j = css.find('{', i)
        if j < 0: break
        k = css.index('}', j)
        sels, body = css[i:j].strip(), css[j:k + 1]
        if sels:
            keep = [s.strip() for s in sels.split(',') if s.strip() and not skip.match(s.strip())]
            if keep: out.append(','.join(pre + ' ' + s for s in keep) + body)
        i = k + 1
    return '\n'.join(out)


def lines_between(src, start_pat, end_pat, inclusive=True):
    i = src.index(start_pat)
    j = src.index(end_pat, i) + (len(end_pat) if inclusive else 0)
    return src[i:j]


def main():
    P = open(os.path.join(ROOT, 'scripts/src/rentcb6-parts.html')).read()
    B = open(os.path.join(ROOT, 'rent-map-cb6.html')).read()
    P = re.sub(r'<!--rs-toggle-->.*?<!--/rs-toggle-->', '', P, flags=re.S)

    # ---- pieces of the CB6 rent page ----
    p_head = P[:P.index('<style>')]
    p_css = lines_between(P, '<style>', '</style>')[len('<style>'):-len('</style>')]
    hero = lines_between(P, '<div class="topbar">', '\n</div>\n')
    wrap = lines_between(P, '<div class="wrap">', '\n</div>\n\n<script>')[:-len('\n\n<script>')]
    wrap = re.sub(r'\s*<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:6px">.*?<div id="bedTabs".*?</div>\s*</div>', '', wrap, count=1, flags=re.S)
    wrap = re.sub(r'\s*<div class="eyebrow">Neighborhood map</div>.*?<iframe id="mapframe"[^\n]*\n', '\n', wrap, count=1, flags=re.S)
    if 'mapframe' in wrap or 'bedTabs' in wrap and 'id="bedTabs"' in wrap: die('could not take out the iframe or the unit tabs')
    main_js = lines_between(P, '<script>\n(function(){\n  var money=', '</script>')
    # the unit tabs are gone (the map's buttons drive the page); the tab builder must not stop the rest
    t = "var bar=document.getElementById('bedTabs');"
    if main_js.count(t) != 1: die('unit tab builder not found')
    main_js = main_js.replace(t, t + " if(!bar) return;")
    sects = lines_between(P, '<details class="sect"><summary><span class="sect-ic">&#128202;</span><span class="sect-tx"><span class="sect-t">Every area, ranked',
                          '\n\n\n<script>', inclusive=False)
    sect_js = lines_between(P, '<script>\n/* Every designation charted over time.', '</script>') + '\n' + \
              lines_between(P, '<script>\n/* Every area as a bar,', '</script>')
    trbar = lines_between(P, '<div class="trbar">', '\n  </div>\n</div>')

    # the map page's buttons drive the CB6 page's sections too (map codes 1br.. -> page codes br1..)
    bridge = ('<script>\n/* one set of unit-size buttons for the whole page */\n(function(){\n'
              "  var M={studio:'studio','1br':'br1','2br':'br2','3br':'br3'};\n"
              "  var bc=document.getElementById('bed-controls'); if(!bc) return;\n"
              "  bc.addEventListener('click',function(e){var b=e.target.closest('[data-bed]'); if(!b) return;\n"
              "    var c=M[b.getAttribute('data-bed')]; if(!c) return; window.curBed=c; if(window.applyBed) window.applyBed();});\n"
              '})();\n</script>\n')

    # ---- assemble on the map page ----
    s = B
    s = p_head + s[s.index('<style>'):]                                     # the CB6 page's title and metadata
    s = s.replace('</head>', '<style>\n.cb6x{background:#f8f7f4;color:#132D65}\n' + scope_css(p_css) + '\n</style>\n</head>', 1)
    s = re.sub(r'<body>', '<body data-rankfile="/data/cb6-rank-history.json">', s, count=1)
    tb = re.search(r'<div class="top-bar">.*?\n</div>\n', s, re.S)
    if not tb: die('no top bar on the map page')
    s = s[:tb.start()] + '<div class="cb6x">' + hero + '</div>\n' + s[tb.end():]
    cap = re.search(r'<div class="map-caption">[^\n]*\n', s)
    if not cap: die('no map caption on the map page')
    s = s[:cap.end()] + '<div class="cb6x">\n' + wrap + '\n' + sects + '\n</div>\n' + s[cap.end():]
    s = s.replace('</body>', main_js + '\n' + sect_js + '\n' + bridge + '<div class="cb6x">' + trbar + '</div>\n'
                  '<script src="/assets/income-history.js" defer></script>\n</body>', 1)
    # the map page sits at the site root and asks for data/...; this page is one folder down
    s = re.sub(r'(["\'(])data/', lambda m: m.group(1) + '/data/', s)
    if s.count('id="map"') != 1 or 'iframe id="mapframe"' in s: die('page check failed')
    open(os.path.join(ROOT, 'rentcb6/index.html'), 'w').write(s)
    print('built rentcb6/index.html (%d KB), map built in' % (len(s) // 1024))


if __name__ == '__main__':
    main()
