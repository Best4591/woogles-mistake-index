import numpy as np
from evalfw import T
ph=T.phase.to_numpy(); src=T.src.to_numpy()
MID=ph=='PHASE_EARLY_MID'; EPEG=ph=='PHASE_EARLY_PREENDGAME'; PEG=ph=='PHASE_PREENDGAME'; EG=ph=='PHASE_ENDGAME'
SIM=src=='sim'
wpl=T.wpl.to_numpy(float); spl=T.spl.to_numpy(float); blown=T.blown.to_numpy(bool)
wfirst=T.wfirst.to_numpy(float); sef=T.sefirst.fillna(0).to_numpy(float); sep=T.sepl.fillna(0).to_numpy(float)
sig=T.sig.to_numpy(float)
DEC=SIM&((wfirst<0.005)|(wfirst>0.995))
SE_D=np.sqrt(sef**2+sep**2)
def g(x): return 1-np.exp(-np.maximum(x,0))
def penalty(sw=0.072, ss_mid=31.0, ss_late=15.4, shrink=False, k_shrink=1.0, lev_n=0.0, smin_q=0.1, blend=None, z0=2.0, a=5.3, b=0.5, blown_pen=1.0, peg_rule='current'):
    D=np.where(SIM|PEG, wpl, 0.0).copy()
    if shrink:
        s=k_shrink*SE_D
        D=np.where(SIM, D*D**2/(D**2+s**2+1e-18), D)
    if lev_n>0:
        live=SIM&~DEC&np.isfinite(sig)
        smin=np.nanquantile(sig[live], smin_q)
        se_e=np.where(np.isfinite(sig),np.sqrt(np.nan_to_num(sig)**2+sef**2+smin**2),np.nan)
        L=np.nanmedian(se_e[live])
        f=np.where(SIM&np.isfinite(se_e), (L/se_e)**lev_n, 1.0)
        D=D*f
    pw=g(D/sw)
    ps_mid=g(spl/ss_mid); ps_late=g(spl/ss_late)
    pen=np.zeros(len(T))
    if blend is None:
        pen[MID]=np.where(DEC[MID], np.maximum(pw[MID],ps_mid[MID]), pw[MID])
        pen[EPEG]=np.where(DEC[EPEG], np.maximum(pw[EPEG],ps_late[EPEG]), pw[EPEG])
    else:
        if blend=='z':
            z=np.where(SE_D>0, wpl/np.maximum(SE_D,1e-12), np.where(wpl>0,np.inf,0))
            w=np.where(np.isinf(z),1.0, z**2/(z**2+z0**2))
        else: # log-odds distance of top play
            p=np.clip(wfirst,1e-6,1-1e-6); d=np.abs(np.log(p/(1-p)))
            w=1/(1+np.exp((d-a)/b))
        psm=np.where(MID,ps_mid,ps_late)
        bl=w*pw+(1-w)*psm
        pen[SIM]=bl[SIM]
    if peg_rule=='current':
        pen[PEG]=np.where(wpl[PEG]>0, pw[PEG], ps_late[PEG])
    pen[EG]=np.where(blown[EG], blown_pen, ps_late[EG])
    return pen
