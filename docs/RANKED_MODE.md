# Ranked mode (experiment)

Draft-only win prediction for high-rank solo queue (Master, Grandmaster, Challenger).

## Why it is a separate model

In pro play, team strength (Elo) explains most of what is predictable. In solo queue there are no fixed teams and
matchmaking pairs players of similar skill, so the draft is the main pre-game signal left, and it is expected to be
small (draft-only models typically reach about 52–56% accuracy).

## Data

22,508 Korean (kr) Master, Grandmaster and Challenger ranked solo games played 26 Sep – 26 Oct 2026, patches 16.19
(2,094), 16.20 (11,912) and 16.21 (8,502). Blue side won 49.2%. Collected 26 Oct 2026 by walking 2,637 of the
11,000 Master+ players from the top of the ladder.

Collected with [`scripts/ranked/collect.py`](../scripts/ranked/collect.py) from the official Riot API
(league-v4 for Master+ players, match-v5 for their ranked games). Only champions, roles, bans, patch, duration and the
winner are stored; no player names or IDs.

## Method

Chronological split (60% train, 20% validation, 20% test). Logistic regression on champion-in-role indicators
(+1 blue, -1 red) with a blue-side term and side-swap augmentation; regularisation chosen on validation log loss.
Compared against the blue-side win rate and smoothed champion win rates, with a bootstrap interval.
Code: [`scripts/ranked/train.py`](../scripts/ranked/train.py).

## Results

Time split: 13,504 train / 4,502 validation / 4,502 test. The test set is the newest games (23–26 Oct 2026, all
patch 16.21), evaluated once. Regularisation C = 0.01 was chosen on validation log loss.

| Model | Accuracy | Log loss | Brier |
|---|---:|---:|---:|
| Blue-side rate | 51.18% | 0.6929 | 0.2499 |
| Champion win rates (smoothed) | 53.02% | 0.6974 | 0.2519 |
| Draft model | 53.33% | 0.6917 | 0.2493 |

- Log-loss improvement vs champion win rates: **+0.0033 to +0.0079** (95%, match bootstrap): the regularised model
  is better calibrated than raw win rates.
- Log-loss improvement vs the blue-side rate: **−0.0028 to +0.0050**: not distinguishable from no model.
- Conclusion: in matchmade high-rank games the draft alone predicts very little. That is a result, not a bug.

Full numbers: [`scripts/ranked/REPORT.md`](../scripts/ranked/REPORT.md), [`scripts/ranked/report.json`](../scripts/ranked/report.json).

## Limitations

- One server (Korea), one month, three patches; the test patch (16.21) is newer than most training games.
- The best regularisation was at the edge of the searched range (C = 0.01); a wider search is the first thing to try
  on new data. It was not re-tuned after seeing the test result.
- No player information (champion experience, recent form), which is where most remaining signal likely is.
- Collection walked only the top 2,637 players of the ladder.

## Next steps

1. Collect another week of games as a fresh test set, untouched until the end.
2. Wider regularisation search and patch-aware champion strength on the existing data.
3. Add player champion experience (games on the champion) from match history.
4. Only then decide whether Ranked mode goes into the app.
