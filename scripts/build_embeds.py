#!/usr/bin/env python3
"""Build pages into other pages, as their own copy (no iframe, no link).

    preservation/index.html  ->  into lessexpensive/index.html and bk/lessexpensive/index.html (no State housing part)
    statehousing/index.html  ->  into lessexpensive/index.html and bk/lessexpensive/index.html
    lessexpensive/index.html ->  into every rent and for-sale map page (after the housing-costs section)

Each source page becomes a block wrapped in <!--embed:NAME--> ... <!--/embed:NAME-->:
  * its styles are scoped to the block's wrapper so they cannot touch the host page;
  * every element id is renamed NAME-id (markup, labels, anchors, selectors and the strings its script
    looks them up by), so two pages' ids cannot collide;
  * its scripts are its own IIFEs, copied as they are apart from the id renames;
  * site chrome is left out: the site bar, the App Store badge, the signed note, the breadcrumb,
    the share/embed button and the tenants' rights bar (the host page has its own).
The block is rebuilt from the source page every run, so editing the source page and re-running keeps
every copy current. Run after scripts/build_cb6_page.py and before scripts/build_sales_pages.py
(build_sales_pages.py leaves embed blocks untouched).
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from build_cb6_page import scope_css          # noqa: E402

RENT_PAGES = ['rentcb6/index.html', 'bkrents/index.html', 'rent-map-boroughs.html', 'nycrents/index.html']


def die(m): sys.exit('build_embeds: ' + m)


def strip_block(s, start_pat, tag):
    m = re.search(start_pat, s)
    if not m: return s
    i, depth = m.start(), 0
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % tag, s[i:]):
        depth += -1 if t.group(1) else 1
        if depth == 0: return s[:i] + s[i + t.end():]
    return s


def js_literals(code, fn):
    out, i, n = [], 0, len(code)
    while i < n:
        c = code[i]
        if code.startswith('//', i) and (i == 0 or code[i - 1] != ':'):
            j = code.find('\n', i); j = n if j < 0 else j; out.append(code[i:j]); i = j; continue
        if code.startswith('/*', i):
            j = code.find('*/', i + 2); j = n if j < 0 else j + 2; out.append(code[i:j]); i = j; continue
        if c in '\'"':
            j = i + 1
            while j < n and code[j] != c and code[j] != '\n':
                j += 2 if code[j] == '\\' else 1
            if j >= n or code[j] != c: out.append(c); i += 1; continue
            out.append(c + fn(code[i + 1:j]) + c); i = j + 1; continue
        out.append(c); i += 1
    return ''.join(out)


def fragment(src, name, title=None, drop=(), drop_js=()):
    s = open(os.path.join(ROOT, src)).read()
    head = s[:s.index('<body')]
    css = ''
    for href in re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="(/assets/[^"?]+\.css)', head) + \
                re.findall(r'<link[^>]+href="(/assets/[^"?]+\.css)"[^>]+rel="stylesheet"', head):
        if 'vendor/' in href: continue
        css += open(os.path.join(ROOT, href.lstrip('/'))).read() + '\n'     # the site's shared page styles, scoped too
    css += '\n'.join(m.group(1) for m in re.finditer(r'<style[^>]*>(.*?)</style>', head, re.S))
    body = s[s.index('>', s.index('<body')) + 1:s.rindex('</body>')]
    # site chrome out
    body = re.sub(r'<script src="/assets/(site-bar|datastamp|income-history)\.js[^"]*"[^>]*></script>', '', body)
    body = re.sub(r'<a id="asb".*?</a><script>.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<script src="https?://[^"]+"></script>|<link[^>]+>', '', body)
    for pat, tag in [(r'<details class="mrnote"', 'details'), (r'<div class="trbar"', 'div'), (r'<div class="breadcrumb"', 'div'),
                     (r'<div class="embed-modal-bg"', 'div'),
                     (r'<div class="crumb"', 'div'), (r'<div class="nav">', 'div')]:
        while re.search(pat, body):
            n0 = len(body); body = strip_block(body, pat, tag)
            if len(body) == n0: break
    body = re.sub(r'<button[^>]*class="embed-fab"[^>]*>.*?</button>', '', body, flags=re.S)
    for pat, tag in drop:                         # sections left out on purpose (already shown elsewhere on the host)
        body = strip_block(body, pat, tag)
    for marker in drop_js:                        # and the scripts that only drive them
        body = re.sub(r'<script>(?:(?!</script>).)*?' + re.escape(marker) + r'.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<!--embed:[\w-]+-->.*?<!--/embed:[\w-]+-->', lambda m: m.group(0), body, flags=re.S)
    # ids
    ids = set(re.findall(r'\bid="([^"\'+]+)"', body)) | set(re.findall(r'\bid=\\?"([\w-]+-)\'\+', body))
    ids |= set(re.findall(r"""\bid=\\?["']([\w-]+-)['"]\s*\+""", body))
    ids.discard('asb')
    P = name + '-'
    def ren_html(h):
        for i in sorted(ids, key=len, reverse=True):
            h = re.sub(r'\b(id|for|aria-controls|aria-labelledby|data-target)=(\\?["\'])' + re.escape(i), lambda m: m.group(1) + '=' + m.group(2) + P + i, h)
            h = re.sub(r'href=(\\?["\'])#' + re.escape(i) + r'(?=\\?["\'])', lambda m: 'href=' + m.group(1) + '#' + P + i, h)
        return h
    def ren_lit(t):
        if t in ids: return P + t
        t2 = ren_html(t)
        for i in sorted(ids, key=len, reverse=True):
            t2 = re.sub(r'#' + re.escape(i) + r'(?![\w-])', '#' + P + i, t2)
        return t2
    parts = re.split(r'(<script\b[^>]*>.*?</script>)', body, flags=re.S)
    out = []
    for x in parts:
        if x.startswith('<script'):
            m = re.match(r'(<script\b[^>]*>)(.*?)(</script>)$', x, re.S)
            # ids built at run time (k+'Sel') are found through a document that tries NAME-id first
            proxy = ('(function(d,P){return new Proxy(d,{get:function(t,k){'
                     "if(k==='getElementById')return function(i){return t.getElementById(P+i)||t.getElementById(i);};"
                     "if(k==='querySelector'||k==='querySelectorAll')return function(s){return t[k](String(s).replace(/#([A-Za-z][\\w-]*)/g,function(m,i){return t.getElementById(P+i)?'#'+P+i:m;}));};"
                     "var v=t[k];return typeof v==='function'?v.bind(t):v;}});})(document,'%s')" % P)
            out.append(m.group(1) + '(function(document){\n' + js_literals(m.group(2), ren_lit) + '\n})(' + proxy + ');' + m.group(3))
        else:
            x = ren_html(x)
            def css_ren(m):
                c = m.group(2)
                for i in sorted(ids, key=len, reverse=True):
                    c = re.sub(r'#' + re.escape(i) + r'(?![\w-])', '#' + P + i, c)
                return m.group(1) + c + m.group(3)
            out.append(re.sub(r'(<style[^>]*>)(.*?)(</style>)', css_ren, x, flags=re.S))
    body = ''.join(out)
    for i in sorted(ids, key=len, reverse=True):
        css = re.sub(r'#' + re.escape(i) + r'(?![\w-])', '#' + P + i, css)
    wrap = 'emb-' + name
    roots = ''.join(m.group(1) for m in re.finditer(r':root\s*\{([^}]*)\}', css))   # CSS variables, given to the wrapper
    scoped = ('.' + wrap + '{' + roots + '}' if roots else '') + scope_css(css, '.' + wrap)
    head = ('<div class="emb-h"><span class="emb-t">%s</span></div>' % title) if title else ''
    return ('<!--embed:%s--><div class="%s" style="background:#f8f7f4;color:#132D65;border-top:3px solid #f47920">'
            '<style>.%s{font-family:"DM Sans",sans-serif;position:relative}%s</style>%s%s</div><!--/embed:%s-->'
            % (name, wrap, wrap, scoped, head, body, name))


def put(host, name, frag, before=None, after=None):
    p = os.path.join(ROOT, host); s = open(p).read()
    s = re.sub(r'<!--embed:%s-->.*?<!--/embed:%s-->' % (name, name), '', s, flags=re.S)
    if after:
        m = re.search(after, s)
        if not m: die('no anchor %r in %s' % (after, host))
        i = s.index('\n', m.end()) + 1 if '\n' in s[m.end():] else m.end()
    else:
        i = s.find(before)
        if i < 0: die('no anchor %r in %s' % (before, host))
    s = s[:i] + frag + '\n' + s[i:]
    open(p, 'w').write(s)
    print('embedded', name, 'into', host)


def main():
    # Neighborhood Preservation Companies: the /preservation directory and map, without its own copy of the
    # State housing section (the State housing page is built in separately, below)
    pr = fragment('preservation/index.html', 'pr', drop=[(r'<details class="sect hpbig" id="hpSec"', 'details')], drop_js=['hpBox', 'sh_map'])
    for host in ['lessexpensive/index.html', 'bk/lessexpensive/index.html']:
        put(host, 'pr', pr, before='  <div class="eyebrow">How to apply</div>')
    sh = fragment('statehousing/index.html', 'sh')
    for host in ['lessexpensive/index.html', 'bk/lessexpensive/index.html']:
        put(host, 'sh', sh, before='  <div class="foot">AMI figures')
    le = fragment('lessexpensive/index.html', 'le')
    for host in RENT_PAGES:
        put(host, 'le', le, after=r'<div class="(?:panel )?inchist"[^>]*></div>')


if __name__ == '__main__':
    main()
