import sqlite3
import pandas as pd

# Connect to the database we just built
conn = sqlite3.connect("/opt/clawdbot/projects/LOL-game-analyzer/backend/nexus_sight.db")

print("--- 📊 TESTING DATABASE: FAKER'S MOST PLAYED ---")

query = """
SELECT 
    champion,
    COUNT(*) as games_played,
    ROUND(AVG(result) * 100, 1) as win_rate,
    ROUND(AVG(dpm), 0) as avg_dpm
FROM player_stats
WHERE playername = 'Faker'
GROUP BY champion
ORDER BY games_played DESC
LIMIT 10;
"""

try:
    df = pd.read_sql(query, conn)
    print(df)
    print("\n✅ If you see champions above, your Data Engineering pipeline is WORKING!")
except Exception as e:
    print(f"❌ Error querying database: {e}")

conn.close()