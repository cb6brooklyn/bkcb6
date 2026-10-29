#!/usr/bin/env python3
"""Build the for-sale map pages from the rent map pages, so they are the same maps, same colours, same
layout, drawing data/sales/ (built by scripts/update_sales_maps.py).

    rentcb6/index.html       -> salescb6/index.html
    rent-map-cb6.html        -> sales-map-cb6.html
    bkrents/index.html       -> bksales/index.html
    rent-map-boroughs.html   -> sales-map-boroughs.html
    nycrents/index.html      -> nycsales/index.html

Run it again whenever a rent page changes. It also puts the Rent / For sale switch on both versions.
Unit-size buttons become home types: Studio -> All homes, 1BR -> Condos, 2BR -> Co-ops, 3BR+ -> Single-family.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = [('rentcb6/index.html', 'salescb6/index.html', '/housecostavail', '/salescb6'),
         ('rent-map-cb6.html', 'sales-map-cb6.html', '/rent-map-cb6.html', '/sales-map-cb6.html'),
         ('bkrents/index.html', 'bksales/index.html', '/bkrents', '/bksales'),
         ('rent-map-boroughs.html', 'sales-map-boroughs.html', '/rent-map-boroughs.html', '/sales-map-boroughs.html'),
         ('nycrents/index.html', 'nycsales/index.html', '/nycrents', '/nycsales')]
LINKS = [(a, b) for _, _, a, b in PAGES] + [('/rentcb6', '/salescb6')]
SALES_FILES = sorted(f for f in os.listdir(os.path.join(ROOT, 'data', 'sales')))

# phrase replacements, longest first, applied only to prose (text nodes and prose-like string literals)
PHRASES = [
    ('Median asking rent is what landlords list, not what tenants pay.', 'Median asking price is what sellers list, not what buyers pay.'),
    ('what you would owe at lease signing', 'what it takes to buy'),
    ('What it costs to rent', 'What it costs to buy'), ('what it costs to rent', 'what it costs to buy'),
    ('1st mo + 1mo deposit', '20% down payment'),
    ('1st month + 1 month deposit', '20% down payment'),
    ('Move-in', 'Down payment'), ('move-in cost', 'down payment'), ('MOVE-IN', 'DOWN PAYMENT'),
    ('rental listings', 'listings for sale'), ('Rental listings', 'Listings for sale'),
    ('rental inventory', 'homes listed for sale'), ('rentalInventory', 'totalInventory'),
    ('units of that size', 'homes of that type'), ('of that unit size', 'of that home type'),
    ('unit sizes', 'home types'), ('Unit sizes', 'Home types'),
    ('unit size', 'home type'), ('Unit size', 'Home type'), ('UNIT SIZE', 'HOME TYPE'),
    ('unit type', 'home type'), ('Unit type', 'Home type'), ('UNIT TYPE', 'HOME TYPE'),
    ('Studio through 3+ bedroom', 'All homes, condos, co-ops and single-family homes'),
    ('3+ Bedroom', 'Single-family'), ('3+ bedroom', 'single-family'), ('3 Bedroom', 'Single-family'), ('three bedroom', 'single-family home'),
    ('2 Bedroom', 'Co-ops'), ('2 bedroom', 'co-ops'), ('1 Bedroom', 'Condos'), ('1 bedroom', 'condos'),
    ('One bedroom', 'Condos'), ('one bedroom', 'condos'), ('Two bedroom', 'Co-ops'), ('two bedroom', 'co-ops'),
    ('3BR+', 'Single-family'), ('3+ BR', 'Single-family'), ('3+BR', 'Single-family'), ('3BR', 'Single-family'),
    ('2BR', 'Co-ops'), ('2 BR', 'Co-ops'), ('1BR', 'Condos'), ('1 BR', 'Condos'),
    ('Studio', 'All homes'),
    ('landlords', 'sellers'), ('tenants', 'buyers'), ('renters', 'buyers'),
    ('/month', ''), ('/mo', ''),
    ('Housing &amp; Rent', 'Housing &amp; Rent'), ('Housing & Rent', 'Housing & Rent'),
    ('Rents', 'Home Prices'), ('rents', 'prices'), ('Rent', 'Price'), ('RENT', 'PRICE'), ('rent', 'price'),
    ('Renting', 'Buying'), ('renting', 'buying'), ('Rental', 'Sale'), ('rental', 'sale'),
    ('Listings', 'Homes for sale'),
]
WORD = re.compile('|'.join(r'(?<![\w-])' + re.escape(a) + r'(?![\w-])' if a[0].isalnum() and a[-1].isalnum() else re.escape(a)
                           for a, _ in PHRASES))
MAP = dict(PHRASES)


def prose(seg):
    if not re.search(r'[A-Za-z]', seg): return False
    bare = re.sub(r'&#?\w+;', ' ', seg)
    if re.search(r'[;{}]|==|&&|\|\||=>|\bfunction\b|\bvar\b|\breturn\b', bare): return False
    if re.fullmatch(r'[\w./#:?=&%+-]*', seg) and not re.fullmatch(r'(Studio|[123]BR\+?|Rents?)', seg): return False
    return True


def swap(seg, force=False):
    return WORD.sub(lambda m: MAP[m.group(0)], seg) if (force or prose(seg)) else seg


def swap_tag(tag):
    """prose attributes inside one tag"""
    return re.sub(r'(\b(?:content|alt|title|aria-label|placeholder)=)(["\'])(.*?)\2',
                  lambda m: m.group(1) + m.group(2) + swap(m.group(3), True) + m.group(2), tag)


def swap_html(seg):
    """prose replacements inside a piece of HTML: only text between tags"""
    parts = re.split(r'(<[^>]*>)', seg)
    return ''.join(swap_tag(x) if x.startswith('<') and x.endswith('>') else swap(x, bool(x.strip())) for x in parts)


def js_strings(code):
    """rewrite string literals in a script, leaving code and comments alone"""
    out, i, n = [], 0, len(code)
    while i < n:
        c = code[i]
        if c == '/' and code.startswith('//', i):
            j = code.find('\n', i); j = n if j < 0 else j
            out.append(code[i:j]); i = j; continue
        if c == '/' and code.startswith('/*', i):
            j = code.find('*/', i + 2); j = n if j < 0 else j + 2
            out.append(code[i:j]); i = j; continue
        if c in '\'"`':
            j = i + 1
            while j < n and code[j] != c and (c == '`' or code[j] != '\n'):
                j += 2 if code[j] == '\\' else 1
            if j >= n or code[j] != c:      # not a string (a quote inside a regex literal, say)
                out.append(c); i += 1; continue
            lit = code[i + 1:j]
            if c == '`' or '${' in lit: new = lit
            elif '<' in lit or '>' in lit: new = swap_html(lit)
            else: new = swap(lit)
            out.append(c + new + c); i = j + 1; continue
        out.append(c); i += 1
    return ''.join(out)


def retext(s):
    parts = re.split(r'(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>)', s, flags=re.S)
    out = []
    for x in parts:
        if x.startswith('<style'): out.append(x)
        elif x.startswith('<script'):
            m = re.match(r'(<script\b[^>]*>)(.*?)(</script>)$', x, re.S)
            out.append(m.group(1) + js_strings(m.group(2)) + m.group(3))
        else:
            out.append(swap_html(x))
    return ''.join(out)


LEVELS = [('CB6', '/housecostavail', '/salescb6'), ('Brooklyn, by community board', '/bkrents', '/bksales'),
          ('All five boroughs', '/rent-map-boroughs.html', '/sales-map-boroughs.html'), ('Citywide, by community district', '/nycrents', '/nycsales')]


def toggle(here, rent_url, sale_url):
    r_on, s_on = (' on', '') if here == 'rent' else ('', ' on')
    return ('<div class="rs-toggle" style="display:flex;background:#0d1b4b;padding:10px 14px;border-bottom:1px solid rgba(255,255,255,.12)">'
            '<style>.rs-toggle a{flex:1;text-align:center;padding:9px 8px;font-family:\'DM Sans\',sans-serif;font-size:.9rem;font-weight:800;'
            'border:2px solid #f47920;color:#fff;text-decoration:none}.rs-toggle a:first-child{border-radius:10px 0 0 10px}'
            '.rs-toggle a:last-child{border-radius:0 10px 10px 0;border-left:0}.rs-toggle a.on{background:#f47920}</style>'
            '<a class="%s" href="%s">Rent</a><a class="%s" href="%s">For sale</a></div>' % (r_on.strip(), rent_url, s_on.strip(), sale_url)
            # on the CB6 page only: the same maps for Brooklyn, the five boroughs and the whole city, folded until tapped
            + ('<details class="lv-more" style="background:#0d1b4b;padding:0 14px 10px;border-bottom:1px solid rgba(255,255,255,.12)">'
               '<style>.lv-more>summary{cursor:pointer;list-style:none;color:#fff;font-family:\'DM Sans\',sans-serif;font-size:.85rem;font-weight:700;padding:8px 0}'
               '.lv-more>summary::-webkit-details-marker{display:none}.lv-more>summary:after{content:" \\25BE";color:#f47920}.lv-more[open]>summary:after{content:" \\25B4"}'
               '.lv-more .lv-row{display:flex;align-items:center;gap:8px;padding:6px 0;border-top:1px solid rgba(255,255,255,.12)}'
               '.lv-more .lv-t{flex:1;color:#fff;font-family:\'DM Sans\',sans-serif;font-size:.85rem;font-weight:600}'
               '.lv-more .lv-row a{padding:6px 14px;border:1.5px solid #f47920;border-radius:999px;color:#fff;text-decoration:none;font-family:\'DM Sans\',sans-serif;font-size:.78rem;font-weight:700}</style>'
               '<summary>Brooklyn, the boroughs and the whole city</summary>'
               + ''.join('<div class="lv-row"><span class="lv-t">%s</span><a href="%s">Rent</a><a href="%s">For sale</a></div>' % (lab, r, s_) for lab, r, s_ in LEVELS[1:])
               + '</details>' if rent_url == '/housecostavail' else '')
            # inside the apps the page is a screen of the app, not a website: no breadcrumbs, back links or share button
            + '<script>(function(){try{if(/[?&]app=1\\b/.test(location.search)||location.protocol==="bkcb:"||sessionStorage.getItem("bkapp")==="1")'
              'document.documentElement.classList.add("inapp")}catch(e){}})();</script>'
            # inside the apps a page is a file in the pack: point Rent / For sale and the other levels at the file itself
            + '<script>(function(){function go(){if(!document.documentElement.classList.contains("inapp"))return;'
              'document.querySelectorAll(".rs-toggle a[href^=\'/\'],.lv-more a[href^=\'/\']").forEach(function(a){'
              'var h=a.getAttribute("href").split("?")[0];if(!/\\.html$/.test(h))h=h.replace(/\\/$/,"")+"/index.html";'
              'a.setAttribute("href",h+"?app=1");});}'
              'if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",go);else go();})();</script>'
              '<style>.inapp .breadcrumb,.inapp .back-link,.inapp .embed-fab,.inapp .embed-modal-bg{display:none!important}</style>'
            # the "On this page" menu, and the long parts folded until opened
            + '<script src="/assets/page-guide.js" defer></script>')


MARK_A, MARK_B = '<!--rs-toggle-->', '<!--/rs-toggle-->'

# Leaflet and Chart.js from the site itself, so the pages (and the app screens that show them) work offline
VENDOR = [('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js', '/assets/vendor/leaflet-1.9.4/leaflet.js'),
          ('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css', '/assets/vendor/leaflet-1.9.4/leaflet.css'),
          ('https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js', '/assets/vendor/chartjs-4.4.1/chart.umd.min.js'),
          ('https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js', '/assets/vendor/chartjs-4.4.1/chart.umd.min.js')]


def vendorize(s):
    for a, b in VENDOR: s = s.replace(a, b)
    return s


def put_toggle(s, html):
    s = re.sub(re.escape(MARK_A) + '.*?' + re.escape(MARK_B), '', s, flags=re.S)
    i = s.find('<div class="top-bar"')
    if i >= 0: j = s.find('</div>', i) + len('</div>')
    else:
        j = s.find('<div class="datastamp"')
        if j < 0: sys.exit('no place for the toggle')
    return s[:j] + MARK_A + html + MARK_B + s[j:]


def drop(s, start_pat, tag):
    """remove the first element whose opening tag matches start_pat, with nesting of the same tag"""
    m = re.search(start_pat, s)
    if not m: return s
    i = m.start(); depth = 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % tag, s[i:]):
        depth += -1 if t.group(1) else 1
        if depth == 0: return s[:i] + s[i + t.end():]
    return s


def build(src, dst, rent_url, sale_url):
    s = open(os.path.join(ROOT, src)).read()
    # rent page gets the switch (only the marked block changes)
    embed = src == 'rent-map-cb6.html'   # drawn inside rentcb6 in an iframe; the page around it has the switch
    if not embed:
        t = vendorize(put_toggle(s, toggle('rent', rent_url, sale_url)))
        open(os.path.join(ROOT, src), 'w').write(t)
    s = re.sub(re.escape(MARK_A) + '.*?' + re.escape(MARK_B), '', s, flags=re.S)
    # pages built into this one (scripts/build_embeds.py) are copied untouched
    held = []
    def hold(m): held.append(m.group(0)); return '<!--held:%d-->' % (len(held) - 1)
    s = re.sub(r'<!--embed:([\w-]+)-->.*?<!--/embed:\1-->', hold, s, flags=re.S)
    # Mike's signed note is about rent; it is his text, so it is not reworded for the sale page
    s = drop(s, r'<details class="mrnote"', 'details')
    # rent-only sections: lotteries / affordable housing and tenants' rights
    for pat in [r'<div[^>]*class="[^"]*afford[^"]*"', r'<section[^>]*class="[^"]*afford[^"]*"', r'<div[^>]*class="[^"]*tenant[^"]*"',
                r'<a[^>]*class="[^"]*afford-cta[^"]*"']:
        while re.search(pat, s):
            n = len(s); s = drop(s, pat, re.match(r'<(\w+)', pat.replace('\\', '')).group(1))
            if len(s) == n: break
    # down payment (20% of price) in place of rent move-in cost (first month plus deposit)
    for v in ['mid', 'signVal', 'p[k]', 'bv', '_bv', 'v', 'bedRent']:
        s = s.replace('money(%s*2)' % v, 'money(Math.round(%s*0.2))' % v)
    s = s.replace('1st mo + 1mo deposit', '20% down')
    s = s.replace('Move-in cost assumes first month plus a one-month security deposit (NYC caps deposits at one month for most apartments; the 2025 FARE Act shifts broker fees to whoever hires the broker, usually the landlord).',
                  'Down payment is 20% of the median asking price.')
    s = s.replace('the move-in cost (first month plus one-month deposit)', 'the down payment (20% of the median asking price)')
    s = re.sub(r'(due )?at signing', 'down payment', s)
    s = s.replace('At signing', 'Down payment')
    # axis labels: prices run to millions, so $1.2M / $850K instead of $1200.0k
    fmt = "(v>=1e6?'$'+(v/1e6).toFixed(1)+'M':'$'+Math.round(v/1000)+'K')"
    s = s.replace("return '$'+(v/1000).toFixed(1)+'k'", 'return ' + fmt).replace("return '$'+(v/1000).toFixed(0)+'k'", 'return ' + fmt)
    # rent-only links and sections: affordable housing lotteries, the rent report, rent history, tenants' rights
    s = re.sub(r'<a class="cta" href="/(lessexpensive|rentreport|rentpastpresent)".*?</a>\s*', '', s)
    s = re.sub(r'<a class="afford-cta".*?</a>\s*', '', s, flags=re.S)
    s = re.sub(r'<a class="rsr-link" target="_top" href="/rentpastpresent">[^<]*</a>', '', s)
    s = drop(s, r'<div class="trbar"', 'div')
    for f in SALES_FILES:
        s = re.sub(r'(?<![\w/])(/?)data/' + re.escape(f), lambda m: m.group(1) + 'data/sales/' + f, s)
    for a, b in LINKS:
        s = re.sub(r'(["\'])' + re.escape(a) + r'(?=["\'?#/])', lambda m: m.group(1) + b, s)
        s = s.replace('https://bkcb6.app' + a + '"', 'https://bkcb6.app' + b + '"')
    s = retext(s)
    s = re.sub(r'<!--held:(\d+)-->', lambda m: held[int(m.group(1))], s)
    if not embed: s = put_toggle(s, toggle('sale', rent_url, sale_url))
    s = vendorize(s)
    os.makedirs(os.path.dirname(os.path.join(ROOT, dst)) or ROOT, exist_ok=True)
    open(os.path.join(ROOT, dst), 'w').write(s)
    print('built', dst)


if __name__ == '__main__':
    for p in PAGES: build(*p)
    # the CB6 page's own address is /housecostavail; /rentcb6 stays as the same page so old links keep working
    os.makedirs(os.path.join(ROOT, 'housecostavail'), exist_ok=True)
    open(os.path.join(ROOT, 'housecostavail/index.html'), 'w').write(open(os.path.join(ROOT, 'rentcb6/index.html')).read())
    print('built housecostavail/index.html (same page as rentcb6)')
