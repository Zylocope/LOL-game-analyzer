<<<<<<< HEAD
# NEXUS SIGHT
### Predictive Draft Analysis Engine for League of Legends Esports

![Status](https://img.shields.io/badge/Status-Production_Ready-0052cc?style=flat-square)
![Model](https://img.shields.io/badge/Model-XGBoost_Classifier-orange?style=flat-square)
![Accuracy](https://img.shields.io/badge/Validation_Accuracy-71.0%25-success?style=flat-square)

Nexus Sight is a predictive analytics platform for League of Legends esports. It utilizes a gradient boosting model trained on professional match data to evaluate draft compositions, quantifying win probability based on skill differential, lane matchups, and structural role integrity.

---

## Core Capabilities

### 1. Predictive Modeling Engine
The system employs an **XGBoost Classifier** trained on 3,000+ competitive matches (LCK, LPL, LEC, LCS, Worlds 2022-2024). Unlike simple win-rate aggregators, it weighs multiple distinct feature vectors to determine game outcome:

*   **Counter Score (56% Importance):** Aggregated lane-specific matchup advantages derived from a historical matrix of 8,900+ unique matchups.
*   **Skill Differential (35% Importance):** Custom Elo rating system adjusted for regional strength disparity (e.g., LCK vs LCS weighting).
*   **Compositional Archetypes (9% Importance):** Feature engineering that detects structural advantages (e.g., "Catch" compositions vs "Protect" compositions) via sub-class density analysis (Vanguards, Enchanters, Marksmen).

### 2. Global Elo System
A custom ranking engine tracks team strength over time, anchoring ratings by regional coefficients.
*   **Active Filtering:** Automatically excludes disbanded organizations, focusing on active franchises (>250 games or active in current season).
*   **Dynamic Updating:** Ratings adjust match-by-match based on opponent strength.

### 3. Draft Simulation Interface
A React-based frontend designed for analysts and coaches.
*   **Real-Time Inference:** Predictions update instantly ( < 100ms ) as champions are selected.
*   **Threat Detection:** Algorithmic identification of specific high-threat counters (e.g., "Viktor is countered by 3+ enemy champions").
*   **Draft Integrity Checks:** Flags off-role selections or composition imbalances (e.g., "No Frontline," "Full Magic Damage").

---

## Technical Architecture

### Backend
*   **Runtime:** Python 3.11
*   **Framework:** FastAPI
*   **ML Stack:** Scikit-Learn, XGBoost, Pandas, NumPy
*   **Data Storage:** SQLite (Optimized for read-heavy analytical queries)
*   **Key Services:**
    *   `train_v4_synthetic.py`: Model training pipeline with feature extraction.
    *   `mine_counters.py`: Matrix generation script for matchup data.
    *   `main.py`: Inference API and business logic.

### Frontend
*   **Framework:** React 18 (Vite)
*   **Language:** TypeScript
*   **State Management:** React Hooks (Custom `useMatchups` logic)
*   **Styling:** TailwindCSS (Custom configuration)

---

## Installation & Deployment

### Prerequisites
*   Node.js (v18+)
*   Python (v3.10+)

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pandas scikit-learn xgboost numpy shap

# Run the API
uvicorn main:app --reload
```

### 2. Frontend Setup
```bash
# In project root
npm install
npm run dev
```

### 3. Model Retraining (Optional)
To regenerate the predictive model based on the latest database entries:
```bash
python backend/train_v4_synthetic.py
```

---

## Data Methodology

Feature importance analysis (Gini Impurity) reveals the following hierarchy in professional play outcomes:
1.  **Counter Score:** The sum of lane-specific win rate deltas is the primary determinant of draft success.
2.  **Elo Differential:** Team skill disparity remains a significant predictor regardless of composition.
3.  **Support & Marksman Density:** The presence of specific utility and damage classes correlates more strongly with victory than generic Tank metrics.
=======
#  NEXUS SIGHT
### Predictive Draft Analysis Engine for League of Legends Esports

![Nexus Sight Banner](https://img.shields.io/badge/Status-Active_Development-gold?style=for-the-badge) ![Python](https://img.shields.io/badge/Backend-FastAPI-blue?style=for-the-badge) ![React](https://img.shields.io/badge/Frontend-React_Vite-cyan?style=for-the-badge) ![Accuracy](https://img.shields.io/badge/Model_Accuracy-70.8%25-green?style=for-the-badge)

**Nexus Sight** is a data science project that brings moneyball-style analytics to League of Legends drafting. Instead of relying on gut feeling, it uses a trained machine learning model (Logistic Regression / XGBoost) on over **24,000 professional matches** to predict win probabilities based on draft composition, team economy, and historical mastery.

---

##  Key Features

### The Prediction "Brain"
- **70%+ Accuracy:** Trained on 8 years of pro play data (LCK, LPL, LEC, LCS, Worlds).
- **Economy & Objectives:** Doesn't just look at champions; it factors in a team's historical **Gold@15**, **Dragon Control Rate**, and **Aggression Score (CKPM)**.
- **Synergy Calculation:** Detects high-winrate duos (Mid/Jungle, Bot/Support) and adjusts win probability dynamically.

### The "Global Elo" System
- **Custom Ranking Engine:** We don't just use winrates. We built a custom weighted Elo system that anchors teams by region strength (e.g., LCK wins count more than minor region wins).
- **Smart Filtering:** Automatically filters out dead/disbanded teams, keeping only "Veterans" (>250 games) and "Active Rising Stars" (Played in 2024+).
- **Power Rankings:** See live ratings for teams like **Gen.G (2096)** vs **T1 (1936)** vs **G2**.

### Esports-Grade UI
- **Interactive Draft Board:** Full Pick/Ban simulation with champion search and role filtering.
- **Dynamic Lobby:** Select teams with their real logos and rosters (synced to latest data).
- **Live Analysis:** As you pick champions, the engine calculates:
  - **Damage Profile:** (e.g., "Heavy AD" or "Balanced")
  - **Matchup Winrates:** Historical head-to-head stats for specific lanes.

---

## Architecture

### Backend (`/backend`)
- **Framework:** FastAPI (Python)
- **Database:** SQLite (`nexus_sight.db`) - Optimized relational schema for match history.
- **ML Model:** Scikit-Learn (moving to XGBoost).
- **Services:**
  - `calculate_team_elo.py`: Runs the Elo simulation.
  - `services.py`: Handles complex SQL queries for matchups and synergy.

### Frontend (`/components`)
- **Framework:** React + Vite + TypeScript.
- **Styling:** TailwindCSS with a custom "Esport Dark" theme.
- **Icons:** Lucide-React.

---

## Quick Start

### 1. Prerequisites
- Node.js (v18+)
- Python (v3.10+)

### 2. Setup Backend
```bash
cd backend
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install fastapi uvicorn pandas scikit-learn sqlite3

# Run the API
uvicorn main:app --reload
>>>>>>> ee480c39171bf1d97b798ae711f30868528dd260
