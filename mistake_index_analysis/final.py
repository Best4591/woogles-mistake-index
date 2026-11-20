import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/claude/work')
from evalfw import *; from variants import *
st=json.load(open('/home/claude/work/steps2.json'))
grp=np.select([T.phase=='PHASE_EARLY_MID',T.phase=='PHASE_EARLY_PREENDGAME',T.phase=='PHASE_PREENDGAME'],[0,1,2],3)
def phase_weighted(pen, which='tune'):
    S=pd.DataFrame({'pg':T.pg,'g':grp,'v':pen}).pivot_table(index='pg',columns='g',values='v',aggfunc='sum',fill_value=0).reindex(PG.index).fillna(0)
    m=PGR.notna()&PG.apply(lambda r: r.uid in SPLIT[r.lg][which],axis=1)
    X1=np.c_[np.ones(m.sum()),S[m].to_numpy()]; b=np.linalg.lstsq(X1,PGR[m].to_numpy(),rcond=None)[0]
    wts=b[1:]/b[1]
    return pd.Series(S.to_numpy()@wts,index=S.index), wts
