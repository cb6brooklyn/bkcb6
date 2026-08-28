import json, os, collections
C='/home/claude/ehdp/'
R='/home/claude/repo/'
meta=json.load(open('/home/claude/ehdp_meta.json'))
tp={t['TimePeriodID']:t for t in json.load(open(C+'metadata_TimePeriods.json'))} \
   if os.path.exists(C+'metadata_TimePeriods.json') else None
if tp is None:
    import urllib.request
    UA={'User-Agent':'Mozilla/5.0'}
    tpl=json.loads(urllib.request.urlopen(urllib.request.Request(
      'https://raw.githubusercontent.com/nychealth/EHDP-data/production/indicators/metadata/TimePeriods.json',
      headers=UA),timeout=60).read().decode())
    json.dump(tpl,open(C+'metadata_TimePeriods.json','w'))
    tp={t['TimePeriodID']:t for t in tpl}

topics=json.load(open('/home/claude/ehdp_topics.json')) if os.path.exists('/home/claude/ehdp_topics.json') else None
if topics is None:
    import urllib.request
    topics=json.loads(urllib.request.urlopen(urllib.request.Request(
      'https://a816-dohbesp.nyc.gov/IndicatorPublic/IndicatorMetadata/topic_indicators.json',
      headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read().decode())
    json.dump(topics,open('/home/claude/ehdp_topics.json','w'))

ind2topic={}
for slug,t in topics.items():
    for iid in t['IndicatorID']:
        ind2topic.setdefault(iid, t['topic_name'])

# measures that carry community district data
measures={}
for ind in meta:
    for me in ind.get('Measures') or []:
        if 'CD' not in (me.get('AvailableGeoTypes') or []): continue
        measures[me['MeasureID']]={
            'id':me['MeasureID'],'ind':ind['IndicatorID'],
            'name':me['MeasureName'],'type':me.get('MeasurementType') or '',
            'indName':ind['IndicatorName'],'indLabel':ind.get('IndicatorLabel') or ind['IndicatorName'],
            'desc':(ind.get('IndicatorDescription') or '').strip(),
            'how':(me.get('how_calculated') or '').strip(),
            'src':(me.get('Sources') or '').strip(),
            'topic':ind2topic.get(ind['IndicatorID'],'Other')}

byCd=collections.defaultdict(lambda: collections.defaultdict(list))
seen=set()
for iid in sorted({m['ind'] for m in measures.values()}):
    p=C+'data_%d.json'%iid
    if not os.path.exists(p): continue
    d=json.load(open(p))
    n=len(d['MeasureID'])
    for i in range(n):
        if d['GeoType'][i]!='CD': continue
        mid=d['MeasureID'][i]
        if mid not in measures: continue
        v=d['Value'][i]
        if v is None or v=='': continue
        cd=str(d['GeoID'][i])
        t=tp.get(d['TimePeriodID'][i])
        byCd[cd][mid].append([t['TimePeriod'] if t else str(d['TimePeriodID'][i]), v])
        seen.add(mid)

for cd in byCd:
    for mid in byCd[cd]:
        byCd[cd][mid].sort(key=lambda r: r[0])

measures={k:v for k,v in measures.items() if k in seen}
print('measures with CD values:',len(measures),'| districts:',len(byCd))

os.makedirs(R+'data/health/cd',exist_ok=True)
tot=0
for cd,rows in sorted(byCd.items()):
    p=R+'data/health/cd/%s.json'%cd
    json.dump({'cd':cd,'m':{str(k):v for k,v in rows.items()}},open(p,'w'),separators=(',',':'))
    tot+=os.path.getsize(p)
print('per district files:',len(byCd),'| avg KB:',tot//len(byCd)//1024,'| total KB:',tot//1024)

# latest value per measure per district, for ranking and the choropleth
latest={}
for cd,rows in byCd.items():
    for mid,series in rows.items():
        latest.setdefault(str(mid),{})[cd]=series[-1][1]
periods={}
for cd,rows in byCd.items():
    for mid,series in rows.items():
        periods.setdefault(str(mid),series[-1][0])

topics_out=collections.defaultdict(list)
for m in measures.values(): topics_out[m['topic']].append(m['id'])

json.dump({'source':'NYC Department of Health and Mental Hygiene, Environment and Health Data Portal',
           'portal':'https://a816-dohbesp.nyc.gov/IndicatorPublic/',
           'fetched':'2026-08-28',
           'measures':{str(k):v for k,v in sorted(measures.items())},
           'topics':{k:sorted(v) for k,v in sorted(topics_out.items())},
           'latest':latest,'latestPeriod':periods},
          open(R+'data/health/index.json','w'),separators=(',',':'))
print('index KB:',os.path.getsize(R+'data/health/index.json')//1024)
print('topics:',len(topics_out))
