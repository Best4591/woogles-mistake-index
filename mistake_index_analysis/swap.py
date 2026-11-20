import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/claude/work')
import evalfw
for lg in evalfw.SPLIT: evalfw.SPLIT[lg]['tune'],evalfw.SPLIT[lg]['test']=evalfw.SPLIT[lg]['test'],evalfw.SPLIT[lg]['tune']
from tune import grid
from evalfw import *; from variants import penalty
from final import phase_weighted
b1=grid({}, dict(sw=[0.03,0.05,0.072,0.1], ss_mid=[2,4,8,15,31], ss_late=[3,5,8,15]))
b1=grid(b1[1], dict(blown_pen=[0.25,0.5,0.75,1.0]))
b3=grid(dict(b1[1],shrink=True), dict(k_shrink=[1,2,3,4,6,10]))
b4=grid(dict(b3[1],lev_n=1.0), dict(smin_q=[0.0,0.01,0.02,0.05,0.1], sw=[0.02,0.03,0.04,0.054,0.072]))
print('swapped tuned params', b4[1])
w={'SMALL':0.2,'MEDIUM':0.5,'LARGE':1.0}
gs0=game_scores(T.msize.map(w).fillna(0).to_numpy())
g1=game_scores(penalty(**b1[1])); g3=game_scores(penalty(**b3[1])); g4=game_scores(penalty(**b4[1]))
g5,wts=phase_weighted(penalty(**b4[1]))
for n,gs in [('current',gs0),('smooth',g1),('+shrink',g3),('+leverage',g4),('+phase weights',g5)]: print(n, {k:round(v,4) for k,v in game_metric(gs).items()})
print('phase weights',np.round(wts,2))
print('final vs current', game_boot(gs0,g5,B=1000))
json.dump(dict(params=b4[1],wts=list(map(float,wts))),open('swap_result.json','w'))
