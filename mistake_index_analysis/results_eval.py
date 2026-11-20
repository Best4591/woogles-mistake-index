import numpy as np, pandas as pd, json, warnings; warnings.filterwarnings('ignore')
from sklearn.metrics import roc_auc_score
D=pd.read_pickle('/home/claude/work/results_D.pkl')
D=D[D.rdiff.notna()].reset_index(drop=True)
D['grp']=D.lg+'|'+D.season.astype(str)+'|'+D['div'].astype(str)
for c in ['cur_diff','new_diff','rdiff']: D[c+'_z']=D.groupby('lg')[c].transform(lambda v:(v-v.mean())/v.std())
def ll_logit(X,y):
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(C=1e6,max_iter=1000).fit(X,y)
def cv_metrics(d, feats, k=5, seed=0):
    """grouped CV by division: log-loss for win (no draws) and R^2 for spread"""
    from sklearn.linear_model import LogisticRegression, LinearRegression
    grps=d.grp.unique(); r=np.random.default_rng(seed); r.shuffle(grps); fold={g:i%k for i,g in enumerate(grps)}
    f=d.grp.map(fold).to_numpy(); ll=[]; se=[]; n=0; sst=0
    for i in range(k):
        tr=d[f!=i]; te=d[f==i]
        trw=tr[tr.win!=0.5]; tew=te[te.win!=0.5]
        if feats:
            m=LogisticRegression(C=1e6,max_iter=1000).fit(trw[feats],trw.win); p=m.predict_proba(tew[feats])[:,1]
            lr=LinearRegression().fit(tr[feats],tr.spread); ps=lr.predict(te[feats])
        else:
            p=np.full(len(tew),trw.win.mean()); ps=np.full(len(te),tr.spread.mean())
        p=np.clip(p,1e-6,1-1e-6); ll+=list(-(tew.win*np.log(p)+(1-tew.win)*np.log(1-p)))
        se+=list((te.spread-ps)**2); sst+=((te.spread-tr.spread.mean())**2).sum()
    return float(np.mean(ll)), float(1-np.sum(se)/sst)
def simple(d):
    w=d[d.win!=0.5]; out={}
    for c in ['cur_diff','new_diff','rdiff']:
        out[c]=dict(auc=roc_auc_score(w.win,w[c]), spread_r=np.corrcoef(d[c],d.spread)[0,1])
    return out
res={}
for lg in ['all','csw','nwl','deutsch']:
    d=D if lg=='all' else D[D.lg==lg]
    s=simple(d)
    cv={name:cv_metrics(d,f) for name,f in [('none',[]),('rating',['rdiff_z']),('current',['cur_diff_z']),('new',['new_diff_z']),
                                          ('rating+current',['rdiff_z','cur_diff_z']),('rating+new',['rdiff_z','new_diff_z']),('rating+current+new',['rdiff_z','cur_diff_z','new_diff_z'])]}
    res[lg]=dict(n=len(d),simple=s,cv=cv)
    print(f'== {lg} (n={len(d)})')
    for c,v in s.items(): print(f'   {c:9s} AUC {v["auc"]:.4f}  corr w/ spread {v["spread_r"]:.4f}')
    for k,(ll,r2) in cv.items(): print(f'   CV {k:20s} logloss {ll:.4f}  spread R2 {r2:.4f}')
json.dump(res,open('/home/claude/work/results_eval.json','w'),indent=1,default=float)
