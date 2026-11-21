import json,gzip,math,glob,os,re
geo=json.load(open('app/data/civic/blocks/bk-geo.json'))
sides=json.load(open('app/data/civic/blocks/sides.json'))
KX=0.76
def m(lo,la): return (lo*84400.0, la*111320.0)
cb6=[r for r in geo if r[1]==306]
# neighbours: blocks with an endpoint within 400 m of a CB6 block endpoint (grid hash)
cell={}
for r in cb6:
    for la,lo in ((r[2],r[3]),(r[4],r[5])):
        x,y=m(lo,la);cell.setdefault((int(x//400),int(y//400)),[]).append((x,y))
def near(la,lo):
    x,y=m(lo,la);cx,cy=int(x//400),int(y//400)
    for i in(-1,0,1):
        for j in(-1,0,1):
            for (px,py) in cell.get((cx+i,cy+j),[]):
                if (px-x)**2+(py-y)**2<=400**2: return True
    return False
want={}
for r in geo:
    if r[1]%100>18: continue
    if r[1]==306 or near(r[2],r[3]) or near(r[4],r[5]): want[r[0]]=r
cds=sorted(set(r[1] for r in want.values()));print('blocks',len(want),'cds',cds)
lines={}
for cd in cds:
    j=json.load(open(f'assets/blocks/bk/{cd}.json'))['blocks']
    for s,r in want.items():
        if r[1]==cd and s in j: lines[s]=j[s].get('lines') or []
STEP=10.0
rows=[]
for s,r in want.items():
    ls=lines.get(s) or [[[r[3],r[2]],[r[5],r[4]]]]
    real = s in sides
    st,fr,to=(r[6],r[7],r[8]) if real else ('','','')
    for ln in ls:
        pts=[m(c[0],c[1]) for c in ln]
        tot=sum(math.dist(a,b) for a,b in zip(pts,pts[1:]))
        if tot<=0: continue
        n=max(1,int(round(tot/STEP)))
        targets=[(k+0.5)*tot/n for k in range(n)]
        acc=0;ti=0
        for (a,b),(ca,cb) in zip(zip(pts,pts[1:]),zip(ln,ln[1:])):
            d=math.dist(a,b)
            while ti<len(targets) and targets[ti]<=acc+d+1e-9:
                t=(targets[ti]-acc)/d if d else 0
                lo=round(ca[0]+(cb[0]-ca[0])*t,6);la=round(ca[1]+(cb[1]-ca[1])*t,6)
                rows.append([s,r[1],la,lo,la,lo,st,fr,to]);ti+=1
            acc+=d
print('rows',len(rows))
json.dump(rows,open('app/data/civic/blocks/zz-geo.json','w'),separators=(',',':'))
print(os.path.getsize('app/data/civic/blocks/zz-geo.json'))
# ---- simulate the app's rule: closest centre over all rows
def pick(la,lo,allrows):
    best=None;bd=1e99
    for r in allrows:
        if r[1]%100>18: continue
        y=(r[2]+r[4])/2-la; x=((r[3]+r[5])/2-lo)*KX; d=x*x+y*y
        if d<bd: bd=d;best=r
    return best
print('414 8th before:',pick(40.66732,-73.98091,geo)[0]);print('414 8th after :',pick(40.66732,-73.98091,geo+rows)[0])
# accuracy over every CB6-area address point: does the picked block's street equal the address's street?
A=json.load(gzip.open('app/data/civic/blocks/addr-bk.json.gz'))
slugst={r[0]:r[6] for r in geo}
ABB={"st":"street","ave":"avenue","av":"avenue","rd":"road","blvd":"boulevard","pl":"place","dr":"drive","ct":"court","ln":"lane","pkwy":"parkway","hwy":"highway","ter":"terrace","sq":"square","e":"east","w":"west","n":"north","s":"south"}
def norm(s):
    out=[]
    for w in s.lower().replace('.',' ').replace(',',' ').split():
        mm=re.fullmatch(r'(\d+)(st|nd|rd|th)',w); w=mm.group(1) if mm else w
        out.append(ABB.get(w,w))
    return ' '.join(out)
lat0=min(min(r[2],r[4]) for r in cb6);lat1=max(max(r[2],r[4]) for r in cb6);lo0=min(min(r[3],r[5]) for r in cb6);lo1=max(max(r[3],r[5]) for r in cb6)
# spatial index for speed
import collections
def index(rs):
    g=collections.defaultdict(list)
    for r in rs:
        if r[1]%100>18: continue
        g[(int(((r[3]+r[5])/2)*400),int(((r[2]+r[4])/2)*400))].append(r)
    return g
def pickg(la,lo,g):
    cx,cy=int(lo*400),int(la*400);best=None;bd=1e99
    for i in range(-2,3):
        for j in range(-2,3):
            for r in g.get((cx+i,cy+j),[]):
                y=(r[2]+r[4])/2-la; x=((r[3]+r[5])/2-lo)*KX; d=x*x+y*y
                if d<bd: bd=d;best=r
    return best
g0=index(geo);g1=index(geo+rows)
cb6slugs=set(r[0] for r in cb6)
tot=ok0=ok1=0
for st,flat in A.items():
    for i in range(0,len(flat),3):
        la,lo=flat[i+1]/1e5,flat[i+2]/1e5
        if not(lat0<=la<=lat1 and lo0<=lo<=lo1): continue
        b0=pickg(la,lo,g0);b1=pickg(la,lo,g1)
        if not b0 or not b1 or (b1[0] not in cb6slugs and b0[0] not in cb6slugs): continue
        tot+=1
        ok0+= norm(slugst[b0[0]])==norm(st); ok1+= norm(slugst[b1[0]])==norm(st)
print('addresses',tot,'own-street block before',ok0,round(100*ok0/tot,1),'after',ok1,round(100*ok1/tot,1))

# ---- address-point rows: every address in the area pinned to the nearest block of its own street
bystreet=collections.defaultdict(list)
for s,r in want.items(): bystreet[norm(r[6])].append(s)
def segd(P,ln):
    best=1e99;pts=[m(c[0],c[1]) for c in ln]
    for a,b in zip(pts,pts[1:]):
        dx=b[0]-a[0];dy=b[1]-a[1];l2=dx*dx+dy*dy;t=max(0,min(1,((P[0]-a[0])*dx+(P[1]-a[1])*dy)/l2)) if l2 else 0
        best=min(best,math.hypot(P[0]-(a[0]+t*dx),P[1]-(a[1]+t*dy)))
    return best
arows=[];seen=set();nomatch=0
for st,flat in A.items():
    cands=bystreet.get(norm(st))
    if not cands: continue
    for i in range(0,len(flat),3):
        la,lo=flat[i+1]/1e5,flat[i+2]/1e5
        if not(lat0-0.004<=la<=lat1+0.004 and lo0-0.005<=lo<=lo1+0.005): continue
        P=m(lo,la);bs=None;bd=1e99
        for s in cands:
            r=want[s]
            for ln in (lines.get(s) or [[[r[3],r[2]],[r[5],r[4]]]]):
                d=segd(P,ln)
                if d<bd: bd=d;bs=s
        if bs is None or bd>60: nomatch+=1;continue
        k=(bs,la,lo)
        if k in seen: continue
        seen.add(k);r=want[bs];real=bs in sides
        arows.append([bs,r[1],la,lo,la,lo]+([r[6],r[7],r[8]] if real else ['','','']))
print('address rows',len(arows),'unmatched',nomatch)
allz=rows+arows
json.dump(allz,open('app/data/civic/blocks/zz-geo.json','w'),separators=(',',':'))
print('file',os.path.getsize('app/data/civic/blocks/zz-geo.json'),'rows',len(allz))
g2=index(geo+allz);tot=ok2=0;bad=[]
for st,flat in A.items():
    for i in range(0,len(flat),3):
        la,lo=flat[i+1]/1e5,flat[i+2]/1e5
        if not(lat0<=la<=lat1 and lo0<=lo<=lo1): continue
        b0=pickg(la,lo,g0);b2=pickg(la,lo,g2)
        if not b0 or not b2 or (b2[0] not in cb6slugs and b0[0] not in cb6slugs): continue
        tot+=1;good=norm(slugst[b2[0]])==norm(st);ok2+=good
        if not good and len(bad)<400: bad.append((flat[i],st,b2[0]))
print('after address rows:',ok2,'of',tot,round(100*ok2/tot,2));import collections as C;print(C.Counter(x[1] for x in bad).most_common(12));print(bad[:6])
print('414 8th:',pick(40.66732,-73.98091,geo+allz)[0])
