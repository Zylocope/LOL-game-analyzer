import sqlite3
import pandas as pd
import numpy as np
import json
import re
import os
import pickle
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nexus_sight.db")
RATINGS_PATH = os.path.join(BASE_DIR, "team_ratings.json")
TAGS_PATH = os.path.join(BASE_DIR, "../data/championTags.ts")
MODEL_OUTPUT_PATH = os.path.join(BASE_DIR, "match_predictor_v3.pkl")

# --- 1. LOAD HELPERS ---

def load_champion_roles():
    """Parses championTags.ts to extract valid roles for each champion."""
    print("📜 Parsing Champion Roles...")
    with open(TAGS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract JSON part using Regex (between 'content = {' and '};')
    # The file starts with "export const CHAMPION_DATA: ... = {"
    match = re.search(r'=\s*({.*})', content, re.DOTALL)
    if not match:
        raise ValueError("Could not parse championTags.ts")
    
    json_str = match.group(1)
    
    # Clean up TypeScript/JS specific syntax to make it valid JSON
    # 1. Remove comments if any (not present in snippet but good safety)
    # 2. Quote unquoted keys (id: -> "id":)
    # This is tricky with regex. A simpler approach for the specific file format:
    # The file is actually well-formatted JSON-like content.
    # Let's try a simpler manual extraction or just eval (risky but easy for local trusted file)
    # Or, since I know the structure, let's just use the frontend data structure logic.
    
    # Hacky but effective for this specific file format:
    # Convert keys "key": to "key": (already done)
    # Convert value numbers and strings.
    # Actually, the file uses double quotes for keys. It might just be valid JSON if I trim the end.
    # It has "stats": { ... globalWinRate: null }. `null` is valid JSON.
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        # If strict JSON fails (e.g. trailing commas), use a lenient approach
        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        try:
            data = json.loads(json_str)
        except:
            print("⚠️ JSON Parse failed, using fallback empty roles.")
            return {}

    # Map: "Ahri" -> ["mid"]
    role_map = {}
    for name, details in data.items():
        role_map[name.lower()] = [r.lower() for r in details.get('roles', [])]
        # normalize names
        role_map[name.lower().replace(" ", "").replace("'", "").replace(".", "")] = role_map[name.lower()]
    
    return role_map

def load_team_elo():
    """Loads the Team Elo Ratings into a Dictionary."""
    print("🏆 Loading Team Ratings...")
    if not os.path.exists(RATINGS_PATH):
        print("❌ Ratings file not found! Run calculate_team_elo.py first.")
        return {}
    
    with open(RATINGS_PATH, 'r') as f:
        ratings_list = json.load(f)
    
    # Map: "t1" -> 2000
    elo_map = {}
    for entry in ratings_list:
        norm_name = entry['team'].lower().replace(" ", "")
        elo_map[norm_name] = entry['rating']
        # Also map the exact name
        elo_map[entry['team']] = entry['rating']
        
    return elo_map

# --- 2. DATASET BUILDING ---

def build_dataset():
    print("🏗️  Building Training Dataset (V3)...")
    conn = sqlite3.connect(DB_PATH)
    
    # A. Get Matches (Target: result) + Team Names
    # We focus on rows where we have result info.
    # We join player_stats to get positions.
    # This is a heavy query. Let's do it in chunks or smart aggregation.
    
    # Step 1: Get Team Stats (The Anchor)
    query_teams = """
    SELECT 
        gameid, 
        teamname, 
        result, 
        golddiffat15, 
        dragons, 
        opp_dragons 
    FROM team_stats
    WHERE datacompleteness = 'complete' 
    AND (year >= 2022) -- Focus on recent meta for better training
    """
    df_teams = pd.read_sql(query_teams, conn)
    
    # Step 2: Get Player Stats (To check Role Fit)
    query_players = """
    SELECT gameid, teamname, champion, position
    FROM player_stats
    WHERE gameid IN (SELECT gameid FROM team_stats WHERE year >= 2022)
    """
    df_players = pd.read_sql(query_players, conn)
    conn.close()
    
    print(f"   Loaded {len(df_teams)} team rows and {len(df_players)} player rows.")
    
    # B. Load External Data
    elo_map = load_team_elo()
    role_map = load_champion_roles()
    
    # C. Feature Engineering Loop
    features = []
    
    # Group players by game and team
    # This is faster than iterating rows
    df_players['norm_champ'] = df_players['champion'].str.lower().str.replace("[^a-z0-9]", "", regex=True)
    df_players['norm_pos'] = df_players['position'].str.lower()
    
    # Helper to check fit
    def check_fit(row):
        champ = row['norm_champ']
        pos = row['norm_pos'] # top, jng, mid, bot, sup
        
        valid_roles = role_map.get(champ, [])
        if not valid_roles: return 0.5 # Unknown champ
        
        # Map DB positions to JSON positions
        # DB: top, jng, mid, bot, sup
        # JSON: top, jungle, mid, bot, support
        mapping = {'jng': 'jungle', 'sup': 'support'}
        clean_pos = mapping.get(pos, pos)
        
        if clean_pos in valid_roles:
            return 1.0
        return -1.0 # PENALTY for off-role
    
    print("   Calculating Role Fits...")
    df_players['role_fit'] = df_players.apply(check_fit, axis=1)
    
    # Aggregate Role Fit per Team
    team_fits = df_players.groupby(['gameid', 'teamname'])['role_fit'].sum().reset_index()
    team_fits.rename(columns={'role_fit': 'team_role_score'}, inplace=True)
    
    # Merge back to Team Stats
    df = pd.merge(df_teams, team_fits, on=['gameid', 'teamname'], how='left')
    df['team_role_score'] = df['team_role_score'].fillna(0)
    
    # Now we need to pair them into Matches (Blue vs Red)
    # A Match has 2 rows in df_teams (same gameid).
    # We need to pivot or self-join.
    
    print("   Pairing Matches...")
    # Assume first row of gameid is Blue, second is Red (or just pair them)
    # Robust way: Group by gameid
    games = []
    
    grouped = df.groupby('gameid')
    for g_id, group in grouped:
        if len(group) != 2: continue
        
        t1 = group.iloc[0]
        t2 = group.iloc[1]
        
        # Normalize Names for Elo Lookup
        name1 = t1['teamname'].replace(" ", "")
        name2 = t2['teamname'].replace(" ", "")
        
        # Features
        elo1 = elo_map.get(name1, elo_map.get(t1['teamname'], 1200)) # Default to 1200 if unknown
        elo2 = elo_map.get(name2, elo_map.get(t2['teamname'], 1200))
        
        # Historical Stats (Identity) - In a real scenario, this should be pre-calculated Avg
        # But for training on past matches, we use the actual game result stats as proxies for "Strength Difference"
        # Wait, using actual GoldDiff@15 of the CURRENT game to predict the outcome of the CURRENT game is cheating (Target Leakage).
        # We must use PRE-GAME stats. 
        # Since we don't have a "Running Average" table easily ready, we will use Elo + Role Fit as the primary predictors.
        # Elo implicitly captures historical gold dominance (calculated in calculating_team_elo.py).
        
        # Features Vector:
        # 1. Elo Diff
        # 2. Role Fit Diff
        # 3. Side (Blue=1, Red=0) - Logic: We always predict from T1 perspective
        
        row_dict = {
            'elo_diff': elo1 - elo2,
            'role_diff': t1['team_role_score'] - t2['team_role_score'],
            'blue_side': 1, # Assuming T1 is blue for simplicity, or we check 'side' column if existed
            't1_win': 1 if t1['result'] == 1 else 0
        }
        games.append(row_dict)
        
        # Data Augmentation: Flip perspective (T2 vs T1)
        row_dict_flip = {
            'elo_diff': elo2 - elo1,
            'role_diff': t2['team_role_score'] - t1['team_role_score'],
            'blue_side': 0,
            't1_win': 1 if t2['result'] == 1 else 0
        }
        games.append(row_dict_flip)

    return pd.DataFrame(games)

# --- 3. TRAINING ---

def train_and_save():
    df = build_dataset()
    print(f"📊 Dataset Ready: {len(df)} samples")
    
    if len(df) == 0:
        print("❌ No data found. Check database.")
        return

    X = df[['elo_diff', 'role_diff']]
    y = df['t1_win']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train XGBoost (GradientBoostingClassifier as safe fallback)
    print("🧠 Training Gradient Boosting Model...")
    clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n🎯 Model Accuracy: {acc*100:.2f}%")
    print(classification_report(y_test, y_pred))
    
    # Feature Importance
    print("\n🔍 Feature Importance:")
    for name, score in zip(X.columns, clf.feature_importances_):
        print(f"   - {name}: {score:.4f}")
        
    # Save
    model_data = {
        'model': clf,
        'features': ['elo_diff', 'role_diff'],
        'version': 'v3'
    }
    with open(MODEL_OUTPUT_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    print(f"\n💾 Model saved to {MODEL_OUTPUT_PATH}")

if __name__ == "__main__":
    train_and_save()
