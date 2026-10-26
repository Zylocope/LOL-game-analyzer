# Nexus Sight: Team Tier Calculation Strategy

## The Goal
Assign a numerical "Power Rating" to every team in the database so the model knows that **T1 (LCK)** beating **Gen.G (LCK)** means more than beating a minor region team.

## The Metrics
We will use a weighted combination of three metrics to generate a **Global Elo Score** (1000 - 3000).

### 1. The Regional Coefficient (The Base)
Not all wins are equal. We must anchor teams by their region's strength (historically).
*   **Tier S (LCK / LPL):** Base 1500
    *   *Why?* They win 90% of Worlds titles.
*   **Tier A (LEC / LCS):** Base 1300
    *   *Why?* Competitive, but consistently lose to Tier S in finals.
*   **Tier B (PCS / VCS / LLA / CBLOL):** Base 1100
    *   *Why?* Minor regions, often struggle in group stages.

### 2. The Win/Loss Elo (The Curve)
We run a standard Elo calculation over the 24,000 matches.
*   **K-Factor (Volatility):** 32 (Standard)
*   **Logic:** If `Tier B` beats `Tier A`, they gain MASSIVE points. If `Tier S` beats `Tier B`, they gain almost nothing.
*   *Why?* This allows a super-team from a minor region (like PSG Talon) to climb if they genuinely beat major teams.

### 3. The "Dominance" Factor (Gold Diff)
A 50-minute struggle win is different from a 15-minute stomp.
*   **Metric:** Average `GoldDiff@15` over the last 10 games.
*   **Adjustment:** +1 point for every +10 Gold lead.
*   *Why?* T1 often has huge gold leads. This captures "Peak Performance" vs "Lucky Wins."

## The Proposed Tier List (Snapshot)
After running this logic, we expect numbers like:

| Rank | Team | Est. Score | Reason |
| :--- | :--- | :--- | :--- |
| **S+** | **Gen.G / T1 / BLG** | **2400+** | High base + consistently beating other S-tiers + huge gold leads. |
| **S** | **HLE / TES / JDG** | **2200+** | Strong region, high winrate, occasionally drop games to S+. |
| **A+** | **G2 Esports** | **1900+** | The King of the West. Beats all A-tiers, fights S-tiers. |
| **A** | **FNC / TL / C9** | **1700+** | Solid major region teams. |
| **B** | **PSG / GAM** | **1400+** | Top of minor regions. |
| **C** | **Bottom Tier (Major)** | **1200** | Losing teams in major regions (still better than randoms). |

## Implementation Plan
1.  **Script:** `calculate_team_elo.py`
2.  **Input:** Iterates through matches chronologically (2018 -> 2025).
3.  **Output:** A JSON file `{ "T1": 2450, "Gen.G": 2480 ... }` to feed the prediction model.

Shall I write the Elo calculator script?
