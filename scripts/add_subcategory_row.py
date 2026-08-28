"""Show the department's second classification, clearly.

The Parks Department records two separate things: typecategory, which the page
already shows as Type, and subcategory, which cuts across it. Large Park appears
on Community Parks, Nature Areas and on a Parkway. Showing both without saying
they are different axes is what made it confusing.

Abbreviations are only expanded where the full wording appears elsewhere in the
department's own data. EXWY and REDEC are left exactly as written because I
cannot establish what they stand for.
"""
import json, re, glob

R='/home/claude/repo/'
src=json.load(open(R+'Parks_Properties_20260414.geojson'))
P={f['properties']['gispropnum']: f['properties'] for f in src['features']}

# every expansion below matches a typecategory string used verbatim in this
# same dataset, so none of it is invented
EXPAND={
 'JOP':'Jointly Operated Playground',
 'PKWY':'Parkway',
 'STRIP':'Strip',
 'Neighborhood Plgd':'Neighborhood Playground',
}
SKIP={'None',''}

def esc(v):
    return (str(v).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            .replace('"','&quot;'))

NOTE=('<p class="subnote">The Parks Department records this property two ways. '
      '<b>Type</b> is what the place is. <b>Also recorded as</b> is a second '
      'grouping it keeps alongside that, and the two are not the same question, '
      'so they often differ.</p>')

n=0; skipped_same=0
for f in sorted(glob.glob(R+'park/*.html')):
    s=open(f,encoding='utf-8').read()
    gm=re.search(r'Parks ID</span><span class="v">([^<]*)</span>', s)
    if not gm: continue
    p=P.get(gm.group(1).strip())
    if not p: continue
    sub=str(p.get('subcategory') or '').strip()
    typ=str(p.get('typecategory') or '').strip()
    if sub in SKIP: continue
    if sub == typ:                      # says nothing new
        skipped_same+=1; continue
    if 'class="k">Also recorded as<' in s: continue
    shown = EXPAND.get(sub)
    label = f'{shown} <span class="raw">({sub})</span>' if shown else esc(sub)
    tm=re.search(r'<li><span class="k">Type</span><span class="v">[^<]*</span></li>', s)
    if not tm: continue
    row=f'<li><span class="k">Also recorded as</span><span class="v">{label}</span></li>'
    s=s[:tm.end()]+row+s[tm.end():]
    # the explanation goes once, right under the list
    um=re.search(r'(<ul class="kv">.*?</ul>)', s, re.S)
    if um and 'subnote' not in s:
        s=s[:um.end()]+NOTE+s[um.end():]
    open(f,'w',encoding='utf-8').write(s)
    n+=1
print('pages given the second classification:', n)
print('skipped because subcategory repeated the type:', skipped_same)
