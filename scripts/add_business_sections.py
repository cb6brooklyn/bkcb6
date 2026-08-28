import json, re, glob, os

R='/home/claude/repo/'
BORO={'1':'Manhattan','2':'Bronx','3':'Brooklyn','4':'Queens','5':'Staten Island'}
SLUG={'bk':'3','mn':'1','qn':'4','bx':'2','si':'5'}

liq=json.load(open(R+'data/liquor/index.json'))
cert=json.load(open(R+'data/certified/index.json'))
food=json.load(open(R+'data/certified/food.json'))
foodCd={}
for r in food['biz']: foodCd[r['cd']]=foodCd.get(r['cd'],0)+1

def block(cd, label, short):
    L=liq['byCd'].get(cd,0)
    C=cert['byCd'].get(cd,0)
    F=foodCd.get(cd,0)
    return f'''<div class="drop-section" id="sec-business">
<button class="drop-toggle" onclick="cbToggle(this)">
    &#127978; Businesses And Licences In This District
    <span class="drop-arr">&#9660;</span>
<a class="drop-share" href="#sec-business" onclick="event.stopPropagation();history.replaceState(null,'','#sec-business')">&#128279;</a>
</button>
<div class="drop-body">
<div style="padding:14px 18px">
<p style="font-size:.8rem;line-height:1.6;color:#333;margin-bottom:12px">Three city and state datasets, each filtered to {short} and each searchable in full. Every figure below is a count of records placed inside this district by their own coordinates.</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:9px">
  <a href="/liquor?cd={cd}" style="display:block;border:1.5px solid var(--border,#e5e2db);border-radius:10px;padding:12px 13px;text-decoration:none;background:#fff">
    <div style="font-size:1.5rem;font-weight:900;color:var(--navy,#0d1b4b);line-height:1">{L:,}</div>
    <div style="font-size:.74rem;font-weight:700;color:var(--navy,#0d1b4b);margin-top:3px">Liquor licences</div>
    <div style="font-size:.63rem;font-family:'DM Mono',monospace;color:var(--muted,#6b6760);margin-top:3px;line-height:1.4">Active and pending, on premises. Search and map &rarr;</div>
  </a>
  <a href="/certified?cd={cd}" style="display:block;border:1.5px solid var(--border,#e5e2db);border-radius:10px;padding:12px 13px;text-decoration:none;background:#fff">
    <div style="font-size:1.5rem;font-weight:900;color:var(--navy,#0d1b4b);line-height:1">{C:,}</div>
    <div style="font-size:.74rem;font-weight:700;color:var(--navy,#0d1b4b);margin-top:3px">Certified businesses</div>
    <div style="font-size:.63rem;font-family:'DM Mono',monospace;color:var(--muted,#6b6760);margin-top:3px;line-height:1.4">MBE, WBE, EBE and LBE vendors &rarr;</div>
  </a>
  <a href="/certified?src=food&amp;cd={cd}" style="display:block;border:1.5px solid var(--border,#e5e2db);border-radius:10px;padding:12px 13px;text-decoration:none;background:#fff">
    <div style="font-size:1.5rem;font-weight:900;color:var(--navy,#0d1b4b);line-height:1">{F:,}</div>
    <div style="font-size:.74rem;font-weight:700;color:var(--navy,#0d1b4b);margin-top:3px">Food stores</div>
    <div style="font-size:.63rem;font-family:'DM Mono',monospace;color:var(--muted,#6b6760);margin-top:3px;line-height:1.4">Supermarkets and greenmarkets &rarr;</div>
  </a>
</div>
<p style="font-size:.72rem;color:var(--muted,#6b6760);line-height:1.55;margin-top:11px">A liquor licence is not a business and one address can hold several. Certification covers only firms that applied for it, not every business here. Food stores are those of 3,000 square feet or more, plus greenmarkets.</p>
</div>
</div>
</div>
'''

files=[f for f in sorted(glob.glob(R+'cb-*-*.html'))
       if not os.path.basename(f).startswith('cb-office') and os.path.getsize(f)>50000]
done=0; skipped=[]
for f in files:
    m=re.match(r'cb-([a-z]{2})-(\d+)\.html', os.path.basename(f))
    if not m: skipped.append(f); continue
    cd=SLUG[m.group(1)]+m.group(2).zfill(2)
    boro=BORO[cd[0]]
    label=f'{boro} Community Board {int(cd[1:])}'
    short=f'{boro} CB{int(cd[1:])}'
    s=open(f,encoding='utf-8').read()
    if 'id="sec-business"' in s: continue
    anchor='<div class="drop-section" id="sec-publicsafety">'
    if anchor not in s:
        skipped.append(os.path.basename(f)); continue
    s=s.replace(anchor, block(cd,label,short)+anchor, 1)
    open(f,'w',encoding='utf-8').write(s)
    done+=1

print('injected into', done, 'district pages')
print('skipped:', skipped)
