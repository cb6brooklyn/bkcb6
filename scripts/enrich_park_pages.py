"""Add the fields the park pages never carried, and fix the truncated ZIPs.

Every district value comes from geometry (build_park_districts.py). Congress is
added for the first time. ZIP keeps the source value except on the 3 records the
source truncates at 50 characters, where only the complete ZIPs are printed.
Nothing is inferred: subcategory, jurisdiction, waterfront, acquisition date and
sign name are printed exactly as the department records them.
"""
import json, re, glob, os

R='/home/claude/repo/'
D=json.load(open('/home/claude/park_all_districts.json'))
src=json.load(open(R+'Parks_Properties_20260414.geojson'))
P={f['properties']['gispropnum']: f['properties']
   for f in src['features'] if f['properties'].get('gispropnum')}

def esc(v):
    return (str(v).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            .replace('"','&quot;'))

def join(parts):
    if not parts: return ''
    if len(parts)==1: return parts[0]
    return ', '.join(parts[:-1]) + ' and ' + parts[-1]

def zips(v):
    """The source truncates this field at exactly 50 characters on 3 records.
    Keep only the parts that are complete five digit ZIPs."""
    v=str(v or '').strip()
    if not v: return None, False
    parts=[x.strip() for x in v.split(',')]
    good=[x for x in parts if re.fullmatch(r'\d{5}', x)]
    truncated = len(v)==50 and len(good)<len(parts)
    if not good: return None, truncated
    return join(good), truncated

def year(v):
    m=re.match(r'^(\d{4})-', str(v or ''))
    return m.group(1) if m else None

def li(k, v):
    return f'<li><span class="k">{k}</span><span class="v">{v}</span></li>'

added=0; zfixed=0; pages=0
for f in sorted(glob.glob(R+'park/*.html')):
    s=open(f,encoding='utf-8').read()
    gm=re.search(r'Parks ID</span><span class="v">([^<]*)</span>', s)
    if not gm: continue
    gid=gm.group(1).strip()
    p=P.get(gid)
    if not p: continue
    rec=D.get(gid) or {}
    orig=s

    # ZIP: replace only where the source is truncated
    zm=re.search(r'(<li><span class="k">ZIP</span><span class="v">)([^<]*)(</span></li>)', s)
    if zm:
        zv, trunc = zips(p.get('zipcode'))
        if zv and trunc and zm.group(2)!=zv:
            s=s[:zm.start()]+zm.group(1)+esc(zv)+zm.group(3)+s[zm.end():]
            zfixed+=1

    # Congress, computed. Insert after Senate so the district rows stay together.
    if 'class="k">Congress<' not in s and rec.get('cong'):
        cv=join([str(n) for n in sorted(int(c) for c in rec['cong'])])
        sm=re.search(r'<li><span class="k">Senate</span><span class="v">[^<]*</span></li>', s)
        if sm:
            s=s[:sm.end()]+li('Congress', esc(cv))+s[sm.end():]

    # What the department says the property actually is, and who runs it.
    # Jurisdiction already appears on 361 pages and Waterfront on 177, both
    # already correct, so neither is added here. Only genuinely absent rows.
    extra=[]
    if p.get('subcategory') and str(p['subcategory']).lower()!='none'        and 'class="k">Category<' not in s:
        extra.append(li('Category', esc(p['subcategory'])))
    y=year(p.get('acquisitiondate'))
    if y and 'class="k">Acquired<' not in s:
        extra.append(li('Acquired', esc(y)))
    sn=str(p.get('signname') or '').strip()
    n311=str(p.get('name311') or '').strip()
    if sn and n311 and sn!=n311 and 'class="k">Sign name<' not in s:
        extra.append(li('Sign name', esc(sn)))

    if extra:
        pm=re.search(r'<li><span class="k">Parks ID</span><span class="v">[^<]*</span></li>', s)
        if pm:
            s=s[:pm.end()]+''.join(extra)+s[pm.end():]
            added+=1

    if s!=orig:
        open(f,'w',encoding='utf-8').write(s); pages+=1

print('pages written:', pages)
print('  truncated ZIPs corrected:', zfixed)
print('  pages given the extra rows:', added)
