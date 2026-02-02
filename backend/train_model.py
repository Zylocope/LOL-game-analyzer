import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib

DB_PATH = "nexus_sight.db"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    
    print("⏳ Loading Team stats...")
    # 1. Get Match Results (Who won?)
    team_query = """
    SELECT gameid, year, teamname, result, golddiffat15
    FROM team_stats
    WHERE result IS NOT NULL
    """
    teams = pd.read_sql(team_query, conn)
    
    print("⏳ Loading Player stats (Drafts)...")
    # 2. Get Drafts (Who played what?)
    player_query = """
    SELECT gameid, teamname, champion, result
    FROM player_stats
    """
    players = pd.read_sql(player_query, conn)
    conn.close()
    
    return teams, players

def calculate_champion_strength(players_df):
    """
    Creates a 'Tier List' dictionary: { 'Ahri': 0.52, 'Ryze': 0.45, ... }
    Based on historical performance.
    """
    print("💪 Calculating Champion Meta Scores...")
    # Group by Champion and calculate average win rate
    champ_stats = players_df.groupby('champion')['result'].mean()
    # Convert to dictionary for fast lookup
    return champ_stats.to_dict()

def engineer_features(teams_df, players_df):
    print("🛠️ Engineering Draft Features (this takes 10-20s)...")
    
    # 1. Get Meta Scores
    champ_power = calculate_champion_strength(players_df)
    global_avg = 0.5
    
    # 2. Map Champions to their Score
    # "If I pick Ahri, my score +0.52"
    players_df['champ_score'] = players_df['champion'].map(champ_power).fillna(global_avg)
    
    # 3. Calculate Team Draft Power per Match
    # Sum up the 5 champions' scores for each team in each game
    draft_power = players_df.groupby(['gameid', 'teamname'])['champ_score'].mean().reset_index()
    draft_power.rename(columns={'champ_score': 'draft_rating'}, inplace=True)
    
    # 4. Merge Draft Power into Team Stats
    # Now 'teams_df' knows that T1 in Game 123 had a Draft Rating of 0.55
    full_data = pd.merge(teams_df, draft_power, on=['gameid', 'teamname'], how='inner')
    
    # 5. Pivot to "Blue vs Red" format
    # We need one row per game: [Blue_Gold, Blue_Draft, Red_Gold, Red_Draft] -> Blue_Win?
    
    games_list = []
    grouped = full_data.groupby('gameid')
    
    for gameid, group in grouped:
        if len(group) != 2: continue # Skip partial data
        
        # Assume first row is Blue, second is Red (Simplification)
        t1 = group.iloc[0]
        t2 = group.iloc[1]
        
        games_list.append({
            'year': t1['year'],
            # Feature Set 1: Team Skill (History)
            't1_gd15': t1['golddiffat15'],
            't2_gd15': t2['golddiffat15'],
            
            # Feature Set 2: Draft Power (The New Upgrade!)
            't1_draft': t1['draft_rating'],
            't2_draft': t2['draft_rating'],
            
            # Target
            't1_won': t1['result']
        })
        
    return pd.DataFrame(games_list), champ_power

def train():
    teams, players = load_data()
    
    # Prepare Data
    processed_df, champ_dict = engineer_features(teams, players)
    processed_df = processed_df.dropna()
    
    print(f"📊 Training on {len(processed_df)} matches...")
    
    # Split Train (Past) vs Test (2025)
    train_df = processed_df[processed_df['year'] < 2025]
    test_df = processed_df[processed_df['year'] == 2025]
    
    # Define Inputs (X) and Output (Y)
    features = ['t1_gd15', 't2_gd15', 't1_draft', 't2_draft']
    target = 't1_won'
    
    X_train = train_df[features]
    y_train = train_df[target]
    
    X_test = test_df[features]
    y_test = test_df[target]
    
    # Train
    model = LogisticRegression()
    model.fit(X_train, y_train)
    
    # Validate
    acc = accuracy_score(y_test, model.predict(X_test))
    print("\n" + "="*30)
    print(f"🚀 New Model Accuracy: {acc:.1%}")
    print("="*30)
    print("Features used:", features)
    
    # Save Model AND the Champion Stats (We need both for the API)
    joblib.dump({
        'model': model,
        'champ_stats': champ_dict
    }, "match_predictor_v2.pkl")
    print("💾 Saved model + champion data to 'match_predictor_v2.pkl'")

if __name__ == "__main__":
    train()