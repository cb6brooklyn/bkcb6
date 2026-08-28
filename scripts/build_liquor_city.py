import json, os, collections
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

U='/mnt/user-data/uploads/'
R='/home/claude/repo/'

# same class map the CB6 page uses, so the two agree
BEV={340:'Full Liquor',370:'Full Liquor',423:'Full Liquor',349:'Full Liquor',243:'Full Liquor',
     346:'Full Liquor',240:'Wine & Beer',267:'Wine & Beer',138:'Wine & Beer',249:'Wine & Beer',
     361:'Wine & Beer',416:'Brewery / Special',15:'Brewery / Special',14:'Brewery / Special',
     25:'Brewery / Special',31:'Brewery / Special',52:'Brewery / Special',56:'Brewery / Special'}
DETAIL={340:'Restaurant \u2014 Full Liquor',370:'Bar / Food & Beverage \u2014 Full Liquor',
        423:'Additional Bar \u2014 Full Liquor',349:'Club \u2014 Full Liquor',243:'Hotel \u2014 Full Liquor',
        346:'Catering Establishment \u2014 Full Liquor',240:'Restaurant \u2014 Wine & Beer',
        267:'Bar / Food & Beverage \u2014 Wine & Beer',138:'Food & Beverage \u2014 Wine & Beer',
        249:'Club \u2014 Wine & Beer',361:'Vessel \u2014 Wine & Beer',416:'Restaurant Brewer',
        15:'Farm Brewer',14:'Micro-Brewery',25:'Farm Cidery',31:'Winery',
        52:'Micro-Distillery',56:'Farm Distillery'}

def load(fn,key):
    g=json.load(open(U+fn)); geoms=[];vals=[]
    for f in g['features']:
        geoms.append(shape(f['geometry']).buffer(0)); vals.append(f['properties'][key])
    return geoms,vals,STRtree(geoms)

cd_g,cd_v,cd_t=load('Community_Districts_20260826.geojson','boro_cd')
cc_g,cc_v,cc_t=load('City_Council_Districts_20260826.geojson','coundist')

def hit(tree,geoms,vals,pt):
    for i in tree.query(pt):
        if geoms[i].contains(pt): return vals[i]
    return None

def norm(v):
    return ' '.join(str(v or '').split()).strip()

recs=[]; nogeo=0; noclass=0
for path,status in [('Current_Liquor_Authority_Active_Licenses_20260828_2.geojson','Active'),
                    ('Current_SLA_Pending_Licenses_20260828.geojson','Pending')]:
    d=json.load(open(U+path))
    for f in d['features']:
        p=f['properties']
        try: cls=int(p.get('class'))
        except (TypeError,ValueError): continue
        if cls not in BEV: noclass+=1; continue
        g=f.get('geometry')
        if not g or g.get('type')!='Point': nogeo+=1; continue
        lon,lat=g['coordinates'][:2]
        pt=Point(lon,lat)
        cd=hit(cd_t,cd_g,cd_v,pt)
        if not cd: continue          # outside the five boroughs
        cc=hit(cc_t,cc_g,cc_v,pt)
        addr=norm(p.get('actualaddressofpremises') or p.get('actual_address_of_premises'))
        r={'i':norm(p.get('licensepermitid') or p.get('application_id')),
           'l':norm(p.get('legalname')),'d':norm(p.get('dba')),
           'a':addr,'z':norm(p.get('zipcode') or p.get('zip_code'))[:5],
           's':status,'b':BEV[cls],'t':DETAIL[cls],'c':cls,
           'cd':str(cd),'y':round(lat,5),'x':round(lon,5)}
        if cc: r['cc']=int(cc)
        recs.append(r)

print('records:',len(recs),'| skipped no geometry:',nogeo,'| off-premises or other class:',noclass)
print('by status:',collections.Counter(r['s'] for r in recs))
print('by bev:',collections.Counter(r['b'] for r in recs))
print('with council:',sum(1 for r in recs if 'cc' in r))

BORO={'1':'Manhattan','2':'Bronx','3':'Brooklyn','4':'Queens','5':'Staten Island'}
os.makedirs(R+'data/liquor',exist_ok=True)
by=collections.defaultdict(list)
for r in recs: by[r['cd'][0]].append(r)
idx={}
for code,rows in sorted(by.items()):
    slug=BORO[code].lower().replace(' ','-')
    json.dump({'borough':BORO[code],'count':len(rows),'recs':rows},
              open(R+'data/liquor/'+slug+'.json','w'),separators=(',',':'))
    kb=os.path.getsize(R+'data/liquor/'+slug+'.json')//1024
    idx[BORO[code]]={'file':slug+'.json','count':len(rows),'kb':kb}
    print(f'  {BORO[code]:14} {len(rows):6}  {kb} KB')

json.dump({'source':'NYS Liquor Authority active and pending on-premises licences via NYC/NY Open Data, pulled 28 August 2026',
           'fetched':'2026-08-28','total':len(recs),'boroughs':idx,
           'byCd':dict(sorted(collections.Counter(r['cd'] for r in recs).items())),
           'byCouncil':{str(k):v for k,v in sorted(collections.Counter(r['cc'] for r in recs if 'cc' in r).items())},
           'byBev':dict(collections.Counter(r['b'] for r in recs)),
           'byStatus':dict(collections.Counter(r['s'] for r in recs))},
          open(R+'data/liquor/index.json','w'),separators=(',',':'))
print('CB6:',sum(1 for r in recs if r['cd']=='306'))
