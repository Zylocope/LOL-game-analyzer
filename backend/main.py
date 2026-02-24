from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .services import get_team_stats, get_player_stats, get_db_connection, get_all_teams, get_matchup_stats, get_composition_analysis
import joblib
import pandas as pd
import numpy as np
import os
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Load V4 Model (XGBoost + Elo + Roles)
MODEL_PATH = os.path.join(BASE_DIR, "match_predictor_v4.pkl")
RATINGS_PATH = os.path.join(BASE_DIR, "team_ratings.json")
TAGS_PATH = os.path.join(BASE_DIR, "../data/championTags.ts")

# Global State
model_data = None
model = None
elo_map = {}
role_map = {}
class_map = {}

# --- LOADERS ---

def load_champion_meta():
    print("📜 Parsing Champion Roles & Classes...")
    if not os.path.exists(TAGS_PATH): return {}, {}
    with open(TAGS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'=\s*({.*})', content, re.DOTALL)
    if not match: return {}, {}
    
    json_str = match.group(1)
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str) # clean trailing commas
    
    try:
        data = json.loads(json_str)
    except:
        return {}, {}

    r_map = {}
    c_map = {}
    for name, details in data.items():
        # Normalized key
        norm_key = name.lower().replace(" ", "").replace("'", "").replace(".", "")
        roles = [r.lower() for r in details.get('roles', [])]
        r_map[norm_key] = roles
        r_map[name.lower()] = roles # backup
        
        classes = [c.lower() for c in details.get('classes', [])]
        c_map[norm_key] = classes
        c_map[name.lower()] = classes
        
    return r_map, c_map

def load_team_elo():
    print("🏆 Loading Team Ratings...")
    if not os.path.exists(RATINGS_PATH): return {}
    with open(RATINGS_PATH, 'r') as f:
        ratings_list = json.load(f)
    
    e_map = {}
    for entry in ratings_list:
        norm_name = entry['team'].lower().replace(" ", "")
        e_map[norm_name] = entry['rating']
        e_map[entry['team']] = entry['rating']
    return e_map

# Initialize Resources
try:
    if os.path.exists(MODEL_PATH):
        # Try loading with joblib first
        model_data = joblib.load(MODEL_PATH)
        # Handle if it was saved as dict or raw model
        if isinstance(model_data, dict) and 'model' in model_data:
            model = model_data['model']
        else:
            model = model_data
        print(f"✅ Loaded V4 Model")
    else:
        raise FileNotFoundError("Model missing")
except Exception as e:
    print(f"⚠️ Model load failed ({e}). Retraining locally to fix version mismatch...")
    try:
        # DYNAMIC RETRAINING ON STARTUP
        # This ensures the model is compatible with the current OS/Python/Numpy
        from .train_v4_synthetic import train_model_v4
        model = train_model_v4() 
        print("✅ Model retrained and loaded successfully.")
    except Exception as train_err:
        print(f"❌ Retraining failed: {train_err}")
        print("⚠️ Falling back to Heuristic Mode (Elo + Role Logic)")
        model = None

elo_map = load_team_elo()
role_map, class_map = load_champion_meta()

# --- API ---

@app.get("/")
def read_root():
    return {"status": "Nexus Sight API is running (V4 Brain)"}

@app.get("/api/teams")
def api_all_teams():
    # 1. Load Ratings (Source of Truth for Rank)
    all_ratings = []
    if os.path.exists(RATINGS_PATH):
        with open(RATINGS_PATH, 'r') as f:
            all_ratings = json.load(f)
            
    # 2. Get Filtered List from DB (Smart Filter)
    filtered_teams_list = get_all_teams()
    filtered_set = set(filtered_teams_list)

    # 3. Intersection
    final_list = [t for t in all_ratings if t['team'] in filtered_set]
    
    # 4. Safety
    rated_names = {t['team'] for t in final_list}
    for team_name in filtered_teams_list:
        if team_name not in rated_names:
             final_list.append({"rank": 999, "team": team_name, "rating": 1000, "region": "Unknown"})
             
    # 5. Sort by Rating
    final_list.sort(key=lambda x: x['rating'], reverse=True)

    return {"teams": final_list}

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

@app.get("/api/matchup/{my_champ}/vs/{enemy_champ}/role/{role}")
def api_matchup_stats(my_champ: str, enemy_champ: str, role: str):
    data = get_matchup_stats(my_champ, enemy_champ, role)
    if not data: return {"found": False}
    return {"found": True, "data": data}

@app.post("/api/predict")
def predict_match(match_data: dict):
    """
    V4 PREDICTION:
    Uses Elo Diff + Role Diff.
    """
    blue_name = match_data.get("blueTeam", "Blue")
    red_name = match_data.get("redTeam", "Red")
    blue_draft = match_data.get("blueDraft", [])
    red_draft = match_data.get("redDraft", [])
    
    # 1. Elo Diff
    elo1 = elo_map.get(blue_name.replace(" ", ""), elo_map.get(blue_name, 1200))
    elo2 = elo_map.get(red_name.replace(" ", ""), elo_map.get(red_name, 1200))
    elo_diff = elo1 - elo2
    
    # 2. Role Diff & Counter Analysis
    POSITIONS = ['top', 'jungle', 'mid', 'bot', 'support']
    # The "Big Hitters" + "Sub-Class Trinity"
    TRACKED_CLASSES = [
        'marksman', 'tank', 'support', 
        'fighter', 'mage', 'assassin',
        'catcher', 'vanguard', 'enchanter'
    ]
    
    # Import services to access Matchup Matrix
    from .services import get_matchup_stats

    def get_role_score(draft, enemy_draft):
        score = 0
        off_role_detected = False
        details = []
        counter_warnings = []
        class_counts = {c: 0 for c in TRACKED_CLASSES}
        total_counter_score = 0.0
        
        for i, champ in enumerate(draft):
            if i >= 5: break
            if not champ: continue
            
            # A. Off-Role Check
            c_norm = champ.lower().replace(" ", "").replace("'", "").replace(".", "")
            pos_req = POSITIONS[i]
            valid = role_map.get(c_norm, [])
            
            if not valid:
                val = 0.0
            elif pos_req in valid:
                val = 1.0
            else:
                val = -1.0
                off_role_detected = True
                details.append(f"{champ} in {pos_req}")
            score += val
            
            # Class Counting
            my_classes = class_map.get(c_norm, [])
            for cls in my_classes:
                if cls in class_counts:
                    class_counts[cls] += 1

            # B. Counter Check (Am I being camped?)
            counters = []
            
            # 1. Lane Counter (Matrix)
            lane_opp = enemy_draft[i] if i < len(enemy_draft) else None
            if lane_opp:
                stats = get_matchup_stats(champ, lane_opp, pos_req)
                if stats:
                    total_counter_score += (stats['winRate'] - 50.0)
                    if stats['type'] == 'disadvantage':
                        counters.append(f"{POSITIONS[i].capitalize()} (Lane)")

            # 2. Cross-Role Counter (Class Logic)
            is_squishy = any(c in ['mage', 'marksman', 'enchanter', 'artillery'] for c in my_classes)
            is_melee = any(c in ['fighter', 'tank', 'slayer'] for c in my_classes)
            
            for j, enemy_champ in enumerate(enemy_draft):
                if not enemy_champ: continue
                if i == j: continue 
                
                e_norm = enemy_champ.lower().replace(" ", "").replace("'", "").replace(".", "")
                e_classes = class_map.get(e_norm, [])
                
                is_threat = False
                
                if is_squishy:
                    if any(c in ['assassin', 'diver', 'catcher', 'vanguard'] for c in e_classes):
                        is_threat = True
                if is_melee:
                    if any(c in ['control', 'disengage', 'warden'] for c in e_classes):
                        is_threat = True
                        
                if is_threat:
                    counters.append(POSITIONS[j].capitalize())
            
            if len(counters) >= 3:
                counter_warnings.append(f"⚠️ {champ} is countered by {', '.join(counters)}")

        return score, off_role_detected, details, counter_warnings, class_counts, total_counter_score

    t1_role_score, t1_bad, t1_details, t1_counters, t1_classes, t1_c_score = get_role_score(blue_draft, red_draft)
    t2_role_score, t2_bad, t2_details, t2_counters, t2_classes, t2_c_score = get_role_score(red_draft, blue_draft)
    
    role_diff = t1_role_score - t2_role_score
    
    # 3. Predict (Pure ML V4)
    blue_win_pct = 50.0 
    
    if model:
        try:
            # Create input vector matching training columns
            input_data = {'elo_diff': elo_diff, 'role_diff': role_diff, 'counter_score': t1_c_score}
            for cls in TRACKED_CLASSES:
                input_data[f'diff_{cls}'] = t1_classes[cls] - t2_classes[cls]
                
            input_vector = pd.DataFrame([input_data])
            probs = model.predict_proba(input_vector)[0]
            blue_win_pct = probs[1] * 100
        except Exception as e:
            print(f"⚠️ ML Prediction failed: {e}")
            # Only fallback if model crashes
            blue_win_pct = 50.0 + (elo_diff / 20) + (role_diff * 5)
    else:
        # Fallback if model file missing
        blue_win_pct = 50.0 + (elo_diff / 20) + (role_diff * 5)

    # 4. Final Polish (Rounding)
    # Ensure 100.0 sum
    blue_win_pct = round(blue_win_pct, 1)
    red_win_pct = round(100.0 - blue_win_pct, 1)
    
    # Clamp to avoid 101% or -5%
    blue_win_pct = max(1.0, min(99.0, blue_win_pct))
    red_win_pct = round(100.0 - blue_win_pct, 1) # Recalculate red to ensure sum match

    # 5. Factors Explanation
    factors = []
    
    if abs(elo_diff) > 50:
        leader = blue_name if elo_diff > 0 else red_name
        factors.append(f"🏆 Power Gap: {leader} (+{abs(elo_diff):.0f} Elo)")
        
    if t1_bad:
        factors.append(f"⚠️ OFF-ROLE: {blue_name} ({', '.join(t1_details)})")
    if t2_bad:
        factors.append(f"⚠️ OFF-ROLE: {red_name} ({', '.join(t2_details)})")
        
    # Counter Warnings (New)
    # factors.extend(t1_counters) <- Remove flat add
    # factors.extend(t2_counters)
        
    if not t1_bad and not t2_bad:
        if role_diff > 1:
            factors.append(f"✅ Composition: {blue_name} role advantage.")
        elif role_diff < -1:
            factors.append(f"✅ Composition: {red_name} role advantage.")

    return {
        "blueWin": blue_win_pct,
        "redWin": red_win_pct,
        "factors": factors,
        "blueWarnings": t1_counters, # New explicit field
        "redWarnings": t2_counters   # New explicit field
    }
