import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
import os

# DB is in the same folder as the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nexus_sight.db")

def load_data():
    conn = sqlite3.connect(DB_PATH)
    
    print("Loading Team stats and Identity data...")
    # 1. Get Match Results + Identity markers
    # We load historical objective stats to build team profiles
    team_query = """
    SELECT gameid, year, teamname, result, golddiffat15, 
           firstblood, firstdragon, dragons, opp_dragons, ckpm
    FROM team_stats
    WHERE result IS NOT NULL
    """
    teams = pd.read_sql(team_query, conn)
    
    print("Loading Player stats (Drafts)...")
    # 2. Get Drafts
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
    print("Calculating Champion Meta Scores...")
    # Group by Champion and calculate average win rate
    champ_stats = players_df.groupby('champion')['result'].mean()
    # Convert to dictionary for fast lookup
    return champ_stats.to_dict()

def calculate_team_identity(teams_df):
    """
    Calculates historical 'Identity' for each team.
    Returns a dict of team profiles.
    """
    print("Building Team Identity Profiles (FB%, Dragon Control...)...")
    
    # Calculate aggregate stats per team
    profiles = teams_df.groupby('teamname').agg({
        'firstblood': 'mean',
        'firstdragon': 'mean',
        'dragons': 'sum',
        'opp_dragons': 'sum',
        'ckpm': 'mean'
    }).reset_index()
    
    # Derived: Dragon Control Rate
    profiles['drag_rate'] = profiles['dragons'] / (profiles['dragons'] + profiles['opp_dragons'] + 0.1)
    
    # Cleanup
    profiles = profiles[['teamname', 'firstblood', 'firstdragon', 'drag_rate', 'ckpm']]
    profiles.rename(columns={
        'firstblood': 'hist_fb',
        'firstdragon': 'hist_fd',
        'drag_rate': 'hist_drag',
        'ckpm': 'hist_aggro'
    }, inplace=True)
    
    return profiles

def engineer_features(teams_df, players_df):
    print("Engineering Advanced Features...")
    
    # 1. Champion Strength
    champ_power = calculate_champion_strength(players_df)
    players_df['champ_score'] = players_df['champion'].map(champ_power).fillna(0.5)
    
    # 2. Draft Power
    draft_power = players_df.groupby(['gameid', 'teamname'])['champ_score'].mean().reset_index()
    draft_power.rename(columns={'champ_score': 'draft_rating'}, inplace=True)
    
    # 3. Team Identity (Historical)
    team_identity = calculate_team_identity(teams_df)
    
    # 4. Merge all into teams_df
    full_data = pd.merge(teams_df, draft_power, on=['gameid', 'teamname'], how='inner')
    full_data = pd.merge(full_data, team_identity, on='teamname', how='left')
    
    # 5. Pivot to "Blue vs Red"
    games_list = []
    grouped = full_data.groupby('gameid')
    
    for gameid, group in grouped:
        if len(group) != 2: continue
        
        # t1=Blue, t2=Red
        t1 = group.iloc[0]
        t2 = group.iloc[1]
        
        games_list.append({
            'year': t1['year'],
            # Feature Set 1: Early Game Power
            't1_gd15': t1['golddiffat15'],
            't2_gd15': t2['golddiffat15'],
            
            # Feature Set 2: Draft Power
            't1_draft': t1['draft_rating'],
            't2_draft': t2['draft_rating'],
            
            # Feature Set 3: Team Identity (New!)
            't1_fb': t1['hist_fb'],
            't2_fb': t2['hist_fb'],
            't1_drag': t1['hist_drag'],
            't2_drag': t2['hist_drag'],
            't1_aggro': t1['hist_aggro'],
            't2_aggro': t2['hist_aggro'],
            
            # Target
            't1_won': t1['result']
        })
        
    return pd.DataFrame(games_list), champ_power

def train():
    teams, players = load_data()
    
    # Prepare Data
    processed_df, champ_dict = engineer_features(teams, players)
    processed_df = processed_df.dropna()
    
    print(f"Training on {len(processed_df)} matches...")
    
    # Split Train vs Test
    train_df = processed_df[processed_df['year'] < 2025]
    test_df = processed_df[processed_df['year'] == 2025]
    
    # Define Inputs
    features = [
        't1_gd15', 't2_gd15', 
        't1_draft', 't2_draft',
        't1_fb', 't2_fb', 
        't1_drag', 't2_drag',
        't1_aggro', 't2_aggro'
    ]
    target = 't1_won'
    
    X_train = train_df[features]
    y_train = train_df[target]
    
    X_test = test_df[features]
    y_test = test_df[target]
    
    # Train (Using a more robust Logistic Regression)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    
    # Validate
    acc = accuracy_score(y_test, model.predict(X_test))
    print("\n" + "="*30)
    print(f"IDENTITY-AWARE MODEL ACCURACY: {acc:.1%}")
    print("="*30)
    print("New Features Added: FB%, Dragon Control, Aggression Rating")
    
    # Save Model
    joblib.dump({
        'model': model,
        'champ_stats': champ_dict
    }, "match_predictor_v2.pkl")
    print("Saved identity-aware model to 'match_predictor_v2.pkl'")

if __name__ == "__main__":
    train()