# Nexus Sight

**Pre-game win probability for professional League of Legends matches.** Pick two teams and their draft; Nexus Sight
estimates each side's chance to win from team and player strength, recent form and the draft, and tells you when a
prediction is less reliable.

**Live demo:** [lol-game-analyzer.onrender.com](https://lol-game-analyzer.onrender.com) (free hosting: the first visit can take about a minute to wake up) · **Stack:** Python (scikit-learn, FastAPI, SQLite) · React + TypeScript (Vite)

---

## Results

Tested once on **1,970 pro games from 2026** that were downloaded and sealed *before* any model development, then
evaluated a single time after every model choice was frozen.

| Model | Accuracy | Log loss ↓ | Brier ↓ |
|---|---:|---:|---:|
| Tuned Elo (baseline) | 63.4% | 0.644 | 0.226 |
| **Nexus Sight (v6)** | **64.7%** | **0.634** | **0.222** |

- The model's probabilities are measurably better than Elo's: the log-loss improvement has a 95% interval of
  **+0.004 to +0.017** (bootstrap by match day), which excludes zero.
- Accuracy is about one point higher, within noise. Most of what is predictable in pro play is team strength;
  the draft mainly improves *how confident* the model should be, not *which* team it picks.
- The tested copy was fitted on games through 2024; the app serves the same method fitted through September 2025.
- The interval does not include uncertainty from choosing between models. Full report:
  [`scripts/v7/FINAL_REPORT.md`](scripts/v7/FINAL_REPORT.md).

### When predictions are less reliable

Measured on the same 2026 test games ([script](scripts/analysis/rare_and_offrole_2026.py),
[output](scripts/analysis/rare_and_offrole_2026.txt)):

| Draft contains | Games | Accuracy | Log loss |
|---|---:|---:|---:|
| A **rare pick** (fewer than 50 earlier pro games) | 61 | 55.7% | 0.684 |
| No rare pick | 1,909 | 65.0% | 0.632 |
| A champion in an **unusual role** (under 10% of its pro games in that role) | 551 | 63.0% | 0.647 |
| No unusual role | 1,419 | 65.4% | 0.629 |

The rare-pick gap is large but based on only 61 games (95% interval for their accuracy: 43–67%), so treat it as a
warning sign rather than a precise number. The app shows both warnings next to the prediction.

## What this project claims (and the evidence)

| Claim | Evidence |
|---|---|
| Better win probabilities than a tuned Elo baseline on unseen games | Sealed 2026 holdout, 1,970 games: log loss 0.634 vs 0.644, 95% interval of the improvement +0.004 to +0.017 ([report](scripts/v7/FINAL_REPORT.md)) |
| About one point higher accuracy than Elo, **not** a significant accuracy gain | Same holdout: 64.7% vs 63.4%; the accuracy interval includes zero |
| No outcome leakage in features | Chronological replay with a result-availability delay; regression tests in `backend/tests` check that a game's own and later results are never visible |
| Predictions are weaker for rare picks and unusual roles | Subgroup analysis on the holdout ([script](scripts/analysis/rare_and_offrole_2026.py)) |
| A richer v7 model did not help | v7 (Glicko-2, TrueSkill, context) scored 63.6%, log loss 0.644 on the same holdout, so v6 stays in production |

Not claimed: betting value, causal champion effects, or performance on leagues outside those listed.

## How it works

1. **Data:** professional games from [Oracle's Elixir](https://oracleselixir.com/) (LCK, LPL, LEC, LCS/LTA, MSI and
   Worlds). The app's database holds 17,350 games from January 2018 to October 2026.
2. **Ratings:** team Elo (tuned K-factor, 20% shrink toward the mean between seasons) and player ratings that follow
   players across teams.
3. **Features, all from before the match:** rating differences, roster stability, recent form relative to Elo
   expectations, patch-and-role champion strength, player comfort on the champion, and lane matchups. A game's result
   only becomes available to later games after a conservative delay, to avoid leaking outcomes.
4. **Model:** regularised logistic regression, chosen over gradient boosting on earlier seasons
   (walk-forward validation), with side-symmetric probabilities.
5. **App:** FastAPI serves predictions, team/player/champion stats and the model's own benchmark; the React front end
   is the draft board. Champion win and pick rates are computed from the **last 12 months** of pro games in the
   database and smoothed toward 50% for champions with few games.

### What I learned (the honest part)

An early version reported 78% accuracy. An audit showed most of that came from **target leakage**: matchup win rates
had been computed from all games, including the game being predicted. Rebuilt with strictly chronological features,
accuracy fell to about 65%, roughly level with Elo. The current version was validated season by season and then tested
once on a sealed 2026 holdout. A later v7 experiment (Glicko-2, TrueSkill, more context) did **not** beat v6 on that
holdout, so v6 stays in production.

## Ranked mode (in progress)

A draft-only model for high-rank solo queue (Master and above), where there are no fixed teams and matchmaking makes
both sides similar in skill. Data collection and training scripts are in [`scripts/ranked/`](scripts/ranked/).

- **Data:** _to be added_
- **Results:** _to be added_
- **In the app:** _to be added_

See [`docs/RANKED_MODE.md`](docs/RANKED_MODE.md).

## Limitations

- Accuracy is close to an Elo baseline; gains are in probability quality, not in picking more winners.
- Rare picks and unusual roles have little data, so those predictions are weaker (see above).
- The tested copy of v6 was fitted on games through 2024; the served copy uses the same method and settings fitted
  through September 2025. After the sealed 2026 test, only ratings and form were refreshed with games through
  October 2026 (`python -m backend.refresh_ratings`); the coefficients themselves were not refitted.
- Match end times are estimated (start + max(2 h, game length + 15 min)), not official.
- Best-of-series format is not available in the source data; series are linked approximately.
- Only major leagues and international events are reported; smaller leagues are used for ratings only (v7).
- Player names are matched by aliases and IDs; unusual spellings can fall back to neutral ratings.
- Pre-game only: nothing that happens during the match is used.

## Future work

- Evaluate on 2027 games as a new sealed test, then decide whether to refit the coefficients on 2025–2026.
- Finish **Ranked mode** (see above) and add a mode switch to the app.
- Explanations per prediction (which factors moved the probability).
- Comparison against bookmaker odds.
- Scheduled data updates (e.g. a weekly GitHub Action).

## Run locally

Python 3.12+ and Node.js 22+. In PowerShell from the repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000. The database and model files are not in Git; see
[`docs/TECHNICAL.md`](docs/TECHNICAL.md) to rebuild them from Oracle's Elixir CSVs and retrain.
To put the app online, see [`deploy/DEPLOY.md`](deploy/DEPLOY.md).

## Project structure

```
backend/          FastAPI app (main.py, services.py), features, models, training, data import, tests
frontend/         React + TypeScript draft board (Vite); data/ holds champion tags and fallback stats
scripts/
  v7/             Frozen 2026 holdout evaluation: protocol, report, data dictionary
  analysis/       Rare-pick and unusual-role analysis on the holdout
  ranked/         Ranked mode: Riot API collector and draft-only trainer (in progress)
deploy/           Docker image and packer for Hugging Face Spaces
docs/             Model card, technical notes, Ranked mode notes, archived reports
tools/legacy/     Earlier experiments, kept for reference only
```

Not in Git (rebuilt locally): the SQLite database, trained models, raw CSVs, `.env`.

## More documentation

- [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md): intended use, data, evaluation and caveats on one page
- [`docs/TECHNICAL.md`](docs/TECHNICAL.md): features, leakage protection, data import and tests
- [`docs/RANKED_MODE.md`](docs/RANKED_MODE.md): solo queue mode (in progress)
- [`scripts/v7/FINAL_REPORT.md`](scripts/v7/FINAL_REPORT.md): sealed 2026 evaluation, ablations and intervals
- [`scripts/v7/DATA_DICTIONARY.md`](scripts/v7/DATA_DICTIONARY.md): data fields and reproduction steps

Data: Oracle's Elixir. League of Legends is a trademark of Riot Games; this project is not endorsed by Riot Games.
