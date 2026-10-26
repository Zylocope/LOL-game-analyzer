
import sqlite3
import pandas as pd

db_path = r"D:\C_analyzer\LOL-game-analyzer\backend\nexus_sight.db"

try:
    conn = sqlite3.connect(db_path)
    
    # 1. Get Game Counts
    query = """
    SELECT teamname, COUNT(*) as games, MAX(date) as last_game
    FROM team_stats 
    GROUP BY teamname 
    ORDER BY games DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # 2. Filter > 250 games
    veterans = df[df['games'] > 250]
    
    # 3. Define "New Teams" (Active in 2024-2025 but < 250 games)
    # We look for teams whose last game was recent (e.g., after Jan 2024)
    # This captures KC, BDS, Heretics, etc.
    recent_teams = df[
        (df['games'] <= 250) & 
        (df['last_game'] > '2024-01-01')
    ]
    
    print(f"Veterans (>250 games): {len(veterans)}")
    print(veterans['teamname'].tolist())
    
    print(f"\nNew/Active Teams (<250 games, active 2024+): {len(recent_teams)}")
    print(recent_teams['teamname'].tolist())
    
except Exception as e:
    print(e)
