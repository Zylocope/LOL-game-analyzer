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
