# Improving the Woogles Mistake Index

7,626 Woogles games from CSW, NWL, and Deutsch lexicons were used
to attempt to refine Joey Krafchick's mistake index grading.
Five different changes were tested against the current mistake index
to see if they tracked player ratings and future results better, and
a note on mistake-timing luck is also included.

## Write-up

Read the full findings in [Improving the Woogles Mistake Index](mistake_index_analysis/Improving%20the%20Woogles%20Mistake%20Index.md).

## What's in this repository

- `prep.py` – reads the game data into tables
- `tune2.py` – tunes each model step on half the players
- `evaltest.py` – tests each step on the other half
- `results_*.py` – tests against actual game results
- `*.json` – the tuned parameters and results

## Data

The game data (7,626 league games with BestBot analysis) isn't included
here because it contains players' usernames and ratings. You can:

- **Collect it yourself** from Woogles' public analysis endpoint. League
  game IDs come from the league pages, and each game's analysis from
  `GetAnalysisResult`. Please keep to one request per second, as agreed
  with the Woogles developers.
- **Request a copy** by contacting me at gbenbow85@gmail.com.

## Credits

- [Woogles.io](https://woogles.io) for the games and BestBot analysis,
  and César Del Solar (14domino) for permission to collect the data
- [Macondo](https://github.com/domino14/macondo), the engine behind BestBot
- Joey Krafchick, whose Mistake Index grading this work builds on
- Analysis and drafting assisted by Claude (Anthropic); see the
  "Use of AI" section of the write-up

## Licence

MIT – see the `LICENSE` file.
