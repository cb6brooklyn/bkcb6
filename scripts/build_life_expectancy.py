import openpyxl, json, os
R='/home/claude/repo/'
wb=openpyxl.load_workbook('/home/claude/chp.xlsx', read_only=True, data_only=True)
ws=wb['CHP_all_data']
rows=list(ws.iter_rows(values_only=True))
hdr=[str(c) if c is not None else '' for c in rows[1]]
li=hdr.index('Life_Expectancy')

cd={}; boro={}; city=None; names={}
for r in rows[2:]:
    if r[0] is None or not isinstance(r[li],(int,float)): continue
    i=int(r[0]); v=round(float(r[li]),1)
    if i==0: city=v
    elif i<10: boro[str(r[2]).strip()]=v
    else:
        cd[str(i)]=v; names[str(i)]=str(r[2]).strip()

vals=sorted(cd.values(), reverse=True)
rank={k:vals.index(v)+1 for k,v in cd.items()}

out={'source':'NYC Department of Health and Mental Hygiene, 2026 Community Health Profiles public use dataset',
     'url':'https://www.nyc.gov/site/doh/data/data-publications/profiles.page',
     'measure':'Life expectancy at birth, in years',
     'years':'2013-2022 for community districts and boroughs, 2022 for the city',
     'city':city,'boroughs':boro,'cd':cd,'names':names,'rank':rank,
     'best':max(cd,key=cd.get),'worst':min(cd,key=cd.get)}
json.dump(out,open(R+'data/health/life-expectancy.json','w'),separators=(',',':'))
print('districts:',len(cd),'| boroughs:',len(boro),'| city:',city)
print('bytes:',os.path.getsize(R+'data/health/life-expectancy.json'))
print('highest:',names[out['best']],cd[out['best']],'| lowest:',names[out['worst']],cd[out['worst']])
print('spread: %.1f years' % (cd[out['best']]-cd[out['worst']]))
print('CB6:',cd['306'],'rank',rank['306'])
