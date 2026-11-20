import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/claude/work')
import numpy as np, pandas as pd
from evalfw import PG, G, T
from scipy.special import expit
from scipy.optimize import minimize
gs0=pd.read_pickle('gs_current.pkl'); gsn=pd.read_pickle('gs_rec.pkl')
Gk=G[~G.end.isin({'TIME','FORCE_FORFEIT','ADJUDICATED'})].copy()
sc=pd.DataFrame({'uid':PG.uid,'lg':PG.lg,'game_id':PG.game_id,'cur':gs0.reindex(PG.index),'new':gsn.reindex(PG.index)})
# leave-one-out player means
agg=sc.groupby('uid')[['cur','new']].agg(['sum','count'])
def loo(row_uid, col, val):
    s=agg.loc[row_uid,(col,'sum')]; n=agg.loc[row_uid,(col,'count')]
    return (s-val)/(n-1) if n>1 else np.nan, n-1
rows=[]
for _,g in Gk.iterrows():
    k0=g.game_id+'|0'; k1=g.game_id+'|1'
    if k0 not in sc.index or k1 not in sc.index: continue
    r={'lg':g.lg,'season':g.season,'div':g['div'],'game_id':g.game_id}
    for c in ['cur','new']:
        a,na=loo(g.u0,c,sc.at[k0,c]); b,nb=loo(g.u1,c,sc.at[k1,c]); r[c+'_diff']=b-a  # positive = player0 expected better
        r['n0'],r['n1']=na,nb
    r['rdiff']=(g.r0-g.r1) if (not g.p0 and not g.p1 and pd.notna(g.r0) and pd.notna(g.r1)) else np.nan
    s=g.get('scores') if 'scores' in g else None
    r['win']=1.0 if g.winner==0 else (0.0 if g.winner==1 else 0.5)
    rows.append(r)
D=pd.DataFrame(rows)
sp=G.set_index('game_id')
# final spread from crosstable scores in games.pkl? recompute from jsonl metadata
spread={}
for lg in ['csw','nwl','deutsch']:
    for line in open(f'/mnt/user-data/outputs/woogles_mi_{lg}.jsonl'):
        g=json.loads(line); s=g.get('md_scores') or g.get('scores'); spread[g['game_id']]=s[0]-s[1]
D['spread']=D.game_id.map(spread)
D=D[(D.n0>=10)&(D.n1>=10)].reset_index(drop=True)
D.to_pickle('results_D.pkl')
print('games used',len(D), D.groupby('lg').size().to_dict(), 'with both ratings', D.rdiff.notna().sum())
print('draws', (D.win==0.5).sum(), ' player0 win rate', round(D.win.mean(),3))
