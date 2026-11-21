import json,pickle,numpy as np,os
from scipy.spatial import cKDTree
exec(open('/tmp/city.py').read().split("# own-street target")[0])
P,kept,BO,tslug,tcd,before,ok=pickle.load(open('/tmp/city3.pkl','rb'))
def rows(mask):
    return [[str(tslug[i]),int(tcd[i]),float(P[i,0]),float(P[i,1]),float(P[i,0]),float(P[i,1]),'','',''] for i in np.nonzero(mask)[0]]
zy=rows(kept);zb=rows(kept&(BO=='bk'))
D='app/data/civic/blocks/'
json.dump(zy,open(D+'zy-geo.json','w'),separators=(',',':'));json.dump(zb,open(D+'zb-geo.json','w'),separators=(',',':'))
print('zy',len(zy),os.path.getsize(D+'zy-geo.json'),'zb',len(zb),os.path.getsize(D+'zb-geo.json'))
Q=np.column_stack([P[:,1]*KX,P[:,0]]);cs=np.array(cslug)
def acc(extra_pts,extra_sl,mask):
    pts=np.vstack([cmid]+extra_pts);sl=np.concatenate([cs]+extra_sl)
    d,i=cKDTree(pts).query(Q[mask],k=1);return sl[i]==tslug[mask]
kq=Q[kept];ks=tslug[kept]
# BKCB: Brooklyn file only, Brooklyn addresses
m=BO=='bk';kb=kept&m
a=acc([Q[kb]],[tslug[kb]],m);print('BKCB (zb) Brooklyn addresses correct',a.sum(),'of',m.sum(),round(100*a.mean(),2),'| before',round(100*before[m].mean(),1))
# CBNYC: city file
a=acc([kq],[ks],np.ones(len(P),bool));print('CBNYC (zy) all addresses correct',a.sum(),'of',len(P),round(100*a.mean(),2),'| before',round(100*before.mean(),1))
# BKCB6: existing dense zz + zy; find fix-ups
zz=json.load(open(D+'zz-geo.json'))
zq=np.array([[r[3]*KX,r[2]] for r in zz]);zs=np.array([r[0] for r in zz])
allm=np.ones(len(P),bool)
a=acc([zq,kq],[zs,ks],allm);print('BKCB6 (zz+zy) correct',a.sum(),'of',len(P),'wrong',(~a).sum())
fix=np.zeros(len(P),bool)
for it in range(10):
    if a.all(): break
    fix|=~a
    a=acc([zq,kq,Q[fix]],[zs,ks,tslug[fix]],allm);print(' fixups',fix.sum(),'wrong left',(~a).sum())
zw=rows(fix);json.dump(zw,open(D+'zw-geo.json','w'),separators=(',',':'));print('zw',len(zw),os.path.getsize(D+'zw-geo.json'))
