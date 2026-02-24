import sqlite3
import pandas as pd
import json
import os
from collections import defaultdict

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nexus_sight.db")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "matchup_matrix.json")

def mine_counters():
    print("⛏️  Starting Counter Matrix Mining...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # 1. Fetch All Matchups (Self-Join on GameID + Position)
    # We only care about VALID roles (Top vs Top, Mid vs Mid, etc.)
    # We filter out rare off-meta picks to reduce noise (games < 5?)
    # For now, get EVERYTHING raw.
    query = """
    SELECT 
        p1.champion as my_champ,
        p2.champion as enemy_champ,
        p1.position as role,
        p1.result as win
    FROM player_stats p1
    JOIN player_stats p2 ON p1.gameid = p2.gameid 
    WHERE 
        p1.teamid != p2.teamid AND
        p1.position = p2.position
    """
    
    print("   Querying database for all lane matchups...")
    try:
        # Use chunks if DB is huge, but usually fine for <100k games
        df = pd.read_sql(query, conn)
    except Exception as e:
        print(f"❌ Query failed: {e}")
        conn.close()
        return

    conn.close()
    print(f"   Loaded {len(df)} matchup records.")
    
    if df.empty:
        print("⚠️  No matchup data found!")
        return

    # 2. Normalize Data
    # Convert role 'jng' -> 'jungle', 'sup' -> 'support'
    role_map = {'jng': 'jungle', 'sup': 'support', 'mid': 'mid', 'top': 'top', 'bot': 'bot'}
    df['role'] = df['role'].str.lower().map(lambda x: role_map.get(x, x))
    
    # Normalize champion names (lowercase, remove spaces/punctuation) for robust keys
    # But keep Display Name for JSON output?
    # Better: Use Normalized Key for lookup, store Display Name as well.
    
    # 3. Aggregate Stats
    # Group by [my_champ, enemy_champ, role]
    # Count: Games, Wins
    print("   Aggregating win rates...")
    grouped = df.groupby(['my_champ', 'enemy_champ', 'role']).agg(
        games=('win', 'count'),
        wins=('win', 'sum')
    ).reset_index()
    
    # Calculate Win Rate
    grouped['winRate'] = (grouped['wins'] / grouped['games']) * 100
    
    # 4. Build JSON Structure
    # Structure: { "ahri": { "mid": { "syndra": { "winRate": 48.5, "games": 12 }, ... } } }
    matrix = defaultdict(lambda: defaultdict(dict))
    
    count = 0
    for _, row in grouped.iterrows():
        c1 = row['my_champ'].lower().replace(" ", "").replace("'", "").replace(".", "")
        c2 = row['enemy_champ'].lower().replace(" ", "").replace("'", "").replace(".", "")
        r = row['role']
        
        matrix[c1][r][c2] = {
            "winRate": round(row['winRate'], 1),
            "games": int(row['games']),
            "enemyName": row['enemy_champ'] # Store original name for display
        }
        count += 1
        
    print(f"✅ Matrix built with {count} unique matchup pairs.")
    
    # 5. Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(matrix, f, indent=2)
        
    print(f"💾 Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    mine_counters()
