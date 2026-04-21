from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services import (
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

def _analyze_champion_role(champion_normalized_name: str, required_position: str, role_map: dict):
    valid_roles = role_map.get(champion_normalized_name, [])
    is_off_role = False
    score_impact = 0.0

    if not valid_roles:
        score_impact = 0.0 # Unknown role, neutral impact
    elif required_position in valid_roles:
        score_impact = 1.0 # Correct role, positive impact
    else:
        score_impact = -1.0 # Off-role, negative impact
        is_off_role = True
    
    return {"score_impact": score_impact, "is_off_role": is_off_role}

def _analyze_champion_meta(champion_normalized_name: str, champ_meta_map: dict, champ_global_avg: float, champ_games_map: dict, min_pro_games_for_confident: int):
    meta_val = champ_meta_map.get(champion_normalized_name, champ_global_avg)
    games = champ_games_map.get(champion_normalized_name, 0)
    meta_score_impact = (meta_val * 100.0 - 50.0)
    is_zero_pro_games = (games == 0)
    is_low_data = (games < min_pro_games_for_confident and games > 0)
    
    return {
        "meta_score_impact": meta_score_impact,
        "is_zero_pro_games": is_zero_pro_games,
        "is_low_data": is_low_data
    }

def _analyze_champion_counters(champion: str, my_classes: list, position_index: int, required_position: str, enemy_draft: list, class_map: dict, get_matchup_stats, POSITIONS: list):
    counters = []
    total_counter_score = 0.0

    # 1. Lane Counter (Matrix)
    lane_opp = enemy_draft[position_index] if position_index < len(enemy_draft) else None
    if lane_opp:
        stats = get_matchup_stats(champion, lane_opp, required_position)
        if stats:
            total_counter_score += (stats["winRate"] - 50.0)
            if stats["type"] == "disadvantage":
                counters.append(f"{POSITIONS[position_index].capitalize()} (Lane)")

    # 2. Cross-Role Counter (Class Logic)
    is_squishy = any(c in ["mage", "marksman", "enchanter", "artillery"] for c in my_classes)
    is_melee = any(c in ["fighter", "tank", "slayer"] for c in my_classes)
    
    for j, enemy_champ in enumerate(enemy_draft):
        if not enemy_champ: continue
        if position_index == j: continue 
        
        e_norm = enemy_champ.lower().replace(" ", "").replace("\"", "").replace(".", "")
        e_classes = class_map.get(e_norm, [])
        
        is_threat = False
        
        if is_squishy:
            if any(c in ["assassin", "diver", "catcher", "vanguard"] for c in e_classes):
                is_threat = True
        if is_melee:
            if any(c in ["control", "disengage", "warden"] for c in e_classes):
                is_threat = True
                
        if is_threat:
            counters.append(POSITIONS[j].capitalize())
    
    warnings = []
    if len(counters) >= 3:
        warnings.append(f"⚠️ {champion} is countered by {", ".join(counters)}")

    return {"counter_score_impact": total_counter_score, "warnings": warnings}

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

def get_role_score(draft, enemy_draft, POSITIONS, TRACKED_CLASSES, role_map, class_map, champ_meta_map, champ_global_avg, champ_games_map, MIN_PRO_GAMES_FOR_CONFIDENT, get_matchup_stats):
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
        
        role_analysis = _analyze_champion_role(c_norm, pos_req, role_map)
        score += role_analysis["score_impact"]
        if role_analysis["is_off_role"]:
            off_role_detected = True
            off_role_count += 1
            details.append(f"{champ} in {pos_req}")
        
        # Class Counting
        my_classes = class_map.get(c_norm, [])
        for cls in my_classes:
            if cls in class_counts:
                class_counts[cls] += 1

        # Champion meta strength (centered around 0)
        meta_analysis = _analyze_champion_meta(c_norm, champ_meta_map, champ_global_avg, champ_games_map, MIN_PRO_GAMES_FOR_CONFIDENT)
        meta_sum += meta_analysis["meta_score_impact"]
        if meta_analysis["is_zero_pro_games"]:
            zero_pro_count += 1
        elif meta_analysis["is_low_data"]:
            low_data_count += 1

        # B. Counter Check
        counter_analysis = _analyze_champion_counters(champ, my_classes, i, pos_req, enemy_draft, class_map, get_matchup_stats, POSITIONS)
        total_counter_score += counter_analysis["counter_score_impact"]
        if counter_analysis["warnings"]:
            counter_warnings.extend(counter_analysis["warnings"])

    meta_avg = meta_sum / max(1, len(draft))
    return score, off_role_detected, off_role_count, details, counter_warnings, class_counts, total_counter_score, meta_avg, low_data_count, zero_pro_count

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

    if not blue_draft or not red_draft:
        return {"error": "Both blueDraft and redDraft must contain champions for prediction.", "blueWinChance": 0.5, "redWinChance": 0.5, "factors": ["Missing draft information."]}

    if model is None:
        print("⚠️ Model not loaded, operating in Heuristic Mode.")
    
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

    blue_score, blue_off_role_detected, blue_off_role_count, blue_details, blue_counter_warnings, blue_class_counts, blue_total_counter_score, blue_meta_avg, blue_low_data_count, blue_zero_pro_count = get_role_score(blue_draft, red_draft, POSITIONS, TRACKED_CLASSES, role_map, class_map, champ_meta_map, champ_global_avg, champ_games_map, MIN_PRO_GAMES_FOR_CONFIDENT, get_matchup_stats)
    red_score, red_off_role_detected, red_off_role_count, red_details, red_counter_warnings, red_class_counts, red_total_counter_score, red_meta_avg, red_low_data_count, red_zero_pro_count = get_role_score(red_draft, blue_draft, POSITIONS, TRACKED_CLASSES, role_map, class_map, champ_meta_map, champ_global_avg, champ_games_map, MIN_PRO_GAMES_FOR_CONFIDENT, get_matchup_stats)

    # 3. Model Prediction
    input_features = [
        elo_diff,
        blue_score,
        red_score,
        blue_total_counter_score,
        red_total_counter_score,
        blue_meta_avg,
        red_meta_avg,
        blue_class_counts['marksman'],
        blue_class_counts['tank'],
        blue_class_counts['support'],
        blue_class_counts['fighter'],
        blue_class_counts['mage'],
        blue_class_counts['assassin'],
        blue_class_counts['catcher'],
        blue_class_counts['vanguard'],
        blue_class_counts['enchanter'],
        red_class_counts['marksman'],
        red_class_counts['tank'],
        red_class_counts['support'],
        red_class_counts['fighter'],
        red_class_counts['mage'],
        red_class_counts['assassin'],
        red_class_counts['catcher'],
        red_class_counts['vanguard'],
        red_class_counts['enchanter'],
    ]

    prediction = 0.5 # Default to 50/50
    if model:
        try:
            prediction = model.predict_proba([input_features])[0][1]
        except Exception as e:
            print(f"Model prediction failed: {e}. Falling back to enhanced heuristic.")
            # Enhanced Heuristic fallback if model fails
            # Weights can be tuned further
            heuristic_score = (
                (elo_diff / 2000) * 0.2 +  # Elo difference contribution
                ((blue_score - red_score) / 10) * 0.3 + # Role score contribution
                ((blue_total_counter_score - red_total_counter_score) / 100) * 0.2 + # Counter score contribution
                ((blue_meta_avg - red_meta_avg) * 100) * 0.1 # Meta average contribution
            )
            prediction = 0.5 + heuristic_score
            prediction = np.clip(prediction, 0.1, 0.9) # Clamp to reasonable range

    # Hard sanity clamp for extreme off-roles or low data
    troll_penalty_blue = 0.0
    if blue_off_role_count == 1: troll_penalty_blue += 0.05
    elif blue_off_role_count >= 2: troll_penalty_blue += 0.15
    
    if blue_zero_pro_count == 1: troll_penalty_blue += 0.03
    elif blue_zero_pro_count == 2: troll_penalty_blue += 0.07
    elif blue_zero_pro_count >= 3: troll_penalty_blue += 0.12

    if blue_low_data_count >= 3: troll_penalty_blue += 0.05

    troll_penalty_red = 0.0
    if red_off_role_count == 1: troll_penalty_red += 0.05
    elif red_off_role_count >= 2: troll_penalty_red += 0.15
    
    if red_zero_pro_count == 1: troll_penalty_red += 0.03
    elif red_zero_pro_count == 2: troll_penalty_red += 0.07
    elif red_zero_pro_count >= 3: troll_penalty_red += 0.12

    if red_low_data_count >= 3: troll_penalty_red += 0.05

    prediction -= (troll_penalty_blue - troll_penalty_red)
    prediction = np.clip(prediction, 0.05, 0.95) # Final clamp

    # Factors Explanation
    factors = []
    if elo_diff > 0:
        factors.append(f"Blue team has a higher Elo rating (Elo difference: {elo_diff:.0f}).")
    elif elo_diff < 0:
        factors.append(f"Red team has a higher Elo rating (Elo difference: {-elo_diff:.0f}).")

    if blue_score > red_score:
        factors.append(f"Blue team has a better role composition score ({blue_score:.1f} vs {red_score:.1f}).")
    elif red_score > blue_score:
        factors.append(f"Red team has a better role composition score ({red_score:.1f} vs {blue_score:.1f}).")

    if blue_total_counter_score < red_total_counter_score:
        factors.append(f"Blue team has a more favorable matchup against the enemy team.")
    elif red_total_counter_score < blue_total_counter_score:
        factors.append(f"Red team has a more favorable matchup against the enemy team.")

    if blue_meta_avg > red_meta_avg:
        factors.append(f"Blue team picked more meta champions (Avg WR: {blue_meta_avg*100:.1f}% vs {red_meta_avg*100:.1f}%).")
    elif red_meta_avg > blue_meta_avg:
        factors.append(f"Red team picked more meta champions (Avg WR: {red_meta_avg*100:.1f}% vs {blue_meta_avg*100:.1f}%).")

    if blue_off_role_detected:
        factors.append(f"Blue team has off-role picks: {', '.join(blue_details)}.")
    if red_off_role_detected:
        factors.append(f"Red team has off-role picks: {', '.join(red_details)}.")

    if blue_zero_pro_count > 0:
        factors.append(f"Blue team has {blue_zero_pro_count} champions with no pro play data.")
    if red_zero_pro_count > 0:
        factors.append(f"Red team has {red_zero_pro_count} champions with no pro play data.")

    if blue_low_data_count > 0:
        factors.append(f"Blue team has {blue_low_data_count} champions with limited pro play data.")
    if red_low_data_count > 0:
        factors.append(f"Red team has {red_low_data_count} champions with limited pro play data.")

    if troll_penalty_blue > 0:
        factors.append(f"Blue team received a penalty ({troll_penalty_blue*100:.0f}%) for unusual draft choices.")
    if troll_penalty_red > 0:
        factors.append(f"Red team received a penalty ({troll_penalty_red*100:.0f}%) for unusual draft choices.")

    # Add a general factor if the model failed and heuristic was used
    if model is None:
        factors.append("Prediction based on heuristic due to model unavailability.")

    # Add counter warnings
    factors.extend(blue_counter_warnings)
    factors.extend(red_counter_warnings)

    return {
        "blueWinChance": prediction,
        "redWinChance": 1 - prediction,
        "factors": factors
    }
