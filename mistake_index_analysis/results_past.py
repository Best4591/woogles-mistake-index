import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/claude/work')
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from evalfw import PG, G
gs0=pd.read_pickle('gs_current.pkl'); gsn=pd.read_pickle('gs_rec.pkl')
ts={}; spread={}; ended={}
for lg in ['csw','nwl','deutsch']:
    for line in open(f'/mnt/user-data/outputs/woogles_mi_{lg}.jsonl'):
        g=json.loads(line); ts[g['game_id']]=g['created_at']; s=g.get('md_scores') or g.get('scores'); spread[g['game_id']]=s[0]-s[1]
Gk=G[~G.end.isin({'TIME','FORCE_FORFEIT','ADJUDICATED'})].copy(); Gk['ts']=Gk.game_id.map(ts)
# NOTE: created_at = game start; correspondence games overlap, so 'past' = games started earlier and of which we use all info
sc=pd.DataFrame({'uid':PG.uid,'game_id':PG.game_id,'cur':gs0.reindex(PG.index),'new':gsn.reindex(PG.index)}).dropna()
sc['ts']=sc.game_id.map(ts); sc=sc.sort_values('ts')
hist={}  # uid -> list of (ts,cur,new)
for r in sc.itertuples(): hist.setdefault(r.uid,[]).append((r.ts,r.cur,r.new))
def past_mean(uid, t, minn=5):
    h=[x for x in hist.get(uid,[]) if x[0]<t]
    if len(h)<minn: return np.nan,np.nan,len(h)
    a=np.array([x[1:] for x in h]); return a[:,0].mean(),a[:,1].mean(),len(h)
rows=[]
for g in Gk.itertuples():
    c0,n0,k0=past_mean(g.u0,g.ts); c1,n1,k1=past_mean(g.u1,g.ts)
    if np.isnan(c0) or np.isnan(c1): continue
    if g.p0 or g.p1 or pd.isna(g.r0) or pd.isna(g.r1): continue
    rows.append(dict(lg=g.lg,season=g.season,div=g.div,game_id=g.game_id,cur_diff=c1-c0,new_diff=n1-n0,rdiff=g.r0-g.r1,
                     win=1.0 if g.winner==0 else (0.0 if g.winner==1 else 0.5),spread=spread[g.game_id],k=min(k0,k1)))
P=pd.DataFrame(rows); P['grp']=P.lg+'|'+P.season.astype(str)+'|'+P['div'].astype(str)
P.to_pickle('results_P.pkl')
print('past-only games',len(P),P.groupby('lg').size().to_dict(),'median prior games',P.k.median())
