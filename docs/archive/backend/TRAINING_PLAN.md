# Nexus Sight: Model Training Strategy

## 1. The Problem
- **Current Model:** Simple Logistic Regression.
- **Features:** Only uses Team Gold Difference (GD@15) and a basic "Draft Score" (avg winrate of champs).
- **Flaw:** It relies 90% on "Who is the better team historically?" (Team Identity) and ignored the draft context. Putting Yuumi in the Jungle doesn't hurt the score because "T1 is still T1."

## 2. The Solution: "Context-Aware" Modeling
We need a model that penalizes **bad decisions**, not just rewards good teams.

### Phase A: Feature Engineering (The Ingredients)
We need to calculate these NEW features for every match in our DB:
1.  **Role Proficiency:** Does this player actually play this champ? (Faker on Azir = 1.0, Faker on Yuumi = 0.1).
2.  **Composition Fit:** 
    - **Damage Distribution:** 4 AP champs? Penalty.
    - **Role Meta:** Yuumi as Jungle? Massive penalty (Winrate < 30%).
3.  **Synergy Pairs:** Specific bonuses for pairs with >55% WR together (Lucian/Nami, Vi/Ahri).

### Phase B: Data Enrichment (Farming)
Our `player_stats` table has 24,000 matches. We need to create a **Training Set** where we:
1.  **Calculate the Stats:** For every historic match, calculate what the team's stats *were* entering that match.
2.  **Negative Sampling (The Secret Weapon):** 
    - The model has only seen "Real Drafts" (Pro teams don't pick Yuumi Jungle).
    - We must **synthesize fake "Bad Drafts"** and label them as losses (or low probability).
    - *Example:* Take a real T1 win, swap Oner's Lee Sin for Yuumi, and tell the model "This version of T1 would lose." This teaches the model to fear bad drafts.

### Phase C: Model Upgrade
- **Algorithm:** Switch from Logistic Regression to **XGBoost** or **Gradient Boosting**. It handles non-linear interactions (like "High Gold Diff is good, BUT not if you have no tank") better.

## 3. Step-by-Step Plan
1.  **Create `feature_engineer.py`:** A script to calculate the new complex features.
2.  **Create `training_set_builder.py`:** Generates the dataset, including the "Negative Samples" (Bad Drafts).
3.  **Train `match_predictor_v3.pkl`:** Train XGBoost on this enriched data.
4.  **Validate:** Run the "Yuumi Test" (Swap a champ and see if win % drops).

Shall we start with **Step 1: Feature Engineering**?
