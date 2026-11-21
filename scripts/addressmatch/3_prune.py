import json,pickle,numpy as np,collections,sys
from scipy.spatial import cKDTree
exec(open('/tmp/city.py').read().split("# own-street target")[0])
out,stats=pickle.load(open('/tmp/city.pkl','rb'))
P=[];T=[];BO=[]
for b in B:
    p,t=out[b];P+=p;T+=t;BO+=[b]*len(p)
P=np.array(P);N=len(P);BO=np.array(BO)
tslug=np.array([t[0] for t in T]);tcd=np.array([t[1] for t in T])
Q=np.column_stack([P[:,1]*KX,P[:,0]])
cslug_a=np.array(cslug)
kept=np.zeros(N,bool)
def evaluate():
    pts=np.vstack([cmid,Q[kept]]);sl=np.concatenate([cslug_a,tslug[kept]])
    d,i=cKDTree(pts).query(Q,k=1)
    return sl[i]==tslug
ok=evaluate();before=ok.copy()
CELL=float(sys.argv[1]) if len(sys.argv)>1 else 25.0
cx=np.floor(P[:,1]*84400/CELL).astype(np.int64);cy=np.floor(P[:,0]*111320/CELL).astype(np.int64)
for it in range(40):
    wrong=np.nonzero(~ok)[0]
    if not len(wrong): break
    cell=CELL if it<25 else 0
    if cell:
        seen=set();pick=[]
        for i in wrong:
            k=(tslug[i],cx[i],cy[i])
            if k in seen: continue
            seen.add(k);pick.append(i)
        kept[pick]=True
    else: kept[wrong]=True
    prev=kept.sum()
    ok=evaluate()
    if it%3==0 or not (~ok).any(): print('iter',it,'kept',kept.sum(),'correct',round(100*ok.mean(),3),flush=True)
print('final kept',kept.sum(),'correct',ok.sum(),'of',N)
for b in B:
    m=BO==b;print(b,'addresses',m.sum(),'before',round(100*before[m].mean(),1),'after',round(100*ok[m].mean(),2),'rows',kept[m].sum())
pickle.dump((P,kept,BO,tslug,tcd,before,ok),open('/tmp/city3.pkl','wb'))
