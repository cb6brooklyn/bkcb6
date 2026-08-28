import json, re, glob, os
R='/home/claude/repo/'
SLUG={'bk':'3','mn':'1','qn':'4','bx':'2','si':'5'}
BORO={'1':'Manhattan','2':'Bronx','3':'Brooklyn','4':'Queens','5':'Staten Island'}
idx=json.load(open(R+'data/health/index.json'))

# premature mortality, age-adjusted, is the closest district-level mortality measure
PM=[mid for mid,m in idx['measures'].items()
    if m['indName']=='Premature mortality' and 'Age-adjusted' in m['name']]
PM=PM[0] if PM else None

def block(cd, short):
    n=sum(1 for mid in idx['latest'] if cd in idx['latest'][mid])
    pm=idx['latest'].get(PM,{}).get(cd) if PM else None
    vals=sorted(idx['latest'].get(PM,{}).values(), reverse=True) if PM else []
    rank=(vals.index(pm)+1) if (pm is not None and pm in vals) else None
    pmline=''
    if pm is not None:
        pmline=(f'<p style="font-size:.78rem;line-height:1.55;color:#333;margin-top:10px">'
                f'Premature mortality, death before 65, runs at <b>{pm}</b> per 100,000 age adjusted here'
                + (f', which is {rank} highest of the 59 districts' if rank else '')
                + f'. The Health Department does not publish life expectancy by community district; this is the nearest measure it does.</p>')
    return f'''<div class="drop-section" id="sec-health-data">
<button class="drop-toggle" onclick="cbToggle(this)">
    &#129658; Health And Environment Data
    <span class="drop-arr">&#9660;</span>
<a class="drop-share" href="#sec-health-data" onclick="event.stopPropagation();history.replaceState(null,'','#sec-health-data')">&#128279;</a>
</button>
<div class="drop-body">
<div style="padding:14px 18px">
<p style="font-size:.8rem;line-height:1.6;color:#333;margin-bottom:11px"><b>{n} measures</b> published for {short} by the city Health Department, covering asthma, air quality, mortality, housing conditions, mental health and more. Each one charts over time and ranks against the other 58 districts.</p>
<a href="/health?cd={cd}" style="display:inline-block;background:var(--orange,#f47920);color:#fff;font-size:.8rem;font-weight:800;text-decoration:none;border-radius:999px;padding:11px 18px">Open the health data for {short} &rarr;</a>
{pmline}
<p style="font-size:.72rem;color:var(--muted,#6b6760);line-height:1.55;margin-top:10px">Source: NYC Department of Health and Mental Hygiene, Environment and Health Data Portal. Many of these measures are estimates with real uncertainty at district level.</p>
</div>
</div>
</div>
'''

files=[f for f in sorted(glob.glob(R+'cb-*-*.html'))
       if not os.path.basename(f).startswith('cb-office') and os.path.getsize(f)>50000]
done=0; skipped=[]
for f in files:
    m=re.match(r'cb-([a-z]{2})-(\d+)\.html', os.path.basename(f))
    cd=SLUG[m.group(1)]+m.group(2).zfill(2)
    short=f'{BORO[cd[0]]} CB{int(cd[1:])}'
    s=open(f,encoding='utf-8').read()
    if 'id="sec-health-data"' in s: continue
    anchor='<div class="drop-section" id="sec-business">'
    if anchor not in s: skipped.append(os.path.basename(f)); continue
    s=s.replace(anchor, block(cd,short)+anchor, 1)
    open(f,'w',encoding='utf-8').write(s)
    done+=1
print('injected into',done,'district pages | skipped',skipped)
print('premature mortality measure id:',PM)
