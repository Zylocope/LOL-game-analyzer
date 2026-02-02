
import sqlite3

db_path = r"D:\C_analyzer\LOL-game-analyzer\backend\nexus_sight.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check for NRG variations
cursor.execute("SELECT DISTINCT teamname FROM team_stats WHERE teamname LIKE '%NRG%'")
nrg_teams = [r[0] for r in cursor.fetchall()]

# Check for Rogue variations
cursor.execute("SELECT DISTINCT teamname FROM team_stats WHERE teamname LIKE '%Rogue%'")
rogue_teams = [r[0] for r in cursor.fetchall()]

# Check for Vici
cursor.execute("SELECT DISTINCT teamname FROM team_stats WHERE teamname LIKE '%Vici%'")
vici_teams = [r[0] for r in cursor.fetchall()]

conn.close()

print(f"NRG Teams in DB: {nrg_teams}")
print(f"Rogue Teams in DB: {rogue_teams}")
print(f"Vici Teams in DB: {vici_teams}")
