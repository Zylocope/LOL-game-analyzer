
import sqlite3
import json

db_path = r"D:\C_analyzer\LOL-game-analyzer\backend\nexus_sight.db"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT teamname FROM team_stats GROUP BY teamname HAVING COUNT(*) > 5 ORDER BY teamname ASC")
    teams = [row[0] for row in cursor.fetchall()]
    conn.close()
    print(json.dumps(teams))
except Exception as e:
    print(e)
