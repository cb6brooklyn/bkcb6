"""Assign every park property to its real districts by geometry.

Nothing is parsed from the agency's own district fields. Those are unusable:
councildistrict is comma delimited ("32, 42, 44"), nys_assembly is run together
with no delimiter ("234145465960"), us_congress is run together AND ambiguous
("8910" could be 8/9/10 or 89/10), precinct lists one value for a 20 mile
parkway, and zipcode is truncated at exactly 50 characters on 3 records.
"""
import json, collections, os
from shapely.geometry import shape
from shapely.strtree import STRtree

R='/home/claude/repo/'; U='/mnt/user-data/uploads/'

LAYERS=[
 ('cd',   U+'Community_Districts_20260826.geojson',      'boro_cd'),
 ('cc',   U+'City_Council_Districts_20260826.geojson',   'coundist'),
 ('ad',   U+'State_Assembly_Districts_20260827.geojson', 'assembly_district'),
 ('sd',   U+'State_Senate_Districts_20260827.geojson',   'st_sen_dist'),
 ('cong', R+'data/congressional-districts.geojson',      'cong_dist'),
 ('pct',  R+'data/police-precincts-citywide.geojson',    'precinct'),
]

idx={}
for tag,path,key in LAYERS:
    d=json.load(open(path))
    gs=[shape(f['geometry']).buffer(0) for f in d['features']]
    vs=[str(f['properties'][key]) for f in d['features']]
    idx[tag]=(gs,vs,STRtree(gs))
    print(f'  loaded {tag}: {len(gs)} polygons', flush=True)

src=json.load(open(R+'Parks_Properties_20260414.geojson'))
print('park properties:', len(src['features']), flush=True)

# A corridor is thin everywhere by design, so requiring it to be "mostly" in a
# district is incoherent. The department's own typecategory identifies them.
CORRIDOR={'Parkway','Mall','Strip'}
SHARE, ACRES = 0.10, 5.0

out={}
for n,f in enumerate(src['features']):
    p=f['properties']
    gid=p.get('gispropnum')
    if not gid: continue
    try: g=shape(f['geometry']).buffer(0)
    except Exception: continue
    if g.is_empty or not g.area: continue
    try: acres=float(p.get('acres') or 0)
    except ValueError: acres=0.0
    corridor = (p.get('typecategory') in CORRIDOR)

    rec={}
    for tag,(gs,vs,tree) in idx.items():
        area=collections.defaultdict(float)
        for i in tree.query(g):
            inter=gs[i].intersection(g)
            if not inter.is_empty and inter.area>0:
                area[vs[i]]+=inter.area
        if not area:
            pt=g.representative_point()
            for i in tree.query(pt):
                if gs[i].contains(pt): area[vs[i]]=1.0; break
        if not area:
            # A pier sits outside every land polygon. Attach it to the shore it
            # touches. Verified on R044: nearest is 1 ft away and agrees with the
            # agency on all six layers.
            near=None; nd=None
            for i,gg in enumerate(gs):
                dist=g.distance(gg)
                if nd is None or dist<nd: nd=dist; near=vs[i]
            if near is not None: area[near]=1.0
        if not area: continue
        tot=sum(area.values())
        ranked=sorted(area.items(), key=lambda kv:-kv[1])
        if corridor:
            # Percentage is meaningless for a corridor: it is thin everywhere by
            # design. Use an absolute floor only. 0.25 acres is about 10,000 sq
            # ft, far above boundary survey noise and well below a real segment.
            keep=[k for k,a in ranked if (acres*a/tot)>=0.25]
        else:
            keep=[k for k,a in ranked if (a/tot)>=SHARE or (acres*a/tot)>=ACRES]
        rec[tag]=keep or [ranked[0][0]]
    rec['corridor']=corridor
    rec['acres']=acres
    out[gid]=rec
    if n%400==0: print(f'   {n}/{len(src["features"])}', flush=True)

json.dump(out, open('/home/claude/park_all_districts.json','w'))
print('assigned:', len(out))
for gid in ('B166','Q096','B385','M094'):
    if gid in out:
        r=out[gid]
        print(f"  {gid} corridor={r['corridor']} cd={r.get('cd')} cc={r.get('cc')} ad={r.get('ad')} sd={r.get('sd')} cong={r.get('cong')} pct={r.get('pct')}")
