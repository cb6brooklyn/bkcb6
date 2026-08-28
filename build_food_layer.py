import json, os
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

U='/mnt/user-data/uploads/'
R='/home/claude/repo/'
src=json.load(open(R+'data/food-places.json'))

def load(fn,key):
    g=json.load(open(U+fn)); geoms=[];vals=[]
    for f in g['features']:
        geoms.append(shape(f['geometry']).buffer(0)); vals.append(f['properties'][key])
    return geoms,vals,STRtree(geoms)

cc_g,cc_v,cc_t=load('City_Council_Districts_20260826.geojson','coundist')
ad_g,ad_v,ad_t=load('State_Assembly_Districts_20260827.geojson','assembly_district')
sd_g,sd_v,sd_t=load('State_Senate_Districts_20260827.geojson','st_sen_dist')

def hit(tree,geoms,vals,lon,lat):
    p=Point(lon,lat)
    for i in tree.query(p):
        if geoms[i].contains(p): return vals[i]
    return None

BORO={'MN':'Manhattan','BX':'Bronx','BK':'Brooklyn','QN':'Queens','SI':'Staten Island'}
recs=[]; miss=0
for e in src:
    if not e.get('lat') or not e.get('lng'): miss+=1; continue
    r={'n':e['name'],'a':e.get('address',''),
       'cd':e['cd'],'y':round(e['lat'],5),'x':round(e['lng'],5),
       'ft':0 if e['type']=='supermarket' else 1,
       'st':e.get('subtype','')}
    if e.get('chain'): r['ch']=e['chain']
    if e.get('sqft'): r['sq']=e['sqft']
    if e.get('hours'): r['h']=(e.get('days','')+' '+e['hours']).strip()
    if e.get('ebt'): r['ebt']=1
    if e.get('approx'): r['ap']=1
    cc=hit(cc_t,cc_g,cc_v,e['lng'],e['lat'])
    ad=hit(ad_t,ad_g,ad_v,e['lng'],e['lat'])
    sd=hit(sd_t,sd_g,sd_v,e['lng'],e['lat'])
    if cc: r['cc']=int(cc)
    if ad: r['ad']=int(ad)
    if sd: r['sd']=int(sd)
    recs.append(r)

print('records:',len(recs),'| dropped without coords:',miss)
print('with council:',sum(1 for r in recs if 'cc' in r),
      '| assembly:',sum(1 for r in recs if 'ad' in r),
      '| senate:',sum(1 for r in recs if 'sd' in r))
out={'source':'NYS Department of Agriculture and Markets retail food store licenses, and NYC greenmarkets, as compiled for the bkcb6.app food map',
     'count':len(recs),'biz':recs}
p=R+'data/certified/food.json'
json.dump(out,open(p,'w'),separators=(',',':'))
print('bytes:',os.path.getsize(p))
import collections
print('CB6 stores:',sum(1 for r in recs if r['cd']=='306'))
