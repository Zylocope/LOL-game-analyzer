<!-- Detailed technical notes (moved from the README on 2026-10-26). The README is the overview. -->

# Nexus Sight v7 — frozen prospective evaluation

V7 preserves the existing v6 code, model, report and database as a fingerprinted baseline. All new experiment scripts are under `scripts/v7/`; the application continues to serve v6 while v7 remains a separately reviewed experiment. Nothing is pushed to GitHub.

Development: expanding 2018–2024 histories, evaluated on each eligible next season (2019–2024). **2025 is validation/calibration only.** The official **2026 yearly CSV was downloaded as opaque bytes and SHA-256 locked before development**, then reserved for a single final evaluation.

### Final 2026 results

<!-- V7_FINAL_START -->

| Model | Games | Accuracy | Log loss | Brier |
|---|---:|---:|---:|---:|
| Elo | 1,970 | 63.35% | 0.64375 | 0.22634 |
| v6_original_data | 1,970 | 64.72% | 0.63392 | 0.22173 |
| v6_expanded_data | 1,970 | 64.62% | 0.63299 | 0.22130 |
| v7_raw | 1,970 | 63.60% | 0.64403 | 0.22593 |
| Elo_calibrated | 1,970 | 63.35% | 0.64375 | 0.22634 |
| v6_calibrated | 1,970 | 64.62% | 0.63299 | 0.22130 |
| v7 | 1,970 | 63.60% | 0.64403 | 0.22593 |

[Full frozen report](../scripts/v7/FINAL_REPORT.md) · [Calibration plot](../scripts/v7/final_calibration.png)

<!-- V7_FINAL_END -->

The final source is a snapshot at retrieval time, not necessarily a completed season. Frozen models may update rating history using earlier available outcomes during online testing; estimator weights and calibration never refit on 2026. Comparisons use identical reporting games.

### Development and validation

The expanded sources contain 34,097 usable games. Secondary leagues update ratings only. Reported cohorts are LCK, LPL, LEC, North America, and international MSI/Worlds games. The experiment includes 2022 and Worlds, and compares unchanged v6 on original and expanded historical data with tuned Elo and v7.

Regularized logistic and LightGBM compete on development log loss. V7 also tests player Glicko-2, actual 5v5 TrueSkill, international-derived regional offsets, recent form, patch/comfort and match context. Platt, isotonic and no calibration are compared on a chronological 2025 split only; the winning calibration procedure is frozen before 2026.

[Validation metrics and ablations](../scripts/v7/validation_report.json) · [Validation calibration curve](../scripts/v7/validation_calibration.png) · [Data dictionary and reproduction](../scripts/v7/DATA_DICTIONARY.md) · [Preregistered protocol](../scripts/v7/protocol.json)

Important limitations: scheduled best-of metadata is absent and masked unknown, not inferred from future series length. Series links are approximate same-day pairings. The fearless flag denotes an era, not confirmed event rules; its effect is not learnable from pre-2025 estimator fitting. Glicko-2 player updates use a mean-opponent approximation. Date-clustered bootstrap intervals condition on model selection and do not establish future superiority.

### Run or inspect v7

```powershell
python -m pip install -r scripts/v7/requirements.txt
python -m unittest scripts.v7.tests -v
```

The complete download/build/train/freeze/final sequence is documented in the data dictionary. Once `freeze.json` exists, training is prohibited; once `final_run.claim` exists, another final attempt is prohibited. Preserve those files. Frozen code must not be changed after the final evaluation.

---

## Preserved v6 documentation

# Nexus Sight

League of Legends pre-game analysis with React, FastAPI, SQLite, and small statistical models. The model uses only information available before the game; no external AI credentials are needed.

## Latest benchmark

The local database contains 12,033 usable games from 2018–2025. LPL and MSI are present. **2022 and Worlds are missing.** Run `python -m backend.data_quality` to inspect the actual coverage.

Model selection uses expanding-season development folds for 2021, 2023, and 2024. Earlier seasons train each fold; its next available season evaluates it. The same protocol chooses rating settings and model parameters. The selected model is a regularized logistic regression, which outperformed gradient boosting on development log loss.

The following results use the **same 1,746 games from 2025**:

| Model stage | Accuracy | Log loss | Brier score |
| --- | ---: | ---: | ---: |
| Tuned Elo | 64.78% | 0.62866 | 0.21929 |
| Add player ratings / roster stability | 64.26% | 0.62598 | 0.21788 |
| Add recent form | 64.60% | 0.62596 | 0.21789 |
| Add patch / comfort / lane features | 64.72% | 0.62066 | 0.21551 |

Lower log loss and Brier score are better. Probability quality improves; classification accuracy is essentially unchanged. Do not claim a demonstrated accuracy advantage.

The paired calendar-day bootstrap interval for the selected model's log-loss improvement over tuned Elo is **0.00209–0.01373**. Its accuracy difference interval includes zero. These intervals do not include uncertainty from model selection or future data shifts.

**2025 was already inspected during the v5 work.** These are retrospective comparisons, not a fresh untouched test. The v5 66.58% figure used a different reporting window and cannot be compared directly with this table. Preserve new future games for a genuinely prospective evaluation.

Exact results, all candidates, folds, coverage, and runtime: `../backend/evaluation_v6.json`. Previous v5 results remain in `backend/evaluation_v5.json`.

## Efficiency and features

- Incremental history updates avoid rebuilding full matchup snapshots for every game. The final benchmark replay took about **1.1 seconds**; the complete rating/model search and fit took about **12 seconds** locally. These timings exclude Python startup and source CSV import and vary by machine.
- Team Elo K-factor and between-season regression are selected on earlier seasons. Current settings: K=16, 20% annual shrinkage toward 1200.
- Player ratings use stable source IDs and follow players across teams. Serving resolves supplied player names against historical IDs. Missing players receive neutral priors.
- Recent form uses the last ten games, weighted toward recent results, measured relative to prior Elo expectations rather than raw wins alone.
- Champion strength is patch-and-role-specific, smoothed toward zero advantage. Player/champion comfort uses both past game counts and smoothed performance relative to team expectations.
- Explicit Elo-offset logistic corrections, ordinary regularized logistic regression, and gradient boosting compete on development folds. Each stage has a separate baseline comparison.
- Predictions and replay use the same feature implementation and enforce side-symmetric probabilities.
- Tiny models use a single CPU thread during training to avoid oversubscription. No GPU is required.

## Outcome availability

Dates may indicate game starts. A result is withheld until **max(2 hours, recorded duration + 15 minutes)** after its timestamp, and must be strictly earlier than the next game's start to enter its history. This conservative delay protects against overlapping-match leakage; it is still an approximation, not verified official completion time. Same-start games never see one another's outcomes. Deployment snapshots include all completed historical results after replay ends.

Player name aliases can be ambiguous; historical IDs are preferred when available. Newly selected patches without observations receive neutral patch priors. Current patch-specific features do not establish causal champion effects or betting calibration.

## Run

Python 3.12+ and Node.js are required. From the project root, in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m backend.data_quality
python -m backend.train
python -m uvicorn backend.main:app --reload --port 8000
```

In a second terminal:

```powershell
npm ci
npm run dev
```

Open http://localhost:3000. The frontend shows the recorded benchmark and data cutoff. Select both drafts and starting players. A blank patch uses the latest patch in the training data, **not today's live patch**. Specify patches with two minor digits, e.g. `15.01` or `15.10`.

The backend loads `model_v6.pkl` and falls back to a v5 bundle only when v6 is absent. It never retrains at startup. Missing models return HTTP 503. Train again and restart the backend after changing the data or dependency versions.

Configure `VITE_API_URL` before building the frontend and backend `CORS_ORIGINS` for hosted origins. No external AI keys are required. Use HTTPS when hosting.

## Import more data safely

Use source CSVs from [Oracle's Elixir downloads](https://master.d36liwrx5rvjnc.amplifyapp.com/tools/downloads), including 2022 and Worlds. No new source games were downloaded during this upgrade.

```powershell
# Append source CSVs to the existing database, deduplicating game/side/role:
python -m backend.db_builder path\to\2022.csv path\to\worlds.csv
python -m backend.add_indexes
python -m backend.data_quality
python -m backend.train
```

Alternatively put CSVs in `backend/Data` and run `python -m backend.db_builder`. The importer streams chunks, retains the `W` Worlds code and historical `Wxx` codes, rejects contradictory outcomes, and stages imports before replacing the live database. Reimporting the same rows does not duplicate them. `--replace` explicitly rebuilds from supplied CSVs. Data is not included in a fresh clone.

## Refresh ratings without retraining

After new games are imported, `python -m backend.refresh_ratings` replays the rating, form and champion history through
the latest game with the K-factor and season shrink chosen during development, swaps that state into `model_v6.pkl`,
rebuilds `team_ratings.json` and attaches the sealed 2026 holdout result. The fitted coefficients do not change.

## Checks and structure

```powershell
python -m unittest discover -s backend/tests -v
npm run build
```

The build includes TypeScript checking. Regression tests cover availability delays, future-label isolation, patch/player separation, season shrinkage, validation folds, side symmetry, missing models, and safe imports.

- `backend/features.py`: fast replay and shared inference features.
- `backend/models.py`: Elo, Elo corrections, logistic regression, and gradient boosting.
- `backend/experiment.py`: rating search, walk-forward comparisons, intervals, and artifacts.
- `backend/train.py`: supported training entry point.
- `backend/data_quality.py`, `backend/db_builder.py`: coverage and safe CSV import.
- `backend/main.py`, `backend/services.py`: APIs and historical statistics.
- `tools/legacy`, `docs/archive`: historical experiments and notes; not maintained workflows.

Local model artifacts and databases are ignored by Git. Existing old models, backups, and unrelated working changes are preserved.
