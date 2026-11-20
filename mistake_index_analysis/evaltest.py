import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/claude/work')
from evalfw import *; from variants import penalty
st=json.load(open('steps2.json'))
w={'SMALL':0.2,'MEDIUM':0.5,'LARGE':1.0}
seq=[('V0 current',None),('V1 smooth (scales tuned)',st['S1_smooth_tuned']),('V2 + noise shrink',st['S3_shrink']),
     ('V3 + leverage (n=1)',st['S4_leverage_n1']),('V4 + z-blend w/ spread',st['S5_blend'])]
gss={}
for name,p in seq:
    gss[name]=game_scores(T.msize.map(w).fillna(0).to_numpy()) if p is None else game_scores(penalty(**p))
res={}
prev=None; base=seq[0][0]
for name,_ in seq:
    gm=game_metric(gss[name]); pm=metrics(gss[name], nsplit=20)
    r=dict(game_r=gm, player=pm)
    if prev: r['vs_prev']=game_boot(gss[prev],gss[name],B=1000); r['vs_base']=game_boot(gss[base],gss[name],B=1000)
    res[name]=r; prev=name
    print(name, {k:round(v,4) for k,v in gm.items()}, '| vs prev', r.get('vs_prev',{}).get('avg'), '| vs base', r.get('vs_base',{}).get('avg'))
    print('    per-lexicon vs prev', {k:v for k,v in r.get('vs_prev',{}).items() if k!='avg'})
    print('    player-level rating r', {k:round(v['rating_r'],4) for k,v in pm.items()}, 'reliability', {k:round(v['reliability'],4) for k,v in pm.items()})
json.dump(res, open('test_results.json','w'), indent=1, default=float)
