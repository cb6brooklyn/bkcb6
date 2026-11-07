import pymupdf, json, re, glob, warnings
warnings.filterwarnings('ignore')
L=[('land','Total District Land'),('parkland','City, State, & Federal Parkland'),('pctParkland','Percent Parkland'),('cityParks','City Parks in District (acres)'),('pctCityParks','Percent City Parks in District'),
('per1k','City Parks in District per 1,000 residents'),('walk','Residents within a 5 minute walk'),('per1kKids','City Parks in District per 1,000 children'),('per1kSeniors','City Parks in District per 1,000 seniors'),
('gardens','Community Gardens'),('reccenters','Recreation Centers'),('playgrounds','Playgrounds'),('pools','Swimming Pools'),('dogruns','Dog Runs'),('spray','Sprayshowers'),('schools','Public Schools'),
('condition','Parks “Acceptable” for Condition'),('clean','Parks “Acceptable” for Cleanliness'),('c311','Park-Related 311 calls'),('volunteer','Park Volunteer Groups')]
R=[('pop','Resident Population'),('under18','Residents under 18'),('over65','Residents over 65'),('income','Average Median Household Income'),('poverty','Population in Poverty'),
('aian','Race: American Indian'),('asian','Race: Asian'),('black','Race: Black'),('multi','Race: Multiracial'),('nhpi','Race: Native Hawaiian'),('other','Race: Other'),('white','Race: White'),('hispanic','Ethnicity: Hispanic'),
('asthma','Child Asthma Incidences'),('childObesity','Child Obesity Rate'),('life','Life Expectancy'),('adultObesity','Adult Obesity Rate'),('diabetes','Adult Diabetes Rate'),('hospitals','Hospitals and Clinics'),('air','Air Pollution'),('canopy','Tree Canopy Cover')]
def num(t):
    t=t.replace(',','').replace('$','')
    m=1
    if t.endswith('K'): m=1e3;t=t[:-1]
    if t.endswith('M'): m=1e6;t=t[:-1]
    if t.endswith('%'): t=t[:-1]
    try: return float(t)*m
    except: return None
def parse(f):
    p=pymupdf.open(f)[1]; W=[(x0,y0,x1,y1,w) for x0,y0,x1,y1,w,*_ in p.get_text('words')]
    # label lines
    def lines(xmin,xmax):
        g={}
        for x0,y0,x1,y1,w in W:
            if xmin<=x0<xmax and y1>140 and y1<520: g.setdefault(round(y1),[]).append((x0,w))
        return {y:' '.join(w for x,w in sorted(v)) for y,v in g.items()}
    out={}
    for side,(lx,cx,nx,ex),labs in (('L',(25,190,225,262),L),('R',(355,512,553,610),R)):
        ll=lines(lx,cx-5)
        for key,lab in labs:
            ys=[y for y,t in ll.items() if t.startswith(lab)]
            if not ys: out[key]=None; continue
            y=ys[0]
            vals=[(x0,w) for x0,y0,x1,y1,w in W if cx-8<=x0<ex and abs(y1-y)<=9]
            cd=[w for x,w in vals if x<nx-2]; ny=[w for x,w in vals if x>=nx-2]
            # nearest by y
            def pick(lst,xa,xb):
                c=[(abs(y1-y),w) for x0,y0,x1,y1,w in W if xa<=x0<xb and abs(y1-y)<=9 and num(w) is not None]
                return min(c)[1] if c else None
            out[key]=[pick(None,cx-8,nx-6),pick(None,nx-6,ex)]
    big=[(y1,w) for x0,y0,x1,y1,w in W if 255<x0<335 and re.fullmatch(r'\d+',w) and y1-y0>15]
    outs=[y1 for x0,y0,x1,y1,w in W if w=='Out' and 255<x0<335]
    ranks=[w for y,w in sorted(big) if any(0<o-y<14 for o in outs)]
    out['ranks']=ranks
    return out
res={}
for f in sorted(glob.glob('[A-Z][A-Z]*.pdf')):
    k=f[:-4]; res[k]=parse(f)
json.dump(res,open('raw.json','w'),indent=0)
bad={k:[a for a,v in r.items() if v is None or (isinstance(v,list) and (v[0] is None))] for k,r in res.items()}
print({k:v for k,v in bad.items() if v})
print(res['BK6'])
