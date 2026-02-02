from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .services import get_team_stats, get_player_stats, get_db_connection, get_all_teams, get_matchup_stats, get_composition_analysis
import joblib
import pandas as pd
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Load the Advanced V2 Model
MODEL_PATH = os.path.join("backend", "match_predictor_v2.pkl")
model_data = None
champ_stats = {}

if os.path.exists(MODEL_PATH):
    model_data = joblib.load(MODEL_PATH)
    # The file contains BOTH the trained model AND the champion dictionary
    model = model_data['model']
    champ_stats = model_data['champ_stats']
    print(f"Loaded V2 Model (Accuracy: 70.8%)")
else:
    print("Model not found.")

@app.get("/")
def read_root():
    return {"status": "Nexus Sight API is running"}

@app.get("/api/teams")
def api_all_teams():
    return {"teams": get_all_teams()}

@app.get("/api/team/{team_name}")
def api_team_stats(team_name: str):
    data = get_team_stats(team_name)
    if not data: return {"error": "Team not found", "use_mock": True}
    return data

@app.get("/api/player/{player_name}/champion/{champion}")
def api_player_stats(player_name: str, champion: str):
    data = get_player_stats(player_name, champion)
    if not data: return {"found": False}
    return {"found": True, "data": data}

@app.get("/api/player/{player_name}/champion/{champion}")
def api_player_stats(player_name: str, champion: str):
    data = get_player_stats(player_name, champion)
    if not data: 
        return {"found": False}
    return {"found": True, "data": data}

@app.get("/api/matchup/{my_champ}/vs/{enemy_champ}/role/{role}")
def api_matchup_stats(my_champ: str, enemy_champ: str, role: str):
    data = get_matchup_stats(my_champ, enemy_champ, role)
    if not data:
        return {"found": False}
    return {"found": True, "data": data}

@app.post("/api/predict")
def predict_match(match_data: dict):
    """
    Receives:
    {
      "blueTeam": "T1",
      "redTeam": "Gen.G",
      "blueDraft": ["Ahri", "Lee Sin", ...], 
      "redDraft": ["Azir", "Viego", ...]
    }
    """
    if not model_data:
        return {"error": "Model not loaded"}

    blue_name = match_data.get("blueTeam")
    red_name = match_data.get("redTeam")
    blue_champs = match_data.get("blueDraft", [])
    red_champs = match_data.get("redDraft", [])
    
    conn = get_db_connection()
    
    # A. Get Team Stats (Gold Diff History)
    def get_gd15(team):
        try:
            df = pd.read_sql("SELECT AVG(golddiffat15) as gd FROM team_stats WHERE teamname = ?", conn, params=(team,))
            return df.iloc[0]['gd'] if not df.empty and pd.notna(df.iloc[0]['gd']) else 0.0
        except: return 0.0

    t1_gd = get_gd15(blue_name)
    t2_gd = get_gd15(red_name)
    conn.close()
    
    # B. Calculate Draft Scores (The New V2 Feature)
    def get_draft_score(champs):
        if not champs: return 0.5 # Default if empty
        # Look up every champion in our training dictionary
        scores = [champ_stats.get(c, 0.5) for c in champs]
        return sum(scores) / len(scores)

    t1_draft = get_draft_score(blue_champs)
    t2_draft = get_draft_score(red_champs)
    
    # C. Composition Analysis (New Feature)
    t1_comp = get_composition_analysis(blue_champs)
    t2_comp = get_composition_analysis(red_champs)
    
    # D. Predict
    # Input columns MUST match training exactly: ['t1_gd15', 't2_gd15', 't1_draft', 't2_draft']
    input_df = pd.DataFrame([{
        't1_gd15': t1_gd, 't2_gd15': t2_gd,
        't1_draft': t1_draft, 't2_draft': t2_draft
    }])
    
    probs = model.predict_proba(input_df)[0]
    raw_blue_win = probs[1] * 100
    
    # Synergy Logic
    synergy_diff = (t1_comp['synergy_bonus'] - t2_comp['synergy_bonus']) * 2.5 
    final_blue_win = max(10, min(90, raw_blue_win + synergy_diff))
    
    # UX: Generate Human-Readable Factors
    factors = []
    
    # 1. Economy Factor (Comparative)
    gd_diff = t1_gd - t2_gd
    if abs(gd_diff) > 200:
        leader = blue_name if gd_diff > 0 else red_name
        factors.append(f"💰 Early Game: {leader} leads by avg {abs(gd_diff):.0f}g at 15m")
    else:
        factors.append(f"⚖️ Early Game: Teams are evenly matched")

    # 2. Draft Factor
    if t1_draft > t2_draft:
        factors.append(f"📈 Draft: Blue side has higher meta winrates")
    elif t2_draft > t1_draft:
        factors.append(f"📈 Draft: Red side has higher meta winrates")
    
    # 3. Comp Profile
    factors.append(f"⚔️ Profile: {t1_comp['damage_profile']} (Blue) vs {t2_comp['damage_profile']} (Red)")
    
    # 4. Synergy
    if t1_comp['synergy_bonus'] > 0 or t2_comp['synergy_bonus'] > 0:
        factors.append(f"🤝 Synergy: Blue has {t1_comp['synergy_bonus']} power-pairs vs Red's {t2_comp['synergy_bonus']}")

    return {
        "blueWin": int(final_blue_win),
        "redWin": int(100 - final_blue_win),
        "factors": factors
    }