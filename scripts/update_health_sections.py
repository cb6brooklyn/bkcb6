import json, re, glob, os
R='/home/claude/repo/'
SLUG={'bk':'3','mn':'1','qn':'4','bx':'2','si':'5'}
BORO={'1':'Manhattan','2':'Bronx','3':'Brooklyn','4':'Queens','5':'Staten Island'}
idx=json.load(open(R+'data/health/index.json'))
le=json.load(open(R+'data/health/life-expectancy.json'))

def leline(v, ref, refname):
    d=v-ref
    if abs(d)<0.05: return 'level with '+refname+' at '+('%.1f'%ref)
    return ('%.1f years %s %s at %.1f' % (abs(d), 'above' if d>0 else 'below', refname, ref))

def block(cd, short):
    n=sum(1 for mid in idx['latest'] if cd in idx['latest'][mid])
    v=le['cd'].get(cd); rank=le['rank'].get(cd); nm=le['names'].get(cd,short)
    boro=BORO[cd[0]]; bv=le['boroughs'].get(boro)
    hero=''
    if v is not None:
        hero=(f'<div style="background:var(--navy,#0d1b4b);color:#fff;border-radius:11px;padding:14px 15px;margin-bottom:12px">'
              f'<div style="font-family:\'DM Mono\',monospace;font-size:.56rem;text-transform:uppercase;letter-spacing:.11em;color:var(--orange,#f47920);font-weight:700">Life expectancy at birth</div>'
              f'<div style="font-size:2.4rem;font-weight:900;line-height:1;margin-top:4px">{v:.1f}</div>'
              f'<div style="font-size:.8rem;font-weight:700;color:rgba(255,255,255,.75);margin-top:2px">years &middot; {nm}</div>'
              f'<div style="font-size:.78rem;line-height:1.6;color:rgba(255,255,255,.9);margin-top:9px">'
              f'{leline(v, le["city"], "the citywide")}'
              + (f', and {leline(v, bv, boro)}' if bv is not None else '')
              + f'. Ranks <b>{rank} of 59</b> districts.</div></div>')
    return f'''<div class="drop-section" id="sec-health-data">
<button class="drop-toggle" onclick="cbToggle(this)">
    &#129658; Health And Environment Data
    <span class="drop-arr">&#9660;</span>
<a class="drop-share" href="#sec-health-data" onclick="event.stopPropagation();history.replaceState(null,'','#sec-health-data')">&#128279;</a>
</button>
<div class="drop-body">
<div style="padding:14px 18px">
{hero}
<p style="font-size:.8rem;line-height:1.6;color:#333;margin-bottom:11px">Another <b>{n} measures</b> are published for {short} by the city Health Department, covering asthma, air quality, mortality, housing conditions, mental health and more. Each charts over time and ranks against the other 58 districts.</p>
<a href="/health?cd={cd}" style="display:inline-block;background:var(--orange,#f47920);color:#fff;font-size:.8rem;font-weight:800;text-decoration:none;border-radius:999px;padding:11px 18px">Open the health data for {short} &rarr;</a>
<p style="font-size:.72rem;color:var(--muted,#6b6760);line-height:1.55;margin-top:10px">Life expectancy from the 2026 Community Health Profiles, 2013 to 2022. Everything else from the Environment and Health Data Portal. Many of these are estimates with real uncertainty at district level.</p>
</div>
</div>
</div>
'''

files=[f for f in sorted(glob.glob(R+'cb-*-*.html'))
       if not os.path.basename(f).startswith('cb-office') and os.path.getsize(f)>50000]
done=0
for f in files:
    m=re.match(r'cb-([a-z]{2})-(\d+)\.html', os.path.basename(f))
    cd=SLUG[m.group(1)]+m.group(2).zfill(2)
    short=f'{BORO[cd[0]]} CB{int(cd[1:])}'
    s=open(f,encoding='utf-8').read()
    i=s.find('<div class="drop-section" id="sec-health-data">')
    if i<0: continue
    j=s.find('<div class="drop-section" id="sec-business">', i)
    if j<0: continue
    s=s[:i]+block(cd,short)+s[j:]
    open(f,'w',encoding='utf-8').write(s)
    done+=1
print('district pages updated with life expectancy:',done)

# ---- borough pages ----
BFILE={'brooklyn.html':'Brooklyn','manhattan.html':'Manhattan','queens.html':'Queens',
       'bronx.html':'Bronx','statenisland.html':'Staten Island'}
for f,name in BFILE.items():
    p=R+f
    s=open(p,encoding='utf-8').read()
    if 'id="sec-health-le"' in s: continue
    bv=le['boroughs'][name]
    code=[k for k,v in BORO.items() if v==name][0]
    mine={k:v for k,v in le['cd'].items() if k[0]==code}
    hi=max(mine,key=mine.get); lo=min(mine,key=mine.get)
    d=bv-le['city']
    cmp=('level with the citywide %.1f'%le['city']) if abs(d)<0.05 else ('%.1f years %s the citywide %.1f'%(abs(d),'above' if d>0 else 'below',le['city']))
    blk=f'''<div class="boro-drop-section" id="sec-health-le">
<button class="boro-drop-toggle" onclick="boroToggle(this)">
    &#129658; {name} Health And Life Expectancy
    <span class="boro-drop-arr">&#9660;</span>
  <a class="boro-drop-share" href="#sec-health-le" onclick="event.stopPropagation();history.replaceState(null,'','#sec-health-le')">&#128279;</a>
  </button>
  <div class="boro-drop-body">
    <div style="padding:14px 18px">
      <div style="background:var(--navy,#0d1b4b);color:#fff;border-radius:11px;padding:15px 16px">
        <div style="font-family:'DM Mono',monospace;font-size:.56rem;text-transform:uppercase;letter-spacing:.11em;color:var(--orange,#f47920);font-weight:700">Life expectancy at birth</div>
        <div style="font-size:2.6rem;font-weight:900;line-height:1;margin-top:4px">{bv:.1f}</div>
        <div style="font-size:.82rem;font-weight:700;color:rgba(255,255,255,.75);margin-top:2px">years &middot; {name}</div>
        <div style="font-size:.79rem;line-height:1.6;color:rgba(255,255,255,.9);margin-top:9px">{cmp}. Inside {name} it runs from <b>{le['cd'][hi]:.1f}</b> in {le['names'][hi]} to <b>{le['cd'][lo]:.1f}</b> in {le['names'][lo]}, a gap of {le['cd'][hi]-le['cd'][lo]:.1f} years.</div>
      </div>
      <p style="font-size:.8rem;line-height:1.6;color:#333;margin:12px 0">182 health and environment measures are published for every community district, each charting over time and ranking against the rest of the city.</p>
      <a href="/health" style="display:inline-block;background:var(--orange,#f47920);color:#fff;font-size:.8rem;font-weight:800;text-decoration:none;border-radius:999px;padding:11px 18px">Health data, district by district &rarr;</a>
      <p style="font-size:.72rem;color:var(--muted,#6b6760);line-height:1.55;margin-top:10px">Life expectancy from the NYC Health Department 2026 Community Health Profiles, 2013 to 2022 for boroughs and districts.</p>
    </div>
  </div>
</div>
'''
    anchor='<div class="boro-drop-section" id="sec-business">'
    if anchor not in s: print('NO ANCHOR',f); continue
    s=s.replace(anchor, blk+anchor, 1)
    open(p,'w',encoding='utf-8').write(s)
    print(f'  {name:14} {bv:.1f} years | range {le["cd"][lo]:.1f} to {le["cd"][hi]:.1f}')
