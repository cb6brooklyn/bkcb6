"""Replace the generic "public parkland" line on the property types where it is
wrong. A parkway is a road. A mall is a planted median. A cemetery is a
cemetery. Telling a reader those are public parkland is false."""
import json, re, glob

R='/home/claude/repo/'
src=json.load(open(R+'Parks_Properties_20260414.geojson'))
P={f['properties']['gispropnum']: f['properties'] for f in src['features']}

TEXT={
 'Parkway': ('A parkway. This is a road corridor, and the Parks Department holds '
             'the right of way along with the planted land beside it, so the acreage '
             'covers the whole corridor rather than a park you walk into. Some '
             'stretches carry a greenway or a waterfront promenade; others are '
             'roadway and its verges.'),
 'Mall': ('A mall. These are the planted strips running down the middle of a street, '
          'like the ones on Broadway, Park Avenue and Ocean Parkway. They are '
          'mapped as parkland and maintained by the Parks Department, but they sit '
          'between lanes of traffic.'),
 'Waterfront Facility': ('A waterfront facility. Parks Department property on the '
          'shoreline, which can mean a pier, a dock, a marina or a bulkhead rather '
          'than open parkland.'),
 'Buildings/Institutions': ('A building or institution on Parks Department property. '
          'The land is mapped as parkland but the site is a structure rather than '
          'open space.'),
 'Managed Sites': ('A managed site. Parks Department land held for a specific '
          'operational purpose rather than general public recreation.'),
 'Cemetery': ('A cemetery on Parks Department property. It is mapped as parkland '
          'but it is a burial ground, not a park.'),
 'Lot': ('A lot held by the Parks Department. Mapped as parkland, but a parcel of '
         'land rather than a park in use.'),
 'Operations': ('An operations site. Parks Department property used for maintenance '
          'and vehicles rather than public recreation.'),
 'Retired N/A': ('A property the Parks Department records as retired. Its current '
          'status is not described in the data.'),
}

GEN='Public parkland held by the New York City Department of Parks and Recreation.'
n=0; by={}
for f in sorted(glob.glob(R+'park/*.html')):
    s=open(f,encoding='utf-8').read()
    gm=re.search(r'Parks ID</span><span class="v">([^<]*)</span>', s)
    if not gm: continue
    t=(P.get(gm.group(1).strip()) or {}).get('typecategory')
    new=TEXT.get(t)
    if not new: continue
    m=re.search(r'(<h2>What it is</h2><div class="bio"><p>)('+re.escape(GEN)+r')(</p>)', s)
    if not m: continue
    s=s[:m.start()]+m.group(1)+new+m.group(3)+s[m.end():]
    open(f,'w',encoding='utf-8').write(s)
    n+=1; by[t]=by.get(t,0)+1
print('descriptions corrected on', n, 'pages')
for k,v in sorted(by.items(), key=lambda kv:-kv[1]): print(f'   {v:4}  {k}')
