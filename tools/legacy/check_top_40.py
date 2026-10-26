
import sqlite3
import pandas as pd

db_path = r"D:\C_analyzer\LOL-game-analyzer\backend\nexus_sight.db"

try:
    conn = sqlite3.connect(db_path)
    
    # Check what threshold gives us ~40 teams
    query = """
    SELECT teamname, COUNT(*) as games
    FROM team_stats 
    GROUP BY teamname 
    ORDER BY games DESC
    LIMIT 45
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(df)
    print(f"\nGame count of the 40th team: {df.iloc[39]['games']}")
    
except Exception as e:
    print(e)
