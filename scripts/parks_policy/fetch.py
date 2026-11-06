import json,urllib.request,urllib.parse,ssl,time,sys,os
ctx=ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def q(ds,**p):
    u='https://data.cityofnewyork.us/resource/%s.json?'%ds+urllib.parse.urlencode({('$'+k):v for k,v in p.items()})
    for a in range(5):
        try: return json.loads(urllib.request.urlopen(u,timeout=300,context=ctx).read())
        except Exception as e: print('retry',ds,e,file=sys.stderr); time.sleep(10*(a+1))
    raise SystemExit('fail '+ds)
def allrows(ds,**p):
    out=[];off=0
    while True:
        r=q(ds,limit=50000,offset=off,order=':id',**p); out+=r
        if len(r)<50000: return out
        off+=50000
def save(n,d): json.dump(d,open('raw/'+n+'.json','w')); print(n,len(d) if isinstance(d,list) else '')
os.makedirs('raw',exist_ok=True)
jobs={
 'props':lambda: allrows('enfh-gkve'),
 'pip':lambda: allrows('yg3y-7juh',where="date>='2025-09-01'"),
 'pipstat':lambda: q('yg3y-7juh',select='prop_id,max(date) as last',group='prop_id',limit=50000),
 'restrooms':lambda: allrows('9byw-znpj'),
 'rrinsp':lambda: allrows('mp8v-wjtf'),
 'cap':lambda: allrows('4hcv-tc5r'),
 'fountains':lambda: allrows('qnv7-p7a2'),
 'spray':lambda: allrows('ckaz-6gaa'),
 'dogs':lambda: allrows('hxx3-bwgv'),
 'athletic':lambda: allrows('qnem-b8re'),
 'pools':lambda: allrows('y5rm-wagw'),
 'skate':lambda: allrows('8knb-zsb6'),
 'gardens':lambda: allrows('p78i-pat6'),
 'events':lambda: allrows('w3wp-dpdi'),
 'wild':lambda: allrows('48va-85tp'),
 'dca':lambda: allrows('j55h-3upk'),
 'monuments':lambda: allrows('6rrm-vxj9'),
 'groups':lambda: allrows('cjw9-h5zw'),
 'trails':lambda: q('vjbm-hsyr',select='parkid,count(*) as n',group='parkid',limit=50000),
 'planting':lambda: q('82zj-84is',select='communityboard,pssite,psstatus,count(*) as n',group='communityboard,pssite,psstatus',limit=50000),
 'fsr':lambda: q('mu46-p9is',select='communityboard,srcategory,count(*) as n',where="createddate>='2025-11-01' and createddate<'2026-11-01'",group='communityboard,srcategory',limit=50000),
 'fsr306':lambda: allrows('mu46-p9is',where="createddate>='2025-11-01' and createddate<'2026-11-01' and communityboard='306.0'"),
 'c311':lambda: q('erm2-nwe9',select='community_board,complaint_type,count(*) as n',where="agency='DPR' and created_date>='2025-11-01' and created_date<'2026-11-01'",group='community_board,complaint_type',limit=50000),
 'c311_306':lambda: allrows('erm2-nwe9',select='unique_key,created_date,complaint_type,descriptor,incident_address,park_facility_name,status,latitude,longitude,resolution_description',where="agency='DPR' and created_date>='2025-11-01' and created_date<'2026-11-01' and community_board='06 BROOKLYN'"),
}
for n in (sys.argv[1:] or jobs):
    if n not in jobs or os.path.exists('raw/'+n+'.json'): continue
    save(n,jobs[n]())
B=(40.6567,-74.0215,40.6948,-73.9696)
jobs2={'trees306':lambda: allrows('hn5i-inap',select='objectid,dbh,tpstructure,tpcondition,genusspecies,location,plantingspaceglobalid',where="within_box(location,%s,%s,%s,%s) and tpstructure='Full'"%(B[2],B[1],B[0],B[3])),
 'ps306':lambda: allrows('82zj-84is',select='globalid,pssite,psstatus,location,communityboard',where="communityboard='306.0'")}
for n in sys.argv[1:]:
    if n in jobs2 and not os.path.exists('raw/'+n+'.json'): save(n,jobs2[n]())
