import pandas as pd, json, re, math
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

U='/mnt/user-data/uploads/'
df=pd.read_csv(U+'SBS_Certified_Business_List_20260827.csv', dtype=str, low_memory=False)
df=df[df['Latitude'].notna() & df['Longitude'].notna()].copy()
df['lat']=pd.to_numeric(df['Latitude'],errors='coerce')
df['lon']=pd.to_numeric(df['Longitude'],errors='coerce')
df=df[df['lat'].notna() & df['lon'].notna()]
print('geocoded rows:',len(df))

def load(fn,key):
    g=json.load(open(U+fn)); geoms=[];vals=[]
    for f in g['features']:
        geoms.append(shape(f['geometry']).buffer(0)); vals.append(f['properties'][key])
    return geoms,vals,STRtree(geoms)

ad_g,ad_v,ad_t=load('State_Assembly_Districts_20260827.geojson','assembly_district')
sd_g,sd_v,sd_t=load('State_Senate_Districts_20260827.geojson','st_sen_dist')

def assign(tree,geoms,vals,lon,lat):
    p=Point(lon,lat)
    for i in tree.query(p):
        if geoms[i].contains(p): return vals[i]
    return None

BORO={'MANHATTAN':'Manhattan','BROOKLYN':'Brooklyn','QUEENS':'Queens',
      'BRONX':'Bronx','STATEN IS':'Staten Island'}
CDB={'1':'Manhattan','2':'Bronx','3':'Brooklyn','4':'Queens','5':'Staten Island'}

def clean(v):
    if v is None or (isinstance(v,float) and math.isnan(v)): return ''
    s=str(v).strip()
    return '' if s.lower() in ('nan','none','n/a','/a','') else s

def phone(v):
    d=re.sub(r'\D','',clean(v))
    return f'({d[:3]}) {d[3:6]}-{d[6:10]}' if len(d)==10 else ''

def site(v):
    s=clean(v)
    if not s or '.' not in s: return ''
    if not s.lower().startswith(('http://','https://')): s='https://'+s
    return s

sectors={}; subs={}
recs=[]
for _,r in df.iterrows():
    cd=clean(r['Community Board'])
    if not cd or len(cd)!=3: continue
    sec=clean(r['NAICS_Sector']); sub=clean(r['NAICS_Subsector'])
    if sec and sec not in sectors: sectors[sec]=len(sectors)
    if sub and sub not in subs: subs[sub]=len(subs)
    name=clean(r['Vendor_DBA']) or clean(r['Vendor_Formal_Name'])
    if not name: continue
    a1=clean(r['Address_Line_1']); a2=clean(r['Address_Line_2'])
    rec={'n':name,'a':(a1+(' '+a2 if a2 else '')).strip(),'z':clean(r['Postcode'])[:5],
         'b':BORO.get(clean(r['Borough']), CDB.get(cd[0],'')),
         'cd':cd,'cc':clean(r['Council District']),
         'y':round(r['lat'],5),'x':round(r['lon'],5),
         'ct':clean(r['Certification']),'e':clean(r['Ethnicity']).title(),
         'p':phone(r['telephone']),'w':site(r['Website']),
         'd':clean(r['NAICS_Title'])}
    if sec: rec['s']=sectors[sec]
    if sub: rec['sb']=subs[sub]
    ad=assign(ad_t,ad_g,ad_v,r['lon'],r['lat']); sd=assign(sd_t,sd_g,sd_v,r['lon'],r['lat'])
    if ad: rec['ad']=int(ad)
    if sd: rec['sd']=int(sd)
    formal=clean(r['Vendor_Formal_Name'])
    if formal and formal.lower()!=name.lower(): rec['fn']=formal
    recs.append(rec)

print('records:',len(recs))
print('with assembly:',sum(1 for r in recs if 'ad' in r),'| senate:',sum(1 for r in recs if 'sd' in r))
out={'source':'NYC Department of Small Business Services, Certified Business List, via NYC Open Data',
     'fetched':'2026-08-27','count':len(recs),
     'sectors':[k for k,_ in sorted(sectors.items(),key=lambda kv:kv[1])],
     'subsectors':[k for k,_ in sorted(subs.items(),key=lambda kv:kv[1])],
     'biz':recs}
import os
os.makedirs('/home/claude/repo/data/certified',exist_ok=True)
p='/home/claude/repo/data/certified/businesses.json'
json.dump(out,open(p,'w'),separators=(',',':'))
print('bytes:',os.path.getsize(p))
