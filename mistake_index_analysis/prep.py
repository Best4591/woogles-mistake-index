import json, numpy as np, pandas as pd, math
rows=[]; games=[]
for lg in ['csw','nwl','deutsch']:
    for line in open(f'/mnt/user-data/outputs/woogles_mi_{lg}.jsonl'):
        g=json.loads(line)
        nick2=[s['player_name'] for s in g['summaries']]
        md={p['nick']:p for p in (g['players'] or [])}
        uid=[]; rat=[]; prov=[]
        for k in range(2):
            pl_=g['players'] or []
            p=pl_[k] if len(pl_)==2 else None
            uid.append(p['user_id'] if p else None)
            r=(p or {}).get('rating') or ''
            prov.append(r.endswith('?')); rat.append(float(r.rstrip('?')) if r.rstrip('?') else np.nan)
        win=g['md_winner'] if g['md_winner'] is not None else g['winner_index']
        games.append(dict(game_id=g['game_id'],lg=lg,season=g['season_number'],div=g['division_number'],end=g['end_reason'],
                          u0=uid[0],u1=uid[1],r0=rat[0],r1=rat[1],p0=prov[0],p1=prov[1],winner=win,
                          mi0=g['summaries'][0]['mistake_index'],mi1=g['summaries'][1]['mistake_index']))
        for t in g['turns']:
            r=dict(game_id=g['game_id'],lg=lg,p=t['p'],uid=uid[t['p']],n=t['n'],phase=t['phase'],bag=t['bag'],size=t['size'],
                   wpl=t['wpl'],spl=t['spl'],blown=t['blown_eg'],optimal=t['optimal'],phony=t['phony'])
            if t['sim']:
                c=[s for s in t['sim'] if not s['ign']]
                top=c[0]; pl=next((s for s in c if s['played']),None)
                others=[s for s in c if not (s['played'] and s is not top)][:5]
                wps=np.array([s['wp'] for s in others])
                r.update(src='sim', wtop=max(s['wp'] for s in c), wfirst=top['wp'], sefirst=top['wse'], eqfirst=top['eq'],
                         wpl_=(pl['wp'] if pl else np.nan), sepl=(pl['wse'] if pl else np.nan), eqpl=(pl['eq'] if pl else np.nan),
                         itpl=(pl['it'] if pl else np.nan), ittop=top['it'], sig=float(wps.std(ddof=1)) if len(wps)>1 else np.nan, ncand=len(c))
            elif t['peg']:
                top=t['peg'][0]; pl=next((s for s in t['peg'] if s['played']),None)
                r.update(src='peg', wtop=top['wp'], wpl_=(pl['wp'] if pl else np.nan), sig=float(np.std([s['wp'] for s in t['peg']][:5],ddof=1)) if len(t['peg'])>1 else np.nan)
            else:
                alts={a['first']:a['spread'] for a in t['alt']}
                pv=t['pv_spread']; ps=alts.get(t['move'])
                r.update(src='eg', pv=pv, ps=ps)
            rows.append(r)
T=pd.DataFrame(rows); G=pd.DataFrame(games)
T.to_pickle('turns.pkl'); G.to_pickle('games.pkl')
print(T.shape, G.shape); print(T.groupby(['lg','src']).size())
print('missing uid turns', T.uid.isna().sum())
