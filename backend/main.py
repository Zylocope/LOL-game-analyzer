from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
try:
    from .services import (
        get_team_stats,
        get_player_stats,
        get_db_connection,
        get_all_teams,
        get_matchup_stats,
        get_composition_analysis,
        get_champion_pro_stats,
        get_recent_champion_table,
        get_champion_usage,
        norm_champion,
    )
except ImportError:
    from services import (
        get_team_stats,
        get_player_stats,
        get_db_connection,
        get_all_teams,
        get_matchup_stats,
        get_composition_analysis,
        get_champion_pro_stats,
        get_recent_champion_table,
        get_champion_usage,
        norm_champion,
    )
import joblib
import pandas as pd
import numpy as np
import os
from datetime import datetime
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

        e_norm = enemy_champ.lower().replace(" ", "").replace("'", "").replace(".", "")
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
        counter_list = ", ".join(counters)
        warnings.append(f"⚠️ {champion} is countered by {counter_list}")

    return {"counter_score_impact": total_counter_score, "warnings": warnings}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Load the explicitly trained chronological model bundle
MODEL_PATH = os.path.join(BASE_DIR, "model_v6.pkl")
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.join(BASE_DIR, "model_v5.pkl")
RATINGS_PATH = os.path.join(BASE_DIR, "team_ratings.json")
TAGS_PATH = os.path.join(BASE_DIR, "../frontend/data/championTags.ts")
CHAMP_STATS_PATH = os.path.join(BASE_DIR, "champion_stats_pro.json")
MIN_PRO_GAMES_FOR_CONFIDENT = 50
TRACKED_CLASSES = [
    'assassin', 'catcher', 'vanguard', 'enchanter'
]
MODEL_FEATURES = [
    'elo_diff',
    'blue_score',
    'red_score',
    'blue_total_counter_score',
    'red_total_counter_score',
    'blue_meta_avg',
    'red_meta_avg',
    'blue_off_role_count',
    'red_off_role_count',
    'blue_unknown_role_count',
    'red_unknown_role_count',
    'blue_support_capable_count',
    'red_support_capable_count',
    'blue_jungle_capable_count',
    'red_jungle_capable_count',
    'blue_low_data_count',
    'red_low_data_count',
    'blue_zero_pro_count',
    'red_zero_pro_count',
] + [f'blue_{c}' for c in TRACKED_CLASSES] + [f'red_{c}' for c in TRACKED_CLASSES]

# Global State
model_data = None
model = None
model_features = None
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

# Only explicitly trained past-only bundles are served. Startup never retrains.
try:
    model_data = joblib.load(MODEL_PATH)
    if model_data.get('version') not in ('v5_past_only', 'v6_elo_corrections'):
        raise ValueError('Unsupported model version; run python -m backend.train')
    model = model_data['model']
    model_features = model_data['features']
except Exception as exc:
    print(f'Model unavailable: {exc}')
    model_data, model = None, None

role_map, class_map = load_champion_meta()
if model_data:
    snapshot = model_data['snapshot']
    elo_map, role_map = snapshot['elo'], snapshot['roles']
    champ_meta_map, champ_games_map = snapshot['meta'], snapshot['games']
    # Serving uses exactly the same smoothed aggregates as training.
    try:
        from . import services as stats_service
    except ImportError:
        import services as stats_service
    stats_service.MATCHUP_MATRIX = snapshot['matrix']

class PredictionRequest(BaseModel):
    blueTeam: str = Field(min_length=1, max_length=200)
    redTeam: str = Field(min_length=1, max_length=200)
    blueDraft: list[Annotated[str, Field(min_length=1, max_length=60)]] = Field(min_length=5, max_length=5)
    redDraft: list[Annotated[str, Field(min_length=1, max_length=60)]] = Field(min_length=5, max_length=5)

    bluePlayers: list[Annotated[str, Field(max_length=120)]] | None = Field(default=None, min_length=5, max_length=5)
    redPlayers: list[Annotated[str, Field(max_length=120)]] | None = Field(default=None, min_length=5, max_length=5)
    patch: str | None = Field(default=None, pattern=r'^\d{1,2}\.\d{2}$')

    @model_validator(mode='after')
    def validate_champions(self):
        normalized = [c.lower().replace(' ', '').replace("'", '').replace('.', '')
                      for c in self.blueDraft + self.redDraft]
        if len(set(normalized)) != 10:
            raise ValueError('Each champion can only be picked once')
        if any(c not in class_map for c in normalized):
            raise ValueError('Draft contains an unknown champion')
        return self

@app.get('/api/model')
def model_status():
    return {'ready': model is not None, 'version': model_data.get('version') if model_data else None,
            'evaluation': model_data.get('evaluation') if model_data else None,
            'holdout': model_data.get('holdout') if model_data else None,
            'ratings_through': model_data.get('ratings_through') if model_data else None,
            'latest_patch': getattr(model_data.get('state'), 'latest_patch', None) if model_data else None}

# --- API ---

@app.get("/")
def read_root():
    return {"status": "Nexus Sight API is running (past-only model)"}

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
    for entry in final_list:
        key = entry['team'].lower().replace(' ', '').replace("'", '').replace('.', '')
        entry['rating'] = round(elo_map.get(key, 1200))
    final_list.sort(key=lambda x: x['rating'], reverse=True)
    for rank, entry in enumerate(final_list, 1):
        entry['rank'] = rank

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


@app.get("/api/champions/recent")
def api_recent_champions():
    """Win rate, pick rate and role split for every champion over the last 12 months of pro games."""
    return get_recent_champion_table()


@app.get("/api/champion/{champion}/role/{role}")
def api_champion_stats(champion: str, role: str):
    """
    Pro stats for a champion in a given role over the last 12 months (smoothed toward 50%).
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
    unknown_role_count = 0
    support_capable_count = 0
    jungle_capable_count = 0

    for i, champ in enumerate(draft):
        if i >= 5: break
        if not champ: continue

        # A. Off-Role Check
        c_norm = champ.lower().replace(" ", "").replace("'", "").replace(".", "")
        pos_req = POSITIONS[i]

        role_analysis = _analyze_champion_role(c_norm, pos_req, role_map)
        valid_roles = role_map.get(c_norm, [])
        score += role_analysis["score_impact"]
        if not valid_roles:
            unknown_role_count += 1
        if "support" in valid_roles:
            support_capable_count += 1
        if "jungle" in valid_roles:
            jungle_capable_count += 1
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
    return score, off_role_detected, off_role_count, details, counter_warnings, class_counts, total_counter_score, meta_avg, low_data_count, zero_pro_count, unknown_role_count, support_capable_count, jungle_capable_count

def predict_v6(request):
    from backend.features import FEATURES, request_roster, patch_key
    state = model_data['state']
    blue = request_roster(state, request.blueTeam, request.blueDraft, request.bluePlayers)
    red = request_roster(state, request.redTeam, request.redDraft, request.redPlayers)
    patch = patch_key(request.patch) if request.patch else state.latest_patch
    vector = state.vector(blue, red, patch)
    frame = pd.DataFrame([vector], columns=FEATURES)
    try:
        probability = float(model.predict_proba(frame)[0, 1])
    except Exception as exc:
        raise HTTPException(status_code=503, detail='Model inference failed') from exc
    values = dict(zip(FEATURES, vector))
    blue_name, red_name = request.blueTeam, request.redTeam
    team_gap = values.get('elo_diff', 0.0)
    if abs(team_gap) < 15:
        factors = ["The two teams are evenly matched on recent results."]
    else:
        stronger = blue_name if team_gap > 0 else red_name
        factors = [f"{stronger} is the stronger team on recent results (rated {abs(team_gap):.0f} points higher)."]
    player_gap = values.get('player_elo_diff', 0.0)
    if 'player_elo_diff' in model_features and abs(player_gap) >= 15:
        factors.append(f"{blue_name if player_gap > 0 else red_name}'s starting players have the stronger track record.")
    unknown = sum(row['player'] not in state.players for row in blue + red)
    if unknown:
        factors.append(f"{unknown} player{'s have' if unknown > 1 else ' has'} no pro history yet, so "
                       f"{'they are' if unknown > 1 else 'they are'} treated as average.")
    if request.bluePlayers is None or request.redPlayers is None:
        factors.append("Starting players weren't entered, so each team's most recent lineup is used.")
    through = str(model_data.get('ratings_through') or model_data['evaluation']['data']['last_date'])[:10]
    try:
        through = datetime.strptime(through, '%Y-%m-%d').strftime('%d %b %Y').lstrip('0')
    except ValueError:
        pass
    factors.append(f"Based on pro games up to {through} (patch {patch}).")
    warnings = draft_reliability_warnings(request.blueDraft, request.redDraft)
    factors.extend(warnings)
    return {'blueWinChance': probability, 'redWinChance': 1-probability,
            'factors': factors, 'warnings': warnings, 'modelVersion': model_data['version'], 'patch': patch}


# Thresholds and measured effects come from scripts/analysis/rare_and_offrole_2026.py
# (v6 on the untouched 2026 test games).
RARE_PICK_GAMES = 50          # fewer all-time pro games than this = rare pick
UNCOMMON_ROLE_SHARE = 0.10    # played in this role in under 10% of its pro games = uncommon role
DRAFT_POSITIONS = [('top', 'Top'), ('jng', 'Jungle'), ('mid', 'Mid'), ('bot', 'Bot'), ('sup', 'Support')]


def draft_reliability_warnings(blue_draft, red_draft):
    usage = get_champion_usage()
    rare, uncommon = [], []
    for draft in (blue_draft, red_draft):
        for (pos, label), champ in zip(DRAFT_POSITIONS, draft):
            u = usage.get(norm_champion(champ), {'games': 0, 'roles': {}})
            games, in_role = u['games'], u['roles'].get(pos, 0)
            if games < RARE_PICK_GAMES:
                rare.append(f"{champ} ({games} pro game{'s' if games != 1 else ''})")
            if (games >= 10 and in_role / games < UNCOMMON_ROLE_SHARE) or (games < 10 and in_role == 0):
                uncommon.append(f"{champ} as {label}")
    warnings = []
    if rare:
        warnings.append("Rare pick: " + ", ".join(rare) + ". Predictions are less certain when a champion has "
                        "little pro history.")
    if uncommon:
        warnings.append("Unusual role: " + ", ".join(uncommon) + ". Predictions are less certain when a champion "
                        "plays outside its usual role.")
    return warnings


# --- Ranked mode: draft-only model for high-rank solo queue (weights from scripts/ranked/train.py) ---
RANKED_PATH = os.path.join(BASE_DIR, "ranked_model.json")
RANKED_ROLES = [("top", "Top"), ("jungle", "Jungle"), ("middle", "Mid"), ("bottom", "Bot"), ("utility", "Support")]
try:
    with open(RANKED_PATH, encoding="utf-8") as _f:
        ranked_model = json.load(_f)
except (OSError, ValueError):
    ranked_model = None
try:
    with open(os.path.join(BASE_DIR, "datadragon_champions.json"), encoding="utf-8") as _f:
        CHAMPION_NAMES = {cid: c.get("name", cid) for cid, c in json.load(_f).get("data", {}).items()}
except (OSError, ValueError):
    CHAMPION_NAMES = {}


class RankedRequest(BaseModel):
    # Riot champion ids in role order: Top, Jungle, Mid, Bot, Support
    blue: list[Annotated[str, Field(min_length=1, max_length=40)]] = Field(min_length=5, max_length=5)
    red: list[Annotated[str, Field(min_length=1, max_length=40)]] = Field(min_length=5, max_length=5)

    @model_validator(mode='after')
    def ten_different(self):
        if len({c.lower() for c in self.blue + self.red}) != 10:
            raise ValueError('Pick ten different champions')
        return self


@app.get("/api/ranked/info")
def ranked_info():
    return {"ready": ranked_model is not None, "summary": ranked_model.get("summary") if ranked_model else None}


@app.post("/api/ranked/predict")
def ranked_predict(request: RankedRequest):
    if ranked_model is None:
        raise HTTPException(status_code=503, detail="Ranked model unavailable")
    weights, logit, picks, unseen = ranked_model["weights"], ranked_model["side"], [], []
    for side, sign, draft in (("blue", 1.0, request.blue), ("red", -1.0, request.red)):
        for (role, label), champ in zip(RANKED_ROLES, draft):
            key = f"{role}:{champ}"
            w = weights.get(key)
            if w is None:
                unseen.append(f"{CHAMPION_NAMES.get(champ, champ)} ({label})")
                w = 0.0
            logit += sign * w
            # Effect in percentage points around an even game (slope of the logistic curve at 50% is 1/4).
            picks.append({"side": side, "role": label, "champion": CHAMPION_NAMES.get(champ, champ), "id": champ,
                          "effect": round(25 * w, 1)})
    import math
    p = 1 / (1 + math.exp(-logit))
    factors = []
    best = sorted(picks, key=lambda x: -x["effect"])
    strong = [f"{x['champion']} ({x['side'].title()} {x['role']})" for x in best[:2] if x["effect"] >= 0.5]
    weak = [f"{x['champion']} ({x['side'].title()} {x['role']})" for x in best[::-1][:2] if x["effect"] <= -0.5]
    if strong:
        factors.append("Doing well in recent Master+ games: " + ", ".join(strong) + ".")
    if weak:
        factors.append("Struggling in recent Master+ games: " + ", ".join(weak) + ".")
    if unseen:
        factors.append("Too few recent games to judge: " + ", ".join(unseen) + ".")
    factors.append("In ranked, matchmaking pairs players of similar skill, so a draft usually moves the odds by only "
                   "a few percent. Player skill decides most games.")
    return {"blueWinChance": p, "redWinChance": 1 - p, "factors": factors, "picks": picks,
            "summary": ranked_model.get("summary")}


@app.post("/api/predict")
def predict_match(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Prediction model unavailable. Run python -m backend.train.")
    if model_data and model_data.get('version') == 'v6_elo_corrections':
        return predict_v6(request)
    match_data = request.model_dump()
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
    elo1 = elo_map.get(blue_name.lower().replace(" ", "").replace("'", "").replace(".", ""), elo_map.get(blue_name, 1200))
    elo2 = elo_map.get(red_name.lower().replace(" ", "").replace("'", "").replace(".", ""), elo_map.get(red_name, 1200))
    elo_diff = elo1 - elo2

    # 2. Role Diff & Counter Analysis
    POSITIONS = ['top', 'jungle', 'mid', 'bot', 'support']

    blue_score, blue_off_role_detected, blue_off_role_count, blue_details, blue_counter_warnings, blue_class_counts, blue_total_counter_score, blue_meta_avg, blue_low_data_count, blue_zero_pro_count, blue_unknown_role_count, blue_support_capable_count, blue_jungle_capable_count = get_role_score(blue_draft, red_draft, POSITIONS, TRACKED_CLASSES, role_map, class_map, champ_meta_map, champ_global_avg, champ_games_map, MIN_PRO_GAMES_FOR_CONFIDENT, get_matchup_stats)
    red_score, red_off_role_detected, red_off_role_count, red_details, red_counter_warnings, red_class_counts, red_total_counter_score, red_meta_avg, red_low_data_count, red_zero_pro_count, red_unknown_role_count, red_support_capable_count, red_jungle_capable_count = get_role_score(red_draft, blue_draft, POSITIONS, TRACKED_CLASSES, role_map, class_map, champ_meta_map, champ_global_avg, champ_games_map, MIN_PRO_GAMES_FOR_CONFIDENT, get_matchup_stats)

    # 3. Model Prediction
    input_feature_map = {
        'elo_diff': elo_diff,
        'blue_score': blue_score,
        'red_score': red_score,
        'blue_total_counter_score': blue_total_counter_score,
        'red_total_counter_score': red_total_counter_score,
        'blue_meta_avg': blue_meta_avg,
        'red_meta_avg': red_meta_avg,
        'blue_off_role_count': blue_off_role_count,
        'red_off_role_count': red_off_role_count,
        'blue_unknown_role_count': blue_unknown_role_count,
        'red_unknown_role_count': red_unknown_role_count,
        'blue_support_capable_count': blue_support_capable_count,
        'red_support_capable_count': red_support_capable_count,
        'blue_jungle_capable_count': blue_jungle_capable_count,
        'red_jungle_capable_count': red_jungle_capable_count,
        'blue_low_data_count': blue_low_data_count,
        'red_low_data_count': red_low_data_count,
        'blue_zero_pro_count': blue_zero_pro_count,
        'red_zero_pro_count': red_zero_pro_count,
        'role_diff': blue_score - red_score,
        'counter_score': blue_total_counter_score,
        'draft_meta_diff': blue_meta_avg - red_meta_avg,
        'low_data_diff': blue_low_data_count - red_low_data_count,
        'zero_pro_diff': blue_zero_pro_count - red_zero_pro_count,
        'off_role_diff': blue_off_role_count - red_off_role_count,
    }
    for champion_class in TRACKED_CLASSES:
        input_feature_map[f'blue_{champion_class}'] = blue_class_counts[champion_class]
        input_feature_map[f'red_{champion_class}'] = red_class_counts[champion_class]
        input_feature_map[f'diff_{champion_class}'] = blue_class_counts[champion_class] - red_class_counts[champion_class]

    prediction = 0.5 # Default to 50/50
    if model:
        try:
            active_features = model_features or MODEL_FEATURES
            model_input = pd.DataFrame(
                [[input_feature_map[feature] for feature in active_features]],
                columns=active_features,
            )
            swapped = dict(input_feature_map)
            swapped['elo_diff'] = -input_feature_map['elo_diff']
            for key in input_feature_map:
                if key.startswith('blue_'):
                    swapped[key] = input_feature_map['red_' + key[5:]]
                elif key.startswith('red_'):
                    swapped[key] = input_feature_map['blue_' + key[4:]]
            mirror = pd.DataFrame([[swapped[f] for f in active_features]], columns=active_features)
            prediction = float((model.predict_proba(model_input)[0][1] + 1 - model.predict_proba(mirror)[0][1]) / 2)
        except Exception as e:
            raise HTTPException(status_code=503, detail="Model inference failed") from e

    # No unvalidated probability penalties: serve the estimator evaluated in the report.
    troll_penalty_blue = troll_penalty_red = 0.0
    draft_integrity_guardrail = None

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

    if blue_total_counter_score > red_total_counter_score:
        factors.append(f"Blue team has a more favorable matchup against the enemy team.")
    elif red_total_counter_score > blue_total_counter_score:
        factors.append(f"Red team has a more favorable matchup against the enemy team.")

    if blue_meta_avg > red_meta_avg:
        factors.append(f"Blue team picked more meta champions (Avg WR: {blue_meta_avg + 50.0:.1f}% vs {red_meta_avg + 50.0:.1f}%).")
    elif red_meta_avg > blue_meta_avg:
        factors.append(f"Red team picked more meta champions (Avg WR: {red_meta_avg + 50.0:.1f}% vs {blue_meta_avg + 50.0:.1f}%).")

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

    if draft_integrity_guardrail:
        factors.append(draft_integrity_guardrail)

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
