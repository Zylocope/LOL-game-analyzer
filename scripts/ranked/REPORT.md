# Ranked mode (draft only): evaluation

22,508 Master+ solo queue matches. Time split: 13,504 train / 4,502 validation / 4,502 test (2026-10-23 to 2026-10-26).

| Model | Accuracy | Log loss | Brier |
|---|---:|---:|---:|
| Blue-side rate | 51.18% | 0.6929 | 0.2499 |
| Champion win rates | 53.02% | 0.6974 | 0.2519 |
| Draft model | 53.33% | 0.6917 | 0.2493 |

Log-loss improvement vs champion win rates: 95% interval +0.0033 to +0.0079 (match bootstrap).
Regularisation C=0.01 chosen on validation log loss.

Draft-only prediction in matchmade games is expected to be weak (about 52-56% accuracy):
matchmaking makes both teams similar in skill, so the draft is a small part of the outcome.
