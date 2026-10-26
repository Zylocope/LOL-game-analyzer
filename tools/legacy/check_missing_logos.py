
import sqlite3
import os

# 1. Connect to DB and get all teams
db_path = r"D:\C_analyzer\LOL-game-analyzer\backend\nexus_sight.db"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT teamname FROM team_stats GROUP BY teamname HAVING COUNT(*) > 5 ORDER BY teamname ASC")
    db_teams = [row[0] for row in cursor.fetchall()]
    conn.close()
except Exception as e:
    print(f"Error reading DB: {e}")
    db_teams = []

# 2. Get existing files
files_path = r"D:\C_analyzer\LOL-game-analyzer\public\teams"
try:
    existing_files = set(os.listdir(files_path))
except Exception as e:
    print(f"Error reading directory: {e}")
    existing_files = set()

# 3. Check for missing logos using the logic from Lobby.tsx
missing_teams = []
logo_map = {}

for team in db_teams:
    # Logic from Lobby.tsx
    # 1. Snake Case
    snake = team.lower().replace(" ", "_").replace(".", "_") + ".png"
    # 2. Compressed
    compressed = "".join(c.lower() for c in team if c.isalnum()) + ".png"
    # 3. Clean ID (approximate)
    clean_id = team.lower().replace(" ", "") + ".png"
    
    # Check if ANY of these exist
    if snake in existing_files:
        logo_map[team] = snake
    elif compressed in existing_files:
        logo_map[team] = compressed
    elif clean_id in existing_files:
        logo_map[team] = clean_id
    else:
        # Check against manual mappings seen in previous turns if needed, 
        # but for now we want raw missing files.
        missing_teams.append(team)

print(f"Total Teams in DB: {len(db_teams)}")
print(f"Missing Logos: {len(missing_teams)}")
print("-" * 30)
for t in missing_teams:
    print(t)
