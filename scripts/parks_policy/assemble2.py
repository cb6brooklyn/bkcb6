import json,re,sys
s=open('scope.tpl.html').read()
san=open('/root/bkcb6/sanitation-policy/index.html').read()
tok=re.search(r"const TOKEN='([^']+)'",san).group(1)
V={'brooklyn':dict(NAME='Brooklyn',INTRO="Every park in Brooklyn's 18 community districts, from the Parks Department's own records: how much park land each district has for its people, how inspectors rate the parks, playgrounds, street trees, capital projects and what people report to 311, ranked against each other, the other boroughs and the city.",GLANCESUB='Eight numbers against the city and the other boroughs',OTHERLINK='<a href="/parks-policy/nyc/">Parks in NYC</a>'),
   'nyc':dict(NAME='NYC',INTRO="Every park in New York City's 59 community districts, from the Parks Department's own records: how much park land each district has for its people, how inspectors rate the parks, playgrounds, street trees, capital projects and what people report to 311, by borough and district.",GLANCESUB='Eight numbers, borough by borough',OTHERLINK='<a href="/parks-policy/brooklyn/">Parks in Brooklyn</a>')}
for sc,v in V.items():
    t=s.replace('{{SCOPE}}',sc).replace('{{CSS}}',open('css.txt').read()).replace('{{ICO}}',json.dumps(json.load(open('ico.json')),separators=(',',':'))).replace('{{TOKEN}}',tok)
    for k,x in v.items(): t=t.replace('{{%s}}'%k,x)
    if sc=='nyc': t=t.replace('<title>Parks in NYC','<title>Parks in NYC').replace('Parks in NYC</h1>','')
    assert '{{' not in t
    import os; os.makedirs('/root/bkcb6/parks-policy/'+sc,exist_ok=True)
    open('/root/bkcb6/parks-policy/%s/index.html'%sc,'w').write(t)
    import shutil; shutil.copy('out/%s.json'%sc,'/root/bkcb6/parks-policy/%s/data.json'%sc); shutil.copy('out/%s-districts.geojson'%sc,'/root/bkcb6/parks-policy/%s/districts.geojson'%sc)
    print(sc,len(t))
