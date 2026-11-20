# Mistake Index analysis (Woogles league games, CSW/NWL/Deutsch)

Data: woogles_mi_{csw,nwl,deutsch}.jsonl (7,626 league games, BestBot analysis v2).

Run order: prep.py (builds turns.pkl/games.pkl) -> tune2.py (tunes steps on half the players) -> evaltest.py (held-out test) -> final.py helpers -> swap.py (re-tune on the other half).

Evaluation: players with 20+ games split 50/50 into tune/test per lexicon (seed 12345). Main metric: per-game correlation between the game's score and the player's game-time (non-provisional) rating; cluster bootstrap by player for CIs. Games ending by TIME / FORCE_FORFEIT / ADJUDICATED excluded.

Recommended model (per turn penalty, summed over the player's turns in the game):
- Early/mid and early pre-endgame (simulated): D = win% lost; shrink by noise D*D^2/(D^2+(6*SE)^2), SE = sqrt(SE_top^2+SE_played^2);
  leverage-adjust D * L/sigma_eff, sigma_eff = sqrt(sigma^2 + SE_top^2 + sigma_min^2), sigma = SD of win% across the top candidates,
  sigma_min = 1st percentile of sigma, L = median sigma_eff over live positions; penalty = 1 - exp(-D/0.025).
  If top play win% < 0.5% or > 99.5%: penalty = max(that, 1 - exp(-spread_loss/15)) [early pre-endgame: /8].
- Pre-endgame: win% lost > 0 -> 1 - exp(-D/0.025); else 1 - exp(-spread_loss/8).
- Endgame: 1 - exp(-spread_loss/8); blown endgame = 0.75.
- Phase weights: early/mid 1.0, early pre-endgame 0.5, pre-endgame 0.45, endgame 1.0.

## Results-based test (actual game results)
results_test.py / results_past.py build, for each game, the difference between the two players' average index from their OTHER games (or only EARLIER games, by game start time), then results_eval.py compares win/loss (AUC, CV log-loss) and final spread (correlation, CV R^2) against game-time rating. Bootstrap CIs resample whole divisions. results_lastk.json: same test using only each player's last 1/3/5/10 earlier games.
