import numpy as np, pandas as pd
T=pd.read_pickle('/home/claude/work/turns.pkl').rename(columns={'size':'msize'})
G=pd.read_pickle('/home/claude/work/games.pkl')
bad_end={'TIME','FORCE_FORFEIT','ADJUDICATED'}
keep_games=set(G.game_id[~G.end.isin(bad_end)])
T=T[T.game_id.isin(keep_games)].reset_index(drop=True)
# player ratings (non-provisional), per player mean
rr=pd.concat([G[['lg','u0','r0','p0']].set_axis(['lg','uid','r','prov'],axis=1),G[['lg','u1','r1','p1']].set_axis(['lg','uid','r','prov'],axis=1)])
rr=rr[(~rr.prov)&rr.r.notna()]
RATING=rr.groupby(['lg','uid']).r.mean()
# player-game keys
T['pg']=T.game_id+'|'+T.p.astype(str)
PG=T.groupby('pg').agg(lg=('lg','first'),uid=('uid','first'),game_id=('game_id','first'),nturns=('n','size'))
rng=np.random.default_rng(12345)
SPLIT={}
for lg in ['csw','nwl','deutsch']:
    u=PG[PG.lg==lg].uid.value_counts(); u=u[u>=20].index.to_numpy()
    u=np.sort(u); rng.shuffle(u); h=len(u)//2
    SPLIT[lg]=dict(tune=set(u[:h]), test=set(u[h:]))
def game_scores(pen, agg='sum'):
    s=pd.Series(pen,index=T.index).groupby(T.pg).sum()
    if agg=='mean': s=s/PG.nturns.reindex(s.index)
    return s
def player_table(gs):
    d=PG.assign(score=gs.reindex(PG.index))
    return d
def metrics(gs, which='test', nsplit=40, seed=0, uids=None):
    d=player_table(gs); out={}
    r=np.random.default_rng(seed)
    for lg in ['csw','nwl','deutsch']:
        us=SPLIT[lg][which] if uids is None else uids[lg]
        x=d[(d.lg==lg)&(d.uid.isin(us))]
        pm=x.groupby('uid').score.mean()
        rat=RATING.reindex([(lg,u) for u in pm.index]).to_numpy()
        ok=~np.isnan(rat)
        rc=np.corrcoef(pm.to_numpy()[ok],rat[ok])[0,1]
        # split-half
        rel=[]
        grp={u:v.to_numpy() for u,v in x.groupby('uid').score}
        for k in range(nsplit):
            a=[];b=[]
            for u,v in grp.items():
                p=r.permutation(len(v)); h=len(v)//2
                a.append(v[p[:h]].mean()); b.append(v[p[h:]].mean())
            c=np.corrcoef(a,b)[0,1]; rel.append(2*c/(1+c))
        out[lg]=dict(n=len(pm), rating_r=-rc, reliability=float(np.mean(rel)))
    return out
def boot_diff(gsA, gsB, which='test', B=1000, seed=1):
    """bootstrap over players: diff in (-corr with rating) B minus A, per lexicon and pooled-average"""
    r=np.random.default_rng(seed); res={}
    dA=player_table(gsA); dB=player_table(gsB)
    allv=[]
    for lg in ['csw','nwl','deutsch']:
        us=SPLIT[lg][which]
        a=dA[(dA.lg==lg)&dA.uid.isin(us)].groupby('uid').score.mean()
        b=dB[(dB.lg==lg)&dB.uid.isin(us)].groupby('uid').score.mean().reindex(a.index)
        rat=RATING.reindex([(lg,u) for u in a.index]).to_numpy(); ok=~np.isnan(rat)
        A=a.to_numpy()[ok]; Bv=b.to_numpy()[ok]; R=rat[ok]; n=len(R)
        diffs=[]
        for _ in range(B):
            i=r.integers(0,n,n)
            diffs.append(-np.corrcoef(Bv[i],R[i])[0,1]+np.corrcoef(A[i],R[i])[0,1])
        diffs=np.array(diffs); allv.append(diffs)
        res[lg]=(float(np.median(diffs)), float(np.percentile(diffs,2.5)), float(np.percentile(diffs,97.5)))
    m=np.mean(allv,axis=0); res['avg']=(float(np.median(m)),float(np.percentile(m,2.5)),float(np.percentile(m,97.5)))
    return res
# game-time rating per player-game
_r=[]
for _,g in G.iterrows():
    _r.append((g.game_id+'|0', g.r0 if not g.p0 else np.nan)); _r.append((g.game_id+'|1', g.r1 if not g.p1 else np.nan))
PGR=pd.Series(dict(_r)).reindex(PG.index)
def game_metric(gs, which='test'):
    out={}
    for lg in ['csw','nwl','deutsch']:
        m=(PG.lg==lg)&PG.uid.isin(SPLIT[lg][which])&PGR.notna()
        x=gs.reindex(PG.index)[m].to_numpy(); y=PGR[m].to_numpy()
        out[lg]=-np.corrcoef(x,y)[0,1]
    out['avg']=float(np.mean(list(out.values())))
    return out
def game_boot(gsA, gsB, which='test', B=1000, seed=2):
    r=np.random.default_rng(seed); res={}; allv=[]
    for lg in ['csw','nwl','deutsch']:
        m=(PG.lg==lg)&PG.uid.isin(SPLIT[lg][which])&PGR.notna()
        sub=PG[m]; a=gsA.reindex(sub.index).to_numpy(); b=gsB.reindex(sub.index).to_numpy(); y=PGR[m].to_numpy()
        uid=sub.uid.to_numpy(); us=np.unique(uid); idx={u:np.where(uid==u)[0] for u in us}
        d=[]
        for _ in range(B):
            pick=np.concatenate([idx[u] for u in r.choice(us,len(us))])
            d.append(-np.corrcoef(b[pick],y[pick])[0,1]+np.corrcoef(a[pick],y[pick])[0,1])
        d=np.array(d); allv.append(d)
        res[lg]=tuple(np.round([np.median(d),np.percentile(d,2.5),np.percentile(d,97.5)],4))
    m=np.mean(allv,axis=0); res['avg']=tuple(np.round([np.median(m),np.percentile(m,2.5),np.percentile(m,97.5)],4))
    return res
