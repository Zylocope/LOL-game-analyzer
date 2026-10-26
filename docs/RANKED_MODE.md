# Ranked mode (in progress)

Draft-only win prediction for high-rank solo queue (Master, Grandmaster, Challenger).

## Why it is a separate model

In pro play, team strength (Elo) explains most of what is predictable. In solo queue there are no fixed teams and
matchmaking pairs players of similar skill, so the draft is the main pre-game signal left, and it is expected to be
small (draft-only models typically reach about 52–56% accuracy).

## Data

_To be added after collection: servers, patches, number of matches, date range._

Collected with [`scripts/ranked/collect.py`](../scripts/ranked/collect.py) from the official Riot API
(league-v4 for Master+ players, match-v5 for their ranked games). Only champions, roles, bans, patch, duration and the
winner are stored; no player names or IDs.

## Method

Chronological split (60% train, 20% validation, 20% test). Logistic regression on champion-in-role indicators
(+1 blue, -1 red) with a blue-side term and side-swap augmentation; regularisation chosen on validation log loss.
Compared against the blue-side win rate and smoothed champion win rates, with a bootstrap interval.
Code: [`scripts/ranked/train.py`](../scripts/ranked/train.py).

## Results

_To be added._

| Model | Accuracy | Log loss | Brier |
|---|---:|---:|---:|
| Blue-side rate | | | |
| Champion win rates | | | |
| Draft model | | | |

## Limitations

_To be added with the results._ Known in advance: one server and a few patches at a time; the free development
key limits collection speed; player skill on the champion is not used.
