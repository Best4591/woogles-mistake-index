# Improving the Woogles Mistake Index

Nov 19, 2026 · @George

## Use of AI

I used Claude throughout this project. The questions, the direction and the decisions were mine; Claude did most of the technical work under my direction.

**What I did**

- Set the goal of making the Mistake Index a more accurate measure of how someone played.
- Raised and tested ideas along the way, including scaling mistakes by tiles in the bag, treating blowouts as lopsided for both players, cutoffs based on simulation noise, adjusting for luck, and how the leverage adjusted Mistake Index can be used to determine some factors of luck.
- Asked 14domino for permission before any data was collected, and kept to the agreed limit of one request per second.
- Chose the scope (all three league lexicons) and the tests, including testing against actual game results rather than rating alone.
- Edited the write-up.

**What Claude did**

- Explained the current Mistake Index and the statistics involved, proposed the model changes (smooth curve, noise shrinkage, leverage, spread blend, phase weights).
- Found Woogles' analysis endpoint and wrote the script that fetched the 7,626 games in my browser, then checked the data for completeness.
- Wrote and ran all of the analysis code, including tuning, held-out testing and bootstrap confidence intervals.
- Drafted this write-up, including the charts.

The code, tuned parameters and full results are in the accompanying analysis package, so anyone can rerun or check them.

## Summary

Two changes make the Mistake Index a clearly better measure of how well someone played a single game: shrinking mistakes that are within the simulation's noise, and scaling each mistake by how much was at stake in the position (leverage). Both held up against two independent targets, player rating and actual game results, in all three league lexicons.

- **Against rating:** on held-out players, a single game's score correlates with the player's rating at r = 0.754 on average, up from 0.693 for the current index, using the full model including the optional phase weights (+0.061, 95% CI +0.054 to +0.070). Re-tuning from scratch on the other half of the players gave +0.057.
- **Against actual results:** predicting the winner from each player's previous game, the AUC (how well a prediction separates wins from losses; 0.5 is a coin flip, 1.0 is perfect) rises from 0.602 to 0.609 with noise shrinkage and leverage (+0.007, CI +0.002 to +0.013). The gain fades once 10 or more earlier games are averaged.
- **The index beats rating at predicting results.** From earlier games only, both versions predict winners better than the players' ratings do (AUC 0.65 vs 0.62).
- **Pre-endgame mistakes are counted about twice as harshly as their predictive value justifies.** Endgame mistakes were undercounted by the current index; the new model fixes that.

Recommendation: adopt noise shrinkage and leverage adjustment, keep a smooth penalty curve, and treat phase weights and a spread blend as optional.

## How the current Mistake Index works

Each move is compared with BestBot's top play and sized as small (0.2), medium (0.5) or large (1.0); the Mistake Index is the sum over the player's moves. Summing those weights from the per-turn data reproduces every reported Mistake Index exactly (0 mismatches across 5,882 player-games checked). The sizing rule depends on the phase:

| Phase | What decides the size | Small / medium / large |
| --- | --- | --- |
| Early / mid game | Win% lost | 0.25–3% / 3–7% / over 7% |
| Early / mid, decided game (top play below 0.5% or above 99.5%) | The larger of the win% size and the spread size | Spread up to 15 / 16–30 / over 30 points |
| Early pre-endgame, decided game | The larger of the win% size and the spread size | Spread 1–7 / 8–15 / 16+ points |
| Pre-endgame | Win% lost if any; otherwise spread | Win% as above; spread 1–7 / 8–15 / 16+ points |
| Endgame | Spread lost; a blown endgame is always large | 1–7 / 8–15 / 16+ points |

Win% losses under 0.25% are treated as noise and not counted.

## Data

The test set is 7,626 finished league games from whole recent seasons, with BestBot analysis (version 2) for every game. All were fetched through Woogles' public analysis endpoint at no more than one request per second, with the developers' agreement.

| League | Games | Seasons | Players with 20+ games |
| --- | --- | --- | --- |
| Collins (CSW24) | 2,941 | 24–25 | 200 |
| NWL (NWL23) | 2,656 | 24–26 | 132 |
| Deutsch (RD29) | 2,029 | 20–23 | 80 |

Each turn records the phase, tiles in the bag, the played and optimal moves, win% and spread lost, and the current mistake size. Simulated turns list the top five candidates plus the player's own move, each with win%, its standard error, equity and iteration count. Pre-endgame turns carry each candidate's result for every possible draw, and endgame turns the solved line and final spread. Each game also carries both players' ratings at the time.

The data is complete: no failed downloads, duplicates or missing analyses. 205 games (2.7%) ended by time-out, forfeit, adjudication or six scoreless turns; the first three kinds were excluded from the tests. 42 games lack one player's rating and 634 player-ratings are provisional; these were left out of the rating comparisons.

## How the versions were tested

Every version was tuned on one half of the players and judged on the other half, against two separate targets.

1. **Split the players.** In each lexicon, players with 20+ games were split at random into a tuning half and a test half. Parameters were chosen on the tuning half only. To check the result wasn't luck of the split, the halves were then swapped and everything re-tuned from scratch.
2. **Rating test.** The main measure is the correlation between one game's score and the player's settled (non-provisional) rating at the time. Player-level checks were also run: each player's average score against their rating, and split-half consistency (do two halves of a player's games agree?).
3. **Results test.** Because the parameters were tuned against rating, results were used as an independent check. For each game, each player's average score over their *earlier* games (by start time) was used to predict the winner and the final spread. Win/loss is scored by AUC: the chance that the prediction ranks a game the player won above one they lost. 0.5 is a coin flip and 1.0 is perfect. Final spread is scored by correlation.
4. **Uncertainty.** 95% confidence intervals come from bootstrap resampling of whole players (rating test) or whole divisions (results test), so that games by the same people stay together.

## What was changed

The model was built in stages, each adding one idea to the one before. Each move's penalty is summed over the player's moves in the game, as now.

1. **Smooth curve.** The three steps (0.2 / 0.5 / 1.0) are replaced by a curve, so 2.9% and 3.1% lost no longer score 0.2 vs 0.5. With D the win% lost, or the spread lost where spread applies, and s a scale per measure:

```latex
\text{penalty} = 1 - e^{-D/s}
```

2. **Noise shrinkage.** Gaps smaller than the simulation can resolve are pulled towards zero, using the standard errors of both plays' win% (the player's move often has the larger one, because weaker candidates get fewer iterations). With k the number of standard errors a gap must exceed to count in full:

```latex
D_{\text{adj}} = D \cdot \frac{D^2}{D^2 + (k \cdot SE_\Delta)^2}, \qquad SE_\Delta = \sqrt{SE_{\text{top}}^2 + SE_{\text{played}}^2}
```

3. **Leverage.** Win% lost is divided by how much the position puts at stake: σ, the spread of win% across the top candidates. A 0.3% slip when every candidate sits at 99.9% is a real error, and a 3% slip where the candidates range over 20% is less telling. Floors keep the ratio finite when σ is near zero:

```latex
D_{\text{lev}} = D_{\text{adj}} \cdot \frac{L}{\sigma_{\text{eff}}}, \qquad \sigma_{\text{eff}} = \sqrt{\sigma^2 + SE_{\text{top}}^2 + \sigma_{\min}^2}
```

L is the median σ\_eff over live positions, which keeps the units in win%. The exponent on the ratio was tested at 0.5 to 1.5; 1 was best.

4. **Spread blend.** The hard switch to spread in decided games (below 0.5% or above 99.5%) is replaced by a gradual blend, weighted by how clearly win% separates the two plays (z = D / SE\_Δ). It did not help against rating and gave only a slight edge on results, so it is not part of the recommendation.
5. **Phase weights.** Each phase's total is weighted by how strongly its penalties predict rating: early/mid 1.0, early pre-endgame 0.5, pre-endgame 0.45, endgame 1.0.

Pre-endgame and endgame turns are solved exactly, so they have no simulation noise or leverage step. Their rules stay as now (win% if any is lost, otherwise spread), on the same smooth curve.

## Results against rating

The new model raises the per-game correlation with rating from 0.693 to 0.754 on held-out players (+0.061, 95% CI +0.054 to +0.070). Each step except the spread blend adds a significant amount, and leverage and smoothing carry most of it.

&#91;embedded content: Woogles league games, CSW/NWL/Deutsch, 7,626 games · held-out test players · bootstrap over players\]

Steps are cumulative. Phase weights are measured against the leverage stage, not the spread blend, which was dropped. Swapping the tuning and test halves and re-tuning from scratch gave +0.057 (CI +0.049 to +0.065), with similar parameters.

| Lexicon | Per-game r, current → new | Player-level r with rating | Split-half consistency |
| --- | --- | --- | --- |
| Collins | 0.737 → 0.801 | 0.927 → 0.940 | 0.979 → 0.986 |
| NWL | 0.712 → 0.774 | 0.940 → 0.951 | 0.981 → 0.988 |
| Deutsch | 0.630 → 0.687 | 0.929 → 0.918 | 0.978 → 0.987 |

Per game, the gain is significant in every lexicon. Averaged over a player's 20+ games, both versions already track rating closely, so the differences there are small.

## Results against actual game results

Predicting the winner from each player's previous game, noise shrinkage plus leverage raises the AUC from 0.602 to 0.609 (+0.007, CI +0.002 to +0.013). The gain stays significant up to 5 earlier games and fades by 10, when both versions have averaged out their noise.

&#91;embedded content: Woogles league games, CSW/NWL/Deutsch · earlier games by start time · bootstrap over divisions\]

The smooth curve on its own is within noise on results. The two optional steps behave differently from the rating test: the spread blend is the best stage in every column, but only 0.001–0.003 above leverage alone, and phase weights add nothing. Spread correlation shows the same pattern more strongly: from one earlier game, the final model raises it from 0.243 to 0.274 (+0.031, CI +0.020 to +0.042).

**Both versions predict results better than rating.** From earlier games only, with each player's last 5+ games:

| Predictor | Win/loss AUC | Final spread R² |
| --- | --- | --- |
| Rating at the time | 0.621 | 0.078 |
| Current Mistake Index | 0.650 | 0.106 |
| New Mistake Index | 0.651 | 0.108 |

The index beats rating by +0.03 AUC (CI +0.016 to +0.043), and adding rating to the index barely helps. Rating appears to lag behind the skill the index picks up.

## Other findings

**Phases are not on the same scale.** Regressing rating on each phase's penalty total shows how many rating points one penalty point is worth in each phase (tuning players, ± bootstrap SE):

| Phase | Current index | New model |
| --- | --- | --- |
| Early / mid | −38 ± 1 | −41 ± 1 |
| Early pre-endgame | −16 ± 3 | −21 ± 3 |
| Pre-endgame | −21 ± 6 | −19 ± 5 |
| Endgame | −53 ± 3 | −42 ± 3 |

A pre-endgame penalty point says about half as much about a player as a midgame one, so those mistakes are counted roughly twice as harshly as they should be. The current index undercounts endgame mistakes by about 1.4×; the new model brings the endgame in line with the midgame.

**Summing beats averaging per turn.** Averaging per turn is clearly worse (per-game r 0.72 vs 0.75 for the new model). Weaker players have longer games, with turns per game correlating with rating at r = −0.45, so part of the sum's edge is game length, not purely mistakes.

## Mistake-timing luck

The leverage model also gives a measure of how unlucky a player was in *when* their mistakes happened. For a single game it is mostly luck, and it explains results on top of the Mistake Index; averaged over many games it partly reflects how hard a player's positions were.

For each move, it is the win% the mistake actually cost minus what a mistake of that quality typically costs, which is the leverage-adjusted size:

```latex
\text{timing luck} = D_{\text{adj}} - D_{\text{lev}}
```

Positive means the mistake came in a tense position and hurt more than usual (unlucky); negative means it came in a quiet one (lucky). It is summed over the game and calibrated so it averages zero in each lexicon. Only live simulated positions are used: including decided games inflated it about four-fold, because tiny slips in blowouts count as huge lucky breaks.

**Size.** Per game, timing luck spreads by about ±11 win% points (SD), against about ±19 for the total win% players actually lose. One player in ten is unlucky by about 10 points or more in a game, and one in ten lucky by about 9 or more.

**Does it carry over between games?** Luck shouldn't. Correlation between a player's averages in two random halves of their games:

| League | Timing luck | Mistake Index |
| --- | --- | --- |
| Collins (200 players) | 0.06, not significant | 0.97 |
| NWL (132 players) | 0.20 (CI 0.08–0.32) | 0.97 |
| Deutsch (80 players) | −0.03, not significant | 0.97 |

It is mostly luck, with a small consistent part in NWL. Higher-rated players also tend to be slightly unluckier (correlation 0.18–0.28 with rating), probably because their few mistakes come in sharp, high-stakes positions. That part reflects difficulty, not luck.

**Does it explain results?** Among games where both players' Mistake Indexes were similar, the player with better timing luck won far more often:

| Timing-luck gap (quintile) | Most unlucky | 2 | 3 | 4 | Most lucky |
| --- | --- | --- | --- | --- | --- |
| Win rate | 36% | 60% | 61% | 62% | 71% |

Adding it to the Mistake Index raises same-game win prediction from AUC 0.742 to 0.765, with about half the Mistake Index's weight per standard deviation. This is partly built in, because both come from the same game's win% losses: it shows the measure tracks results, not that it predicts future games.

For a single game, it could be shown next to the Mistake Index as "how unlucky your mistakes were". A long-run average should not be presented as luck.

## Recommendations

Adopt noise shrinkage and leverage: both tests support them clearly. Keep the smooth curve, since it is simple and helped against rating. Phase weights and the spread blend each helped on one test but not the other, so they are optional.

| Change | Rating test | Results test | Recommendation |
| --- | --- | --- | --- |
| Smooth curve | +0.023, significant | Within noise | Adopt |
| Noise shrinkage | +0.007, significant | Small gain, significant from 3 games | Adopt |
| Leverage (n = 1) | +0.025, significant | +0.007 from one game, significant up to 5 | Adopt |
| Spread blend | +0.001, not significant | Slightly best stage, within noise of leverage | Optional |
| Phase weights | +0.005, significant | No gain | Optional |

Recommended parameters, rounded from the two tuning runs:

| Parameter | Value |
| --- | --- |
| Win% curve scale | 2.5% |
| Spread scale, early/mid decided games | 15 points |
| Spread scale, early pre-endgame, pre-endgame and endgame | 8 points |
| Blown endgame | 0.75 |
| Noise shrinkage factor k | 6 |
| Leverage exponent | 1 |
| Leverage floor σ\_min | 1st percentile of σ in live positions |
| Phase weights (if used) | 1.0 / 0.5 / 0.45 / 1.0 |

Scores on this model land in a similar range to the current index (median about 5 per game), and the two correlate at 0.93 per game.

## Limitations

- **Targets are noisy.** Ratings lag behind skill, and single results are dominated by luck, which caps every AUC in the 0.60–0.69 range.
- **Only league games.** All games are long-time-limit league games; faster time controls may behave differently.
- **Small samples in places.** Deutsch has 80 qualifying players, and player-level rating correlation dipped slightly there (0.929 → 0.918, 40 test players).
- **"Earlier" games overlap.** League games run in parallel, so a few "earlier" games were still in progress when the predicted game started.
- **Parameters fit these seasons.** The values come from 2–4 recent seasons per lexicon with analysis version 2; a different analyser version may need re-tuning.
- **Few candidates.** σ is computed from only the top 5–6 candidates per turn, which makes it rough. More candidates, or longer simulations for the player's own move, would make leverage more reliable.
