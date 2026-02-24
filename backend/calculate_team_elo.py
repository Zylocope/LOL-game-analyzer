import sqlite3
import pandas as pd
import json
import os

# CONFIG
DB_PATH = "/opt/clawdbot/projects/LOL-game-analyzer/backend/nexus_sight.db"
OUTPUT_FILE = "/opt/clawdbot/projects/LOL-game-analyzer/backend/team_ratings.json"

# 1. Base Elo by Region (The Anchor)
REGION_BASE_ELO = {
    "LCK": 1550, # Korea - The Kings
    "LPL": 1500, # China - The Challengers
    "LEC": 1300, # Europe - The Gatekeepers
    "LCS": 1280, # NA - Fighting for relevance
    "PCS": 1150, # TW/SEA - Strong minor
    "VCS": 1100, # Vietnam - Aggressive but lower macro
    "CBLOL": 1050, # Brazil
    "Lla": 1050,   # LatAm
    "LJL": 1050,   # Japan
    "TCL": 1050,   # Turkey (if present)
    "W": 1400,     # Worlds/MSI (Generic International code sometimes used)
    "MSI": 1400
}

# Teams to manually map if league is missing or weird
TEAM_REGION_MAP = {
    "T1": "LCK", "Gen.G": "LCK", "DK": "LCK", "HLE": "LCK", "KT": "LCK",
    "BLG": "LPL", "JDG": "LPL", "TES": "LPL", "LNG": "LPL", "WBG": "LPL",
    "G2": "LEC", "FNC": "LEC", "MAD": "LEC",
    "TL": "LCS", "C9": "LCS", "FLY": "LCS",
    "PSG": "PCS", "GAM": "VCS"
}

def get_k_factor(rating):
    """Dynamic K-Factor. Higher volatility for lower ranks to allow climbing."""
    if rating > 2400: return 16 # Stabilize at the top
    if rating > 2000: return 24
    return 32 # Volatile at the bottom

def calculate_expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_elo(rating_winner, rating_loser):
    k = get_k_factor(rating_winner)
    expected_winner = calculate_expected_score(rating_winner, rating_loser)
    
    # Standard Elo Update
    change = k * (1 - expected_winner)
    
    return rating_winner + change, rating_loser - change

def run_elo_simulation():
    print("🏆 Calculating Team Elo Ratings...")
    
    if not os.path.exists(DB_PATH):
        print("❌ Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # Get all matches sorted by date (Ascending)
    # We need: gameid, date, teamname, result, league, golddiffat15
    # Since each match has 2 rows (one for each team), we need to pair them.
    query = """
    SELECT gameid, date, teamname, result, league, golddiffat15
    FROM team_stats
    ORDER BY date ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # State Dictionary
    team_ratings = {} # { "T1": 1500 }
    team_regions = {} # { "T1": "LCK" }
    
    # 1. Initialization Pass (Set Base Elo)
    # We scan all teams and assign base Elo based on their PRIMARY league.
    for _, row in df.iterrows():
        team = row['teamname']
        league = row['league']
        
        # Determine Region
        if team not in team_regions:
            # Try map first
            region = TEAM_REGION_MAP.get(team, league)
            team_regions[team] = region
            
            # Set Base Rating
            base = REGION_BASE_ELO.get(region, 1000)
            team_ratings[team] = base

    # 2. Simulation Pass
    # Group by gameid to get match pairs
    matches = df.groupby('gameid')
    
    print(f"   Simulating {len(matches)} matches...")
    
    for gameid, group in matches:
        if len(group) != 2: continue # Skip incomplete data
        
        row1 = group.iloc[0]
        row2 = group.iloc[1]
        
        t1, t2 = row1['teamname'], row2['teamname']
        r1, r2 = team_ratings[t1], team_ratings[t2]
        
        # Determine Winner
        # result is 1 (Win) or 0 (Loss)
        if row1['result'] == 1:
            winner, loser = t1, t2
            w_rating, l_rating = r1, r2
            gold_diff = row1['golddiffat15'] # Positive if T1 led? Wait, need to check side.
            # Actually, golddiffat15 is from perspective of the team.
            # If T1 won, usually positive.
            gd = row1['golddiffat15']
        else:
            winner, loser = t2, t1
            w_rating, l_rating = r2, r1
            gd = row2['golddiffat15']
            
        # Update Elo
        new_w, new_l = update_elo(w_rating, l_rating)
        
        # Bonus: Gold Dominance
        # If winner had > 1000g lead at 15m, give bonus +2 Elo
        if gd and gd > 1000:
            new_w += 2
            
        # Apply
        team_ratings[winner] = new_w
        team_ratings[loser] = new_l

    # 3. Final Polish & Save
    # Sort by Rating
    sorted_teams = sorted(team_ratings.items(), key=lambda x: x[1], reverse=True)
    
    # Format for JSON
    output_data = []
    rank = 1
    for team, rating in sorted_teams:
        output_data.append({
            "rank": rank,
            "team": team,
            "rating": int(rating),
            "region": team_regions.get(team, "Unknown")
        })
        rank += 1
        
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    print("\n👑 TOP 10 TEAMS (Calculated):")
    for i in range(10):
        t = output_data[i]
        print(f"   #{t['rank']} {t['team']} ({t['region']}): {t['rating']}")
        
    print(f"\n✅ Saved ratings to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_elo_simulation()
