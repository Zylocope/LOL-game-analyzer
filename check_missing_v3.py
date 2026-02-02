
import sqlite3
import os

# 1. Exact Map from Lobby.tsx
TEAM_FILENAME_MAP = {
  "100 Thieves": "100thieves.png",
  "100t": "100thieves.png",
  "Anyone's Legend": "anyone_s_legend.png",
  "Astralis": "astralis.png",
  "Bilibili Gaming": "bilibili_gaming.png",
  "Cloud9": "cloud9.png",
  "Clutch Gaming": "clutch_gaming.png",
  "Counter Logic Gaming": "counter_logic_gaming.png",
  "Dignitas": "dignitas.png",
  "Dire Wolves": "dire_wolves.png",
  "Dplus KIA": "dplus_kia.png",
  "DRX": "drx.png",
  "Echo Fox": "echo_fox.png",
  "EDward Gaming": "edward_gaming.png",
  "Evil Geniuses": "evil_geniuses_na.png",
  "FlyQuest": "flyquest.png",
  "Fnatic": "fnatic.png",
  "FunPlus Phoenix": "funplus_phoenix.png",
  "G2 Esports": "g2esports.png",
  "GAM Esports": "gam_esports.png",
  "Gen.G": "gen_g.png",
  "Golden Guardians": "golden_guardians.png",
  "Hanwha Life Esports": "hanwha_life_esports.png",
  "Immortals": "immortals.png",
  "Invictus Gaming": "invictus_gaming.png",
  "JD Gaming": "jd_gaming.png",
  "Karmine Corp": "karmine_corp.png",
  "Karmine Corp Blue": "karmine_corp_blue.png",
  "KT Rolster": "kt_rolster.png",
  "LGD Gaming": "lgd_gaming.png",
  "LNG Esports": "lngesports.png",
  "LOUD": "loud.png",
  "MAD Lions": "mad_lions.png",
  "MAD Lions KOI": "mad_lions.png",
  "Natus Vincere": "natus_vincere.png",
  "Ninjas in Pyjamas": "ninjas_in_pyjamas_cn.png",
  "Nongshim RedForce": "nongshim_redforce.png",
  "Oh My God": "oh_my_god.png",
  "Oxygen Esports": "oxygen_gaming.png",
  "Rare Atom": "rare_atom.png",
  "Rogue": "rogue.png",
  "Royal Never Give Up": "royal_never_give_up.png",
  "SK Gaming": "sk_gaming.png",
  "T1": "t1.png",
  "Team BDS": "team_bds.png",
  "Team Heretics": "team_heretics.png",
  "Team Liquid": "team_liquid.png",
  "Team WE": "team_we.png",
  "Team Vitality": "teamvitality.png",
  "Top Esports": "top_esports.png",
  "TSM": "tsm.png",
  "Weibo Gaming": "weibo_gaming.png"
}

# 2. Get DB Teams
db_path = r"D:\C_analyzer\LOL-game-analyzer\backend\nexus_sight.db"
db_teams = []
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT teamname FROM team_stats GROUP BY teamname HAVING COUNT(*) > 5 ORDER BY teamname ASC")
    db_teams = [row[0] for row in cursor.fetchall()]
    conn.close()
except:
    pass

# 3. Get Actual Files
files_path = r"D:\C_analyzer\LOL-game-analyzer\public\teams"
existing_files = set(os.listdir(files_path))

# 4. Check Match Logic
missing = []

for team in db_teams:
    found = False
    
    # Priority 1: Map
    if team in TEAM_FILENAME_MAP:
        target = TEAM_FILENAME_MAP[team]
        if target in existing_files:
            found = True
    
    # Priority 2: Snake Case
    if not found:
        snake = team.lower().replace(" ", "_").replace(".", "_") + ".png"
        if snake in existing_files:
            found = True
            
    # Priority 3: Compressed
    if not found:
        compressed = "".join(c.lower() for c in team if c.isalnum()) + ".png"
        if compressed in existing_files:
            found = True
            
    # Priority 4: Clean ID (just spaces removed) + .png
    if not found:
        clean = team.lower().replace(" ", "") + ".png"
        if clean in existing_files:
            found = True

    if not found:
        missing.append(team)

# 5. Output
print(f"Total Missing: {len(missing)}")
for m in missing:
    try:
        print(m)
    except:
        print(m.encode('utf-8'))
