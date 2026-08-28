import json, re, os
R='/home/claude/repo/'
liq=json.load(open(R+'data/liquor/index.json'))
cert=json.load(open(R+'data/certified/index.json'))
food=json.load(open(R+'data/certified/food.json'))

BORO={'brooklyn.html':('Brooklyn','3'),'manhattan.html':('Manhattan','1'),
      'queens.html':('Queens','4'),'bronx.html':('Bronx','2'),
      'statenisland.html':('Staten Island','5')}

def counts(code):
    L=sum(v for k,v in liq['byCd'].items() if k[0]==code)
    C=sum(v for k,v in cert['byCd'].items() if k[0]==code)
    F=sum(1 for r in food['biz'] if r['cd'][0]==code)
    return L,C,F

def block(name, code):
    L,C,F=counts(code)
    q=name.replace(' ','%20')
    return f'''<div class="boro-drop-section" id="sec-business">
<button class="boro-drop-toggle" onclick="boroToggle(this)">
    &#127978; {name} Businesses And Licences
    <span class="boro-drop-arr">&#9660;</span>
  <a class="boro-drop-share" href="#sec-business" onclick="event.stopPropagation();history.replaceState(null,'','#sec-business')">&#128279;</a>
  </button>
  <div class="boro-drop-body">
    <div style="padding:14px 18px">
    <p style="font-size:.82rem;line-height:1.6;color:#333;margin-bottom:12px">Three city and state datasets filtered to {name}, each one searchable in full and breakable down to a single community board or council district.</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:9px">
      <a href="/liquor?boro={q}" style="display:block;border:1.5px solid var(--border,#e5e2db);border-radius:10px;padding:13px 14px;text-decoration:none;background:#fff">
        <div style="font-size:1.6rem;font-weight:900;color:var(--navy,#0d1b4b);line-height:1">{L:,}</div>
        <div style="font-size:.76rem;font-weight:700;color:var(--navy,#0d1b4b);margin-top:3px">Liquor licences</div>
        <div style="font-size:.63rem;font-family:'DM Mono',monospace;color:var(--muted,#6b6760);margin-top:3px;line-height:1.4">Active and pending, on premises &rarr;</div>
      </a>
      <a href="/certified?boro={q}" style="display:block;border:1.5px solid var(--border,#e5e2db);border-radius:10px;padding:13px 14px;text-decoration:none;background:#fff">
        <div style="font-size:1.6rem;font-weight:900;color:var(--navy,#0d1b4b);line-height:1">{C:,}</div>
        <div style="font-size:.76rem;font-weight:700;color:var(--navy,#0d1b4b);margin-top:3px">Certified businesses</div>
        <div style="font-size:.63rem;font-family:'DM Mono',monospace;color:var(--muted,#6b6760);margin-top:3px;line-height:1.4">MBE, WBE, EBE and LBE vendors &rarr;</div>
      </a>
      <a href="/certified?src=food&amp;boro={q}" style="display:block;border:1.5px solid var(--border,#e5e2db);border-radius:10px;padding:13px 14px;text-decoration:none;background:#fff">
        <div style="font-size:1.6rem;font-weight:900;color:var(--navy,#0d1b4b);line-height:1">{F:,}</div>
        <div style="font-size:.76rem;font-weight:700;color:var(--navy,#0d1b4b);margin-top:3px">Food stores</div>
        <div style="font-size:.63rem;font-family:'DM Mono',monospace;color:var(--muted,#6b6760);margin-top:3px;line-height:1.4">Supermarkets and greenmarkets &rarr;</div>
      </a>
    </div>
    <p style="font-size:.72rem;color:var(--muted,#6b6760);line-height:1.55;margin-top:11px">A liquor licence is not a business and one address can hold several. Certification covers only firms that applied for it. Food stores are those of 3,000 square feet or more, plus greenmarkets.</p>
    </div>
  </div>
</div>
'''

for f,(name,code) in BORO.items():
    p=R+f
    s=open(p,encoding='utf-8').read()
    if 'id="sec-business"' in s: print('already',f); continue
    anchor='<div class="boro-drop-section" id="sec-zoning">'
    if anchor not in s: print('NO ANCHOR',f); continue
    s=s.replace(anchor, block(name,code)+anchor, 1)
    open(p,'w',encoding='utf-8').write(s)
    L,C,F=counts(code)
    print(f'{name:14} liquor {L:6,}  certified {C:5,}  food {F:5,}')
