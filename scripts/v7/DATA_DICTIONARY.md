# Nexus Sight v7 data dictionary and provenance

Source: Oracle's Elixir official yearly CSVs, linked by its public downloads page to Google Drive. `sources.json` records file IDs; development and holdout manifests record retrieval time and SHA-256. Only 2018–2025 files enter the development database. The 2026 snapshot is opaque until `final.py` claims the single final run.

## Raw fields retained

| Field | Meaning | Permitted use |
|---|---|---|
| gameid | Source game identifier | Identity, grouping, joins; never numeric model input |
| date | Source recorded game timestamp, parsed as UTC | Chronological order; may not equal exact draft start |
| side | Blue or Red | Team separation and pre-game side context |
| position | top/jng/mid/bot/sup | Canonical role order; jng/sup normalized |
| teamname, teamid | Team identity | Team ratings and same-day series linking |
| playerid, playername | Stable player ID and display alias | Player ratings and comfort; IDs carry across teams |
| champion | Picked champion | Draft features after picks are known |
| patch | Game patch | Bayesian smoothed patch-role performance; numeric 15.1 normalized to 15.10 |
| league, year, split, playoffs | Competition metadata | Fixed reporting cohort, region and temporal filtering |
| game | Source game ordinal within a match | Pre-game ordinal only; never infer best-of from final ordinal |
| firstPick | Source blue-side first-pick indicator | Known draft context with a missing-data indicator |
| result | Win/loss label | Training labels or updating history after availability; never an input feature |
| gamelength | Recorded seconds | Result availability only: max(2h, duration+15m) after timestamp; never a model feature |

All other raw statistics (kills, gold, objectives, in-game leads, etc.) are excluded from this benchmark database and from model inputs.

## Reporting and rating cohorts

Five reporting families are LCK, LPL, LEC (including EU LCS), North America (LCS, NA LCS, LTA N and cross-conference LTA), and International (MSI, WLDs/W/Worlds). This explicitly includes Worlds per user preference. Other international events such as FST/EWC are outside the preregistered cohort. LTA S is rating-only under Brazil.

Secondary rating-only sources: LCKC/LCK CL/CK, LDL, PCS/LCP/LMS, VCS, CBLOL/LTA S, LJL. Secondary games do not contribute model training labels, champion patch rates, player/champion comfort, or recent-form statistics. They do update team/player/region rating state and rating-internal last-played time. Match-context rest is computed from primary-cohort games only.

A game needs ten player rows, distinct champions, five canonical roles per side, consistent team/result/date fields, and complementary outcomes. Rejected game counts are reported. No deduplication or exclusions are chosen based on predictive performance.

## Features

- v6 feature group: unchanged Elo/player Elo, weighted ten-game form, roster overlap, patch residual strength, patch sample coverage, player/champion comfort and smoothed lane outcomes.
- Broad rating group: secondary-inclusive team/player Elo, international-derived regional offset, player TrueSkill means/deviations, approximate player Glicko-2 means/RDs.
- Match context: past-only same-day series score if all preceding results are available; source game ordinal; first-pick with missingness; roster-change flag; days since last available primary-cohort game; 2025+ fearless-era proxy.
- Best-of: explicit Bo1/Bo3/Bo5 columns and a known-format flag. The yearly source lacks authoritative scheduled formats; all are currently masked unknown. This is missing information, not a claim that Bo features were successfully recovered.

Glicko-2 player updates use a head-to-head mean-opponent-team approximation. TrueSkill updates actual 5v5 groups. Region assignment is learned from earlier domestic participation; offsets update only when previously assigned regions meet at MSI/Worlds. Unknown regions have neutral offsets. Glicko/TrueSkill uncertainty is a model feature; its parameters use documented library defaults, with season uncertainty inflation.

## Temporal safeguards

Features are computed before pushing the current outcome. Only results with availability strictly earlier than the current timestamp enter history. Pending December outcomes remain pending at the 2026 boundary. No result-duration or label value is provided to any model as a feature. Timestamps, final-game duration and availability remain approximate and may differ from actual broadcast/draft timing.

No format is inferred from the observed final number of series games. Same-day team-pair linking can miss overnight series or misidentify unusual rematches. The fearless flag is an era proxy; because estimator fitting stops at 2024, its 2025+ effect cannot be learned in this strict protocol.

## Reproduction

Run commands from the repository root using Python 3.12+:

```powershell
python -m pip install -r scripts/v7/requirements.txt
python -m scripts.v7.lock
python -m scripts.v7.download
python -m scripts.v7.data
python -m unittest scripts.v7.tests -v
python -m scripts.v7.train
python -m scripts.v7.freeze
# Exactly once after all source/model checks; permanent claim forbids another attempt:
python -m scripts.v7.final
```

Raw downloads and fitted bundles are local and Git-ignored. Upstream Drive files can change; manifests reject mismatching bytes. Exact reproduction requires retaining these raw snapshots. `data.py` refuses to replace an existing development database; the v6 database is never rebuilt or changed.

`freeze.json` fingerprints source code, configuration, database, manifests, fitted estimators and calibrators. `final_run.claim` is created exclusively before parsing the sealed snapshot. A failure retains the claim and writes an error record; there is no automatic retry. The final evaluator only emits predetermined reports, predictions, plot and README results. No subsequent model/code changes are permitted.
