import json,pickle,numpy as np,os
from scipy.spatial import cKDTree
exec(open('/tmp/city.py').read().split("# own-street target")[0])
P,kept,BO,tslug,tcd,before,ok=pickle.load(open('/tmp/city3.pkl','rb'))
D='app/data/civic/blocks/'
Q=np.column_stack([P[:,1]*KX,P[:,0]]);cs=np.array(cslug)
zz=json.load(open(D+'zz-geo.json'));zq=np.array([[r[3]*KX,r[2]] for r in zz]);zs=np.array([r[0] for r in zz])
m=BO=='bk';kb=kept&m
def acc(extra_pts,extra_sl):
    pts=np.vstack([cmid,zq,Q[kb]]+extra_pts);sl=np.concatenate([cs,zs,tslug[kb]]+extra_sl)
    d,i=cKDTree(pts).query(Q[m],k=1);return sl[i]==tslug[m]
idx=np.nonzero(m)[0];a=acc([],[]);print('BKCB6 zz+zb Brooklyn correct',a.sum(),'of',m.sum(),'wrong',(~a).sum())
fix=np.zeros(len(P),bool)
for it in range(6):
    fix[idx[~a]]=True
    a=acc([Q[fix]],[tslug[fix]]);print(' fixups',fix.sum(),'wrong left',(~a).sum())
zw=[[str(tslug[i]),int(tcd[i]),float(P[i,0]),float(P[i,1]),float(P[i,0]),float(P[i,1]),'','',''] for i in np.nonzero(fix)[0]]
json.dump(zw,open(D+'zw-geo.json','w'),separators=(',',':'));print('zw',len(zw),os.path.getsize(D+'zw-geo.json'),round(100*a.mean(),2))
