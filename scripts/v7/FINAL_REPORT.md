# Nexus Sight v7 — single frozen 2026 evaluation

| Model | Games | Accuracy | Log loss | Brier |
|---|---:|---:|---:|---:|
| Elo | 1,970 | 63.35% | 0.64375 | 0.22634 |
| v6_original_data | 1,970 | 64.72% | 0.63392 | 0.22173 |
| v6_expanded_data | 1,970 | 64.62% | 0.63299 | 0.22130 |
| v7_raw | 1,970 | 63.60% | 0.64403 | 0.22593 |
| Elo_calibrated | 1,970 | 63.35% | 0.64375 | 0.22634 |
| v6_calibrated | 1,970 | 64.62% | 0.63299 | 0.22130 |
| v7 | 1,970 | 63.60% | 0.64403 | 0.22593 |

## Frozen-feature ablations

| Model | Games | Accuracy | Log loss | Brier |
|---|---:|---:|---:|---:|
| elo_ratings | 1,970 | 63.45% | 0.63850 | 0.22376 |
| glicko_ratings | 1,970 | 63.60% | 0.63723 | 0.22322 |
| trueskill_ratings | 1,970 | 63.71% | 0.63526 | 0.22237 |
| all_ratings | 1,970 | 63.81% | 0.63340 | 0.22163 |
| add_form | 1,970 | 63.35% | 0.63370 | 0.22173 |
| add_context | 1,970 | 63.40% | 0.64799 | 0.22790 |
| full | 1,970 | 63.60% | 0.64403 | 0.22593 |

All choices were frozen before parsing 2026. No model changes followed this evaluation. Results cover the locked yearly CSV snapshot, not necessarily a completed 2026 season. Secondary games update ratings only. The estimator remains fitted through 2024; 2025 was validation/calibration only.

## Conditional uncertainty vs Elo

- Elo: log-loss improvement 95% interval [0.00000, 0.00000].
- v6_original_data: log-loss improvement 95% interval [0.00354, 0.01697].
- v6_expanded_data: log-loss improvement 95% interval [0.00438, 0.01811].
- v7_raw: log-loss improvement 95% interval [-0.01145, 0.01110].
- Elo_calibrated: log-loss improvement 95% interval [0.00000, 0.00000].
- v6_calibrated: log-loss improvement 95% interval [0.00438, 0.01811].
- v7: log-loss improvement 95% interval [-0.01145, 0.01110].

## Limitations

- Scheduled best-of absent in OE source: masked unknown; no BO inferred from completed series length.
- Series linkage is same-day team pair plus source game ordinal, not an authoritative series ID.
- Fearless era flag is a time proxy, not a tournament-specific rule; constant pre-2025, so its effect is not learned.
- Glicko-2 player updates approximate the opponent team by mean rating and aggregate deviation; TrueSkill uses actual 5v5.
- Validation-tail calibration selection is optimistic; final 2026 is the only locked final evaluation.
- CIs cluster by UTC date and condition on selected models; selection uncertainty is not included.
- v6 code unchanged; v6 expanded-data control and original-data control both refit only through 2024.
- Conservative outcome availability uses max(2 hours, recorded duration + 15 minutes).
- The 2026 yearly source is a snapshot at retrieval time, not guaranteed to be the full season.
- Ratings may update online using earlier completed 2026 results; model and calibration never refit.
- No v7 application deployment: the existing app still serves preserved v6.
