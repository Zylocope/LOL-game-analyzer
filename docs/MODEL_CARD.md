# Model card: Nexus Sight v6

| | |
|---|---|
| **Task** | Probability that the blue side wins a professional League of Legends game, before the game starts |
| **Model** | Regularised logistic regression on Elo-based and draft features (`backend/model_v6.pkl`, version `v6_elo_corrections`) |
| **Inputs** | Two team names, ten champions by role, optionally the ten starting players and the patch |
| **Output** | Blue and red win probability, the factors behind it, and reliability warnings |
| **Author** | La Min Oo (Zylocope) |

## Intended use

Portfolio project and pre-game analysis for fans and analysts: comparing drafts and seeing how much a draft shifts
an Elo-based expectation. **Not intended for betting**; it has not been compared with bookmaker odds.

## Training data

- Source: [Oracle's Elixir](https://oracleselixir.com/) match data.
- Model fitting: 12,033 games, January 2018 to September 2025 (LCK, LPL, LEC, LCS, MSI; 2022 and Worlds were not in
  that build). Hyperparameters chosen on expanding-season folds (2021, 2023, 2024); 2025 used for validation.
- Every feature uses only results available before the match. Results enter the history after
  max(2 hours, game length + 15 minutes).

## Evaluation

Sealed 2026 holdout (1,970 games), downloaded and hashed before development, evaluated once after freezing.
The tested copy of v6 was fitted on games through 2024 (same method and settings as the served copy, which is fitted
through September 2025):

| Model | Accuracy | Log loss | Brier |
|---|---:|---:|---:|
| Tuned Elo | 63.35% | 0.6438 | 0.2263 |
| **v6** | **64.72%** | **0.6339** | **0.2217** |

Log-loss improvement over Elo: 95% interval **0.0035 to 0.0170** (paired bootstrap by match day, conditional on the
selected model). Accuracy difference is within noise. Source: `scripts/v7/FINAL_REPORT.md`.

### Subgroups (same holdout)

| Subgroup | Games | v6 accuracy | Log loss |
|---|---:|---:|---:|
| Draft has a rare pick (< 50 earlier pro games) | 61 | 55.7% | 0.684 |
| No rare pick | 1,909 | 65.0% | 0.632 |
| Draft has an unusual-role pick (< 10% of the champion's pro games in that role) | 551 | 63.0% | 0.647 |
| No unusual-role pick | 1,419 | 65.4% | 0.629 |

Source: `scripts/analysis/rare_and_offrole_2026.py`. The rare-pick subgroup is small (accuracy 95% interval 43–67%).

## Known limitations

- Probability quality improves over Elo; accuracy essentially does not.
- Coefficients are frozen from development; ratings and form were refreshed with games through October 2026 after
  the sealed test (`python -m backend.refresh_ratings`). The original bundle is kept as `model_v6.original.pkl`.
- Rare champions, unusual roles, new players and new patches have little or no history; the app warns about the first
  two, and unknown players receive neutral ratings.
- Match completion times and series structure are approximated.
- 2025 was inspected during earlier development; only the 2026 holdout is a clean test.
- A v7 model with Glicko-2, TrueSkill and match context did not beat v6 on the holdout and is not served.

## Ethical and legal notes

Uses public professional match data with attribution. Contains no personal data beyond public player handles.
League of Legends is a trademark of Riot Games; this project is not endorsed by Riot Games.
