from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .services import (
    get_team_stats,
    get_player_stats,
    get_db_connection,
    get_all_teams,
    get_matchup_stats,
    get_composition_analysis,
    get_champion_pro_stats,
)
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
CHAMP_STATS_PATH = os.path.join(BASE_DIR, "champion_stats_pro.json")
MIN_PRO_GAMES_FOR_CONFIDENT = 50

# Global State
model_data = None
model = None
elo_map = {}
role_map = {}
class_map = {}
champ_meta_map = {}
champ_games_map = {}
champ_global_avg = 0.5

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

def load_champion_strengths(alpha: float = 50.0):
    """
    Loads champion-level pro meta strength from champion_stats_pro.json.
    Returns:
        meta_map: normalized champ name -> smoothed winrate (0-1)
        global_avg: global average pro winrate (0-1)
        games_map: normalized champ name -> pro games count
    """
    if not os.path.exists(CHAMP_STATS_PATH):
        print("⚠️ Champion stats file not found, skipping champion strength features.")
        return {}, 0.5, {}
    
    with open(CHAMP_STATS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    total_games = 0
    weighted_wins = 0.0
    for stats in data.values():
        games = max(0, stats.get("pro_games", 0))
        wr = stats.get("pro_win_rate", None)
        if wr is None:
            continue
        total_games += games
        weighted_wins += games * (wr / 100.0)
    
    global_avg = (weighted_wins / total_games) if total_games > 0 else 0.5
    
    meta_map = {}
    games_map = {}
    for name, stats in data.items():
        games = max(0, stats.get("pro_games", 0))
        raw_wr = stats.get("pro_win_rate", None)
        if raw_wr is None:
            base_wr = global_avg
        else:
            base_wr = raw_wr / 100.0
        
        denom = games + alpha
        if denom > 0:
            smoothed = (base_wr * games + alpha * global_avg) / denom
        else:
            smoothed = global_avg
        
        norm_key = name.lower().replace(" ", "").replace("'", "").replace(".", "")
        
        meta_map[norm_key] = smoothed
        meta_map[name.lower()] = smoothed
        games_map[norm_key] = games
        games_map[name.lower()] = games
    
    return meta_map, global_avg, games_map

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
champ_meta_map, champ_global_avg, champ_games_map = load_champion_strengths()

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


@app.get("/api/champion/{champion}/role/{role}")
def api_champion_stats(champion: str, role: str):
    """
    Global pro stats (7-year DB) for a champion in a given role.
    Used when a specific player has no games on that champ.
    """
    data = get_champion_pro_stats(champion, role)
    if not data:
        return {"found": False}
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
        off_role_count = 0
        details = []
        counter_warnings = []
        class_counts = {c: 0 for c in TRACKED_CLASSES}
        total_counter_score = 0.0
        meta_sum = 0.0
        low_data_count = 0
        zero_pro_count = 0
        
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
                off_role_count += 1
                details.append(f"{champ} in {pos_req}")
            score += val
            
            # Class Counting
            my_classes = class_map.get(c_norm, [])
            for cls in my_classes:
                if cls in class_counts:
                    class_counts[cls] += 1

            # Champion meta strength (centered around 0)
            meta_val = champ_meta_map.get(c_norm, champ_global_avg)
            games = champ_games_map.get(c_norm, 0)
            meta_sum += (meta_val * 100.0 - 50.0)
            if games == 0:
                zero_pro_count += 1
            elif games < MIN_PRO_GAMES_FOR_CONFIDENT:
                low_data_count += 1

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

        meta_avg = meta_sum / max(1, len(draft))
        return score, off_role_detected, off_role_count, details, counter_warnings, class_counts, total_counter_score, meta_avg, low_data_count, zero_pro_count

    t1_role_score, t1_bad, t1_off_count, t1_details, t1_counters, t1_classes, t1_c_score, t1_meta, t1_low, t1_zero = get_role_score(blue_draft, red_draft)
    t2_role_score, t2_bad, t2_off_count, t2_details, t2_counters, t2_classes, t2_c_score, t2_meta, t2_low, t2_zero = get_role_score(red_draft, blue_draft)
    
    role_diff = t1_role_score - t2_role_score
    draft_meta_diff = t1_meta - t2_meta
    low_data_diff = t1_low - t2_low
    zero_pro_diff = t1_zero - t2_zero
    
    # 3. Predict (Pure ML V4)
    blue_win_pct = 50.0 
    
    if model:
        try:
            # Create input vector matching training columns
            input_data = {
                'elo_diff': elo_diff,
                'role_diff': role_diff,
                'counter_score': t1_c_score,
                'draft_meta_diff': draft_meta_diff,
                'low_data_diff': low_data_diff,
                'zero_pro_diff': zero_pro_diff,
            }
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

    # 4. Hard sanity clamp for troll drafts
    # If one team has 3+ clear off-role champs and the other has 0, heavily punish that team.
    if t1_off_count >= 3 and t2_off_count == 0:
        # Blue is trolling
        blue_win_pct = min(blue_win_pct, 20.0)
    elif t2_off_count >= 3 and t1_off_count == 0:
        # Red is trolling
        blue_win_pct = max(blue_win_pct, 80.0)

    # 5. Final Polish (Rounding)
    # Ensure 100.0 sum
    blue_win_pct = round(blue_win_pct, 1)
    red_win_pct = round(100.0 - blue_win_pct, 1)
    
    # Clamp to avoid 101% or -5%
    blue_win_pct = max(1.0, min(99.0, blue_win_pct))
    red_win_pct = round(100.0 - blue_win_pct, 1) # Recalculate red to ensure sum match

    # 6. Factors Explanation
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
