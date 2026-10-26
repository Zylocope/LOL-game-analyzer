import sqlite3
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('D:/C_analyzer/LOL-game-analyzer/backend/nexus_sight.db')
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT teamname FROM team_stats GROUP BY teamname HAVING COUNT(*) > 5 ORDER BY teamname ASC')
teams = cursor.fetchall()

print("--- TEAM LIST ---")
for t in teams:
    print(t[0])
