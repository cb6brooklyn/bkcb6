#!/usr/bin/env python3
"""Make every profile card in the CB6 block of /orgs/ searchable by name, address
and interest category. Adds data-s (search text) and data-c (categories) to each
card, one search box and a row of interest chips above all the sections. Re-run
after new cards are added; cards with no category entry below fail loudly."""
import json, re, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'orgs', 'index.html')

CATS = [
    ('arts', 'Arts and culture'),
    ('parks', 'Parks, gardens and environment'),
    ('water', 'Waterfront'),
    ('schools', 'Schools'),
    ('childcare', 'Childcare and preschools'),
    ('libraries', 'Libraries'),
    ('youth', 'Youth and families'),
    ('housing', 'Housing and tenants'),
    ('food', 'Food'),
    ('streets', 'Streets, bikes and transit'),
    ('business', 'Business and development'),
    ('civic', 'Civic and neighborhood groups'),
    ('health', 'Health and social services'),
    ('safety', 'Public safety and justice'),
    ('elected', 'Elected officials'),
    ('gov', 'Government agencies'),
]

C = {
 '6-15-green': 'parks', 'artichoke-dance-company': 'arts parks', 'artsgowanus': 'arts',
 'atlantic-avenue-ldc': 'business civic', 'bark-slope': 'business', 'bergen-bike-bus': 'streets youth',
 'bird-collective': 'parks business', 'books-are-magic': 'arts business', 'bric': 'arts',
 'brooklyn-botanic-garden': 'parks', 'brooklyn-bridge-park': 'parks water', 'brooklyn-conservatory-of-music': 'arts youth',
 'brooklyn-pop-up': 'business arts', 'brooklyn-pride': 'civic arts', 'brooklyn-public-library-cb6': 'libraries',
 'camp-friendship': 'food youth health', 'carroll-gardens-association': 'housing civic', 'chips': 'food health housing',
 'churches-united-for-fair-housing': 'housing', 'cobble-hill-association': 'civic', 'columbia-street-waterfront-association': 'civic water',
 'dubois-bunche-center': 'civic', 'fifth-avenue-committee': 'housing civic', 'fort-defiance-sidewalk-galleries': 'arts',
 'forth-on-fourth-avenue': 'streets civic', 'friends-of-firefighters': 'health safety', 'gowanus-canal-conservancy': 'parks water',
 'gowanus-dredgers': 'water parks', 'grown-up-bike-bus': 'streets', 'hook-arts-media': 'arts youth',
 'house-pepper': 'food business', 'jalopy-theatre': 'arts', 'nitehawk-prospect-park': 'arts business',
 'oldstonehouse': 'arts parks', 'pacemakers-dance-team': 'arts', 'park-slope-civic-council': 'civic',
 'park-slope-farmers-market': 'food', 'park-slope-fifth-avenue-bid': 'business streets', 'park-slope-food-coop': 'food',
 'park-slope-open-streets': 'streets', 'pioneer-works': 'arts', 'porch-stomp': 'arts', 'portside-newyork': 'water arts',
 'powerhouse-arts': 'arts', 'principles-gi-coffee-house': 'civic food', 'prospect-park-alliance': 'parks',
 'record-shop': 'arts business', 'red-hook-art-project': 'arts youth', 'red-hook-business-alliance': 'business',
 'red-hook-initiative': 'youth health', 'red-hook-lobster-pound': 'food business', 'resilient-red-hook': 'civic water',
 'rooftop-films': 'arts', 'sbidc': 'business', 'the-secret-garden': 'parks', 'smith-street-stage': 'arts',
 'south-brooklyn-dsa': 'civic', 'south-brooklyn-soccer': 'parks youth', 'southwest-brooklyn-tenant-union': 'housing',
 'street-lab': 'streets youth', 'strong-rope-brewery': 'food business', 'van-alen-institute': 'civic arts',
 'waterfront-museum': 'water arts', 'why-not-art': 'arts', 'wytchonymous-arts': 'arts',
 'brooklyn-community-board-6': 'gov civic', '76th-precinct': 'safety gov', '78th-precinct': 'safety gov',
 'dsny-brooklyn-6': 'gov streets', 'nyc-dot': 'gov streets', 'nyc-dep': 'gov water', 'nyc-hpd': 'gov housing',
 'nyc-parks-brooklyn': 'gov parks', 'nyc-planning': 'gov business', 'landmarks-preservation-commission': 'gov',
 'mta': 'gov streets', 'brooklyn-marine-terminal-development-corporation': 'gov water business',
 'cec-district-15': 'gov schools', 'rent-guidelines-board': 'gov housing', 'nycha-cb6': 'gov housing',
 'red-hook-community-justice-center': 'safety gov', 'new-york-city-council': 'gov elected', 'nyc-votes': 'gov civic',
 'nyc-public-schools-cb6': 'gov schools', 'eric-gonzalez': 'elected safety', 'letitia-james': 'elected safety',
}

def cats_for(slug, seat):
    if slug in C: return C[slug].split()
    s = seat.lower()
    if 'library' in s: return ['libraries']
    if any(k in s for k in ('council member', 'assembly member', 'senator', 'representative', 'borough president',
                            'mayor', 'public advocate', 'comptroller', 'governor', 'attorney general', 'district attorney')):
        return ['elected']
    if any(k in s for k in ('preschool', 'child care', 'infant', 'early childhood', 'pre-k center', 'childcare')):
        return ['childcare', 'youth']
    if 'school' in s or 'learning center' in s:
        return ['schools', 'youth']
    raise SystemExit('no category for %s (%s)' % (slug, seat))

addr = {'oldstonehouse': '336 3rd Street'}
for f in ('org-profiles-cal.json', 'gov-profiles.json', 'place-profiles.json'):
    for r in json.load(open(os.path.join(ROOT, 'data', f), encoding='utf-8')):
        addr[r['slug']] = ' '.join(x for x in [(r.get('addr') or '').replace('<br>', ', '), r.get('addr_note') or '',
                                               r.get('zip') or ''] if x)
src = open(os.path.join(ROOT, 'build_org_pages.py'), encoding='utf-8').read()
for m in re.finditer(r"'slug':'([^']+)'.*?'addr':'([^']*)'.*?'zip':'([^']*)'", src, re.S):
    addr.setdefault(m.group(1), m.group(2).replace('<br>', ', ') + ' ' + m.group(3))

s = open(P, encoding='utf-8').read()
a = s.index('<!--cb6profiles-->'); b = s.index('<!--/cb6profiles-->')
block = s[a:b]
LABEL = dict(CATS)
counts = {k: 0 for k, _ in CATS}

def card(m):
    slug, rest = m.group(1), m.group(2)
    nm = re.search(r'<span class="cbpn">([^<]*)</span>', rest).group(1)
    seat = re.search(r'<span class="cbps">([^<]*)</span>', rest).group(1)
    cs = cats_for(slug, html.unescape(seat))
    for c in cs: counts[c] += 1
    text = ' '.join([html.unescape(nm), html.unescape(seat), addr.get(slug, ''), ' '.join(LABEL[c] for c in cs)])
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.escape(re.sub(r'\s+', ' ', text).strip().lower(), quote=True)
    return '<a class="cbp" href="/%s/" data-c="%s" data-s="%s">%s</a>' % (slug, ' '.join(cs), text, rest)

block = re.sub(r'<a class="cbp" href="/([^"/]+)/?"(?: data-c="[^"]*")?(?: data-s="[^"]*")?>(.*?)</a>', card, block, flags=re.S)

# one search box and the interest chips, above every section
block = re.sub(r'<div class="cbpx">.*?</div><!--/cbpx-->', '', block, flags=re.S)
block = block.replace('<input id="cbpq" type="search" placeholder="Search CB6 organizations" autocomplete="off">', '')
chips = ''.join('<button type="button" class="cbpc" data-k="%s">%s</button>' % (k, l) for k, l in CATS if counts[k])
tools = ('<div class="cbpx"><input id="cbpq" type="search" placeholder="Search by name, address or interest" autocomplete="off">'
         '<div class="cbpcs">' + chips + '</div><div class="cbpn0" id="cbpn0" hidden>Nothing matches that.</div></div><!--/cbpx-->')
block = block.replace('<section class="cb6p">', '<section class="cb6p">' + tools, 1)

# the old name-only search script, replaced by one that covers every section
block = re.sub(r'<script>\(function\(\)\{var q=document.getElementById\("cbpq"\).*?</script>', '', block, flags=re.S)
block = re.sub(r'<style>\.cbpx\{.*?</style>', '', block, flags=re.S)
block = re.sub(r'<script>/\*cbpsearch\*/.*?</script>', '', block, flags=re.S)
block += ('<style>.cbpx{margin:0 0 14px}.cbpcs{display:flex;flex-wrap:wrap;gap:6px;margin-top:2px}'
          '.cbpc{font-family:"DM Mono",monospace;font-size:.62rem;letter-spacing:.04em;text-transform:uppercase;background:#fff;'
          'border:1.5px solid #e1dfd8;color:#555;border-radius:999px;padding:6px 11px;cursor:pointer}'
          '.cbpc.on{background:#0d1b4b;border-color:#0d1b4b;color:#fff}'
          '.cbpn0{padding:12px 2px;font-size:.88rem;color:#666}</style>'
          '<script>/*cbpsearch*/(function(){var q=document.getElementById("cbpq"),none=document.getElementById("cbpn0"),on={};'
          'var root=q.closest(".cb6p").parentNode;'
          'function head(g){var e=g.previousElementSibling;while(e&&e.tagName!=="H2")e=e.previousElementSibling;return e;}'
          'function run(){var t=q.value.toLowerCase().trim().replace(/\\s+/g," "),keys=Object.keys(on),total=0;'
          'var cards=[].slice.call(root.querySelectorAll(".cbp")),words=t?[t]:[];'
          'if(t&&!cards.some(function(a){return (a.getAttribute("data-s")||"").indexOf(t)>-1;}))words=t.split(" ");'
          'root.querySelectorAll(".cbpg").forEach(function(g){var n=0;g.querySelectorAll(".cbp").forEach(function(a){'
          'var s=a.getAttribute("data-s")||a.textContent.toLowerCase(),c=" "+(a.getAttribute("data-c")||"")+" ";'
          'var ok=words.every(function(w){return s.indexOf(w)>-1;})&&keys.every(function(k){return c.indexOf(" "+k+" ")>-1;});'
          'a.style.display=ok?"":"none";if(ok)n++;});'
          'g.style.display=n?"":"none";var h=head(g);if(h)h.style.display=n?"":"none";'
          'var p=h&&h.nextElementSibling;if(p&&p.tagName==="P")p.style.display=n?"":"none";total+=n;});'
          'none.hidden=total>0;}'
          'q.addEventListener("input",run);'
          'document.querySelectorAll(".cbpc").forEach(function(b){b.addEventListener("click",function(){var k=b.getAttribute("data-k");'
          'if(on[k]){delete on[k];b.classList.remove("on");}else{on[k]=1;b.classList.add("on");}run();});});})();</script>')
s = s[:a] + block + s[b:]
open(P, 'w', encoding='utf-8').write(s)
print('cards', block.count('class="cbp"'), counts)
