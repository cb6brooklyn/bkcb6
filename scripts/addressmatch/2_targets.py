import json,gzip,math,re,os,collections,sys
import numpy as np
from scipy.spatial import cKDTree
B=['mn','bx','bk','qn','si']
D='app/data/civic/blocks/'
geo={b:json.load(open((D if b=='bk' else 'assets/blocks/')+f'{b}-geo.json')) for b in B}
ABB={"st":"street","ave":"avenue","av":"avenue","rd":"road","blvd":"boulevard","pl":"place","dr":"drive","ct":"court","ln":"lane","pkwy":"parkway","hwy":"highway","ter":"terrace","sq":"square","e":"east","w":"west","n":"north","s":"south"}
def norm(s):
    out=[]
    for w in s.lower().replace('.',' ').replace(',',' ').split():
        mm=re.fullmatch(r'(\d+)(st|nd|rd|th)',w); w=mm.group(1) if mm else w
        out.append(ABB.get(w,w))
    return ' '.join(out)
KX=0.76
# candidate rows the app considers, in the app's order (mn,bx,bk,qn,si)
cand=[];
for b in B:
    for r in geo[b]:
        if r[1]%100>18: continue
        cand.append(r)
cmid=np.array([[(r[3]+r[5])/2*KX,(r[2]+r[4])/2] for r in cand])
cslug=[r[0] for r in cand]
# own-street target for each address
MX=84400.0;MY=111320.0
out={}
stats={}
for b in B:
    A=json.load(gzip.open(D+f'addr-{b}.json.gz'))
    bys=collections.defaultdict(list)
    for r in geo[b]:
        if r[1]%100>18: continue
        bys[norm(r[6])].append(r)
    P=[];T=[]
    for st,flat in A.items():
        rs=bys.get(norm(st))
        if not rs: continue
        a=np.array([[r[3]*MX,r[2]*MY] for r in rs]);c=np.array([[r[5]*MX,r[4]*MY] for r in rs])
        d=c-a;l2=(d**2).sum(1);l2[l2==0]=1e-9
        pts=np.array([[flat[i+2]/1e5*MX,flat[i+1]/1e5*MY] for i in range(0,len(flat),3)])
        for s in range(0,len(pts),2000):
            p=pts[s:s+2000]
            t=np.clip(((p[:,None,:]-a[None])*d[None]).sum(2)/l2[None],0,1)
            q=a[None]+t[...,None]*d[None]
            dist=np.hypot(*(p[:,None,:]-q).transpose(2,0,1))
            j=dist.argmin(1);ok=dist[np.arange(len(p)),j]<=60
            for k in np.nonzero(ok)[0]:
                i=(s+k)*3
                P.append((flat[i+1]/1e5,flat[i+2]/1e5));T.append(rs[j[k]])
    out[b]=(P,T);stats[b]=[sum(len(v) for v in A.values())//3,len(P)]
    print(b,'addresses',stats[b][0],'with an own-street block within 60 m',len(P),flush=True)
import pickle;pickle.dump((out,stats),open('/tmp/city.pkl','wb'))
