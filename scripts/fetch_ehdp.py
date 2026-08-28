import urllib.request, json, os, time, collections
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36'}
B='https://raw.githubusercontent.com/nychealth/EHDP-data/production/indicators/'
C='/home/claude/ehdp/'
os.makedirs(C,exist_ok=True)
def gj(p, cache=True):
    k=C+p.replace('/','_')
    if cache and os.path.exists(k): return json.load(open(k))
    for a in range(3):
        try:
            r=urllib.request.urlopen(urllib.request.Request(B+p,headers=UA),timeout=60)
            d=json.loads(r.read().decode('utf-8','ignore'))
            if cache: json.dump(d,open(k,'w'))
            time.sleep(0.25); return d
        except Exception as e:
            if a==2: return None
            time.sleep(2*(a+1))

meta=json.load(open('/home/claude/ehdp_meta.json'))
want={}
for ind in meta:
    for me in ind.get('Measures') or []:
        if 'CD' in (me.get('AvailableGeoTypes') or []):
            want.setdefault(ind['IndicatorID'],[]).append(me)
print('indicators with CD data:',len(want))

got=0; fail=[]
for i,iid in enumerate(sorted(want)):
    d=gj('data/%d.json'%iid)
    if d is None: fail.append(iid)
    else: got+=1
    if i%20==0: print(f'  {i}/{len(want)}',flush=True)
print('downloaded:',got,'| failed:',fail)
