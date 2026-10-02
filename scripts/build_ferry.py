import csv, json, collections
D='/tmp/ferry/'
def rd(f): return list(csv.DictReader(open(D+f, encoding='utf-8-sig')))
routes={r['route_id']:r for r in rd('routes.txt')}
trips=rd('trips.txt'); stops={s['stop_id']:s for s in rd('stops.txt')}
shapes=collections.defaultdict(list)
for p in rd('shapes.txt'): shapes[p['shape_id']].append((int(p['shape_pt_sequence']), round(float(p['shape_pt_lat']),5), round(float(p['shape_pt_lon']),5)))
route_shapes=collections.defaultdict(set)
trip_route={}
for t in trips: route_shapes[t['route_id']].add(t['shape_id']); trip_route[t['trip_id']]=t['route_id']
stop_routes=collections.defaultdict(set)
for st in rd('stop_times.txt'): stop_routes[st['stop_id']].add(trip_route.get(st['trip_id'],''))
out={'source':'NYC Ferry GTFS feed (nycferry.connexionz.net), fetched 2026-10-02','routes':[],'stops':[]}
for rid,r in routes.items():
    lines=[]
    for sid in sorted(route_shapes[rid]):
        pts=[[la,lo] for _,la,lo in sorted(shapes[sid])]
        if pts: lines.append(pts)
    out['routes'].append({'id':rid,'name':r['route_long_name'],'color':'#'+r['route_color'],'lines':lines,'kind':'ferry' if r['route_type']=='4' else 'shuttle bus'})
seen=set()
for sid,s in stops.items():
    key=(s['stop_name'],round(float(s['stop_lat']),4),round(float(s['stop_lon']),4))
    if key in seen: continue
    seen.add(key)
    rs=sorted(x for x in stop_routes[sid] if x)
    if not any(routes[x]['route_type']=='4' for x in rs): continue
    out['stops'].append({'name':s['stop_name'],'lat':float(s['stop_lat']),'lng':float(s['stop_lon']),'routes':rs,'ada':s.get('wheelchair_boarding','')=='1'})
json.dump(out,open('/tmp/ferry/ferry.json','w'),separators=(',',':'))
print('routes',len(out['routes']),'stops',len(out['stops']),'shape points',sum(len(l) for r in out['routes'] for l in r['lines']))
print([ (r['id'],len(r['lines'])) for r in out['routes']]); print([s['name'] for s in out['stops']])
