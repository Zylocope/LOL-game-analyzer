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
