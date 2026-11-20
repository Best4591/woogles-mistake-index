import sys, itertools, json, time; sys.path.insert(0,'/home/claude/work')
from evalfw import *; from variants import *
def score(params, agg='sum', which='tune'):
    return game_metric(game_scores(penalty(**params), agg), which)['avg']
def grid(base, space, agg='sum'):
    best=None
    keys=list(space)
    for vals in itertools.product(*[space[k] for k in keys]):
        p=dict(base); p.update(dict(zip(keys,vals)))
        s=score(p,agg)
        if best is None or s>best[0]: best=(s,p)
    return best

