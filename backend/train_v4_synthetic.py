import sqlite3
import pandas as pd
import numpy as np
import json
import re
import os
import pickle
import random
from sklearn.ensemble import GradientBoostingClassifier

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nexus_sight.db")
TAGS_PATH = os.path.join(BASE_DIR, "../data/championTags.ts")
DATASET_OUTPUT_PATH = os.path.join(BASE_DIR, "dataset_v4.csv")
MODEL_OUTPUT_PATH = os.path.join(BASE_DIR, "match_predictor_v4.pkl")
MATRIX_PATH = os.path.join(BASE_DIR, "data", "matchup_matrix.json")

# --- 1. LOADERS ---

def load_champion_meta():
    print("📜 Parsing Champion Roles & Classes...")
    if not os.path.exists(TAGS_PATH):
        print("❌ Champion Tags not found.")
        return {}, {}
        
    with open(TAGS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'=\s*({.*})', content, re.DOTALL)
    if not match: return {}, {}
    
    json_str = match.group(1)
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    try:
        data = json.loads(json_str)
    except:
        return {}, {}

    role_map = {}
    class_map = {}
    for name, details in data.items():
        # Normalized key
        norm_key = name.lower().replace(" ", "").replace("'", "").replace(".", "")
        
        # Roles
        roles = [r.lower() for r in details.get('roles', [])]
        role_map[norm_key] = roles
        role_map[name.lower()] = roles
        
        # Classes
        classes = [c.lower() for c in details.get('classes', [])]
        class_map[norm_key] = classes
        class_map[name.lower()] = classes
        
    return role_map, class_map

def load_team_elo():
    # Helper to fetch Elo if available (stub for now, usually loaded from JSON)
    # For synthetic training, we assume Elo is already in DB or use placeholder
    # Actually, main.py loads Elo from a file. 
    # Here we should try to load it or default to 1200.
    RATINGS_PATH = os.path.join(BASE_DIR, "team_ratings.json")
    if not os.path.exists(RATINGS_PATH): return {}
    with open(RATINGS_PATH, 'r') as f:
        ratings_list = json.load(f)
    
    elo_map = {}
    for entry in ratings_list:
        norm_name = entry['team'].lower().replace(" ", "")
        elo_map[norm_name] = entry['rating']
        elo_map[entry['team']] = entry['rating']
    return elo_map

# --- 2. DATA GENERATION ---

def generate_data():
    print("🏗️  Building Synthetic Training Data (V4)...")
    
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT gameid, teamname, result, position, champion
    FROM player_stats
    WHERE gameid IN (
        SELECT gameid FROM team_stats 
        WHERE year >= 2022 AND datacompleteness = 'complete'
    )
    """
    try:
        df_raw = pd.read_sql(query, conn)
    except:
        print("❌ DB Read Failed")
        conn.close()
        return pd.DataFrame()
    conn.close()
    
    role_map, class_map = load_champion_meta()
    elo_map = load_team_elo()
    
    # Load Matchup Matrix
    matchup_matrix = {}
    if os.path.exists(MATRIX_PATH):
        with open(MATRIX_PATH, 'r') as f:
            matchup_matrix = json.load(f)

    # RESTART LOOP AT GAME LEVEL
    matches = df_raw.groupby('gameid')
    
    final_dataset = []
    count_real = 0
    count_fake = 0
    
    # Classes to track (The "Big Hitters" + "Sub-Class Trinity")
    TRACKED_CLASSES = [
        'marksman', 'tank', 'support', 
        'fighter', 'mage', 'assassin',
        'catcher', 'vanguard', 'enchanter'
    ]
    
    for gameid, game_df in matches:
        teams = game_df['teamname'].unique()
        if len(teams) != 2: continue
        
        t1_name = teams[0]
        t2_name = teams[1]
        
        t1_rows = game_df[game_df['teamname'] == t1_name]
        t2_rows = game_df[game_df['teamname'] == t2_name]
        
        if len(t1_rows) != 5 or len(t2_rows) != 5: continue
        
        # --- HELPER: Compute Features for a Team ---
        def get_team_features(rows, t_name, enemy_rows=None):
            r_score = 0
            roster_data = []
            class_counts = {c: 0 for c in TRACKED_CLASSES}
            
            # Helper to map position to champion for counter lookup
            my_champs = {} 
            
            for _, r in rows.iterrows():
                p = r['position'].lower()
                p = {'jng': 'jungle', 'sup': 'support'}.get(p, p)
                c = r['champion'].lower().replace(" ", "").replace("'", "").replace(".", "")
                
                my_champs[p] = c
                
                # Role Score
                valid = role_map.get(c, [])
                if not valid: val = 0.5 
                else: val = 1.0 if p in valid else -1.0
                r_score += val
                
                # Class Counts
                my_classes = class_map.get(c, [])
                for cls in my_classes:
                    if cls in class_counts:
                        class_counts[cls] += 1
                
                roster_data.append((c, p, valid))

            # Counter Score (vs Enemy)
            c_score = 0.0
            if enemy_rows is not None:
                for _, er in enemy_rows.iterrows():
                    ep = er['position'].lower()
                    ep = {'jng': 'jungle', 'sup': 'support'}.get(ep, ep)
                    ec = er['champion'].lower().replace(" ", "").replace("'", "").replace(".", "")
                    
                    mc = my_champs.get(ep)
                    if mc and mc in matchup_matrix and ep in matchup_matrix[mc]:
                        if ec in matchup_matrix[mc][ep]:
                            wr = matchup_matrix[mc][ep][ec]['winRate']
                            # CLAMP to [-10, +10]
                            impact = max(-10.0, min(10.0, wr - 50.0))
                            c_score += impact

            elo = elo_map.get(t_name.replace(" ", ""), elo_map.get(t_name, 1200))
            result = rows.iloc[0]['result']
            return elo, r_score, result, roster_data, class_counts, c_score

        # 1. Get Real Stats
        t1_elo, t1_role, t1_res, t1_roster, t1_classes, t1_counter = get_team_features(t1_rows, t1_name, t2_rows)
        t2_elo, t2_role, t2_res, t2_roster, t2_classes, t2_counter = get_team_features(t2_rows, t2_name, t1_rows)
        
        real_row = {
            'elo_diff': t1_elo - t2_elo,
            'role_diff': t1_role - t2_role,
            'counter_score': t1_counter, # T1 advantage vs T2
            'target': 1 if t1_res == 1 else 0,
            'type': 'real'
        }
        for cls in TRACKED_CLASSES:
            real_row[f'diff_{cls}'] = t1_classes[cls] - t2_classes[cls]
            
        final_dataset.append(real_row)
        count_real += 1
        
        # NOTE: Synthetic Data Generation (Corruption Logic) has been removed
        # to ensure the model trains exclusively on real professional match data.
        # This prioritizes historical accuracy over hypothetical scenarios.

    print(f"✅ Generated: {count_real} Real Samples")
    
    df = pd.DataFrame(final_dataset)
    df.to_csv(DATASET_OUTPUT_PATH, index=False)
    print(f"💾 Dataset written to {DATASET_OUTPUT_PATH}")
    return df

# --- 3. TRAINING ---

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ... (Imports above stay same)

def train_model_v4():
    try:
        # 1. Generate / Load Data
        df = generate_data()
        if df.empty: return None
        
        # 2. Train
        TRACKED_CLASSES = [
            'marksman', 'tank', 'support', 
            'fighter', 'mage', 'assassin',
            'catcher', 'vanguard', 'enchanter'
        ]
        
        features = ['elo_diff', 'role_diff', 'counter_score'] + [f'diff_{c}' for c in TRACKED_CLASSES]
        
        X = df[features]
        y = df['target']
        
        # --- NEW: Validation Split (80% Train, 20% Test) ---
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        print(f"🧠 Training Gradient Boosting Classifier (Train: {len(X_train)}, Test: {len(X_test)})...")
        clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        clf.fit(X_train, y_train)
        
        # 3. Evaluate
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        
        print("\n📊 Model Performance:")
        print(f"   - Accuracy: {acc:.1%}")
        print(classification_report(y_test, y_pred, target_names=['Loss', 'Win']))
        
        # Report Features
        print("\n🔍 Feature Importance:")
        for name, score in zip(X.columns, clf.feature_importances_):
            print(f"   - {name}: {score:.4f}")
            
        # Save (Train on FULL data for production? Or just save this validated one?
        # Usually better to retrain on full data for production, but for now let's save this one)
        model_data = {
            'model': clf,
            'features': features,
            'version': 'v4_real_validated'
        }
        with open(MODEL_OUTPUT_PATH, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"💾 Model V4 saved to {MODEL_OUTPUT_PATH}")
        
        return clf

    except Exception as e:
        print(f"❌ Training failed: {e}")
        raise e

if __name__ == "__main__":
    train_model_v4()
