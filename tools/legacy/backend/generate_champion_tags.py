import sqlite3
import pandas as pd
import json
import os

# CONFIG
DB_PATH = "/opt/clawdbot/projects/LOL-game-analyzer/backend/nexus_sight.db"
OUTPUT_FILE = "/opt/clawdbot/projects/LOL-game-analyzer/backend/champion_stats.json"

# Manual "Base Truth" for Damage Types (Since CSV doesn't have Physical/Magic split)
# We fix the "Mage includes Marksman" issue here by being specific.
CHAMPION_BASE_INFO = {
    # EXAMPLES OF CORRECTED TYPES
    "Varus": {"class": "Marksman", "dmg_type": "Hybrid"},
    "Kaisa": {"class": "Marksman", "dmg_type": "Hybrid"},
    "Corki": {"class": "Marksman", "dmg_type": "Hybrid"}, # Often Mid, but class is Marksman
    "Azir":  {"class": "Mage", "dmg_type": "Magic"},
    "Ahri":  {"class": "Mage", "dmg_type": "Magic"},
    "Zeri":  {"class": "Marksman", "dmg_type": "Physical"},
    "Ashe":  {"class": "Marksman", "dmg_type": "Physical"},
    "Maokai": {"class": "Tank", "dmg_type": "Magic"},
    "Kante": {"class": "Tank", "dmg_type": "Physical"}, # K'Sante
    "KSante": {"class": "Tank", "dmg_type": "Physical"},
    
    # DEFAULT FALLBACKS (If not in list, we guess based on role)
    # We will expand this list with the script or user can edit the JSON later.
}

def get_damage_type_heuristic(champ_name, primary_role):
    """
    If we don't know the champ, guess based on where they go.
    This is a fallback for the 160+ champs if we don't map them all manually.
    """
    champ = champ_name.lower()
    
    # Known Keywords
    if "lee" in champ or "vi" in champ or "xin" in champ: return "Physical"
    if "ahri" in champ or "ori" in champ or "syn" in champ: return "Magic"
    
    if primary_role == "bot": return "Physical" # 90% are ADCs
    if primary_role == "mid": return "Magic"    # 60% are Mages
    if primary_role == "sup": return "Utility"
    return "Physical" # Top/Jng tilt physical/tank

def generate_meta():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    print("📊 Connecting to Database...")
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Get Play Rates per Position
    print("   Mining role distributions...")
    query = """
    SELECT 
        champion, 
        position, 
        COUNT(*) as games
    FROM player_stats
    GROUP BY champion, position
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Pivot to get: Champion | Top | Jng | Mid | Bot | Sup | Total
    pivot = df.pivot(index='champion', columns='position', values='games').fillna(0)
    pivot['total'] = pivot.sum(axis=1)
    
    champion_data = {}
    
    print(f"   Analyzing {len(pivot)} champions...")
    
    for champ, row in pivot.iterrows():
        total = row['total']
        if total < 10: continue # Skip rare picks
        
        # Calculate % played in each role
        roles = {}
        primary_role = "mid"
        max_pct = 0
        
        for pos in ['top', 'jng', 'mid', 'bot', 'sup']:
            if pos not in row: continue
            pct = (row[pos] / total) * 100
            if pct > 5: # Threshold: Must be played >5% of time to list
                roles[pos] = round(pct, 1)
            
            if pct > max_pct:
                max_pct = pct
                primary_role = pos
                
        # Get Static Info (or guess)
        base_info = CHAMPION_BASE_INFO.get(champ, {})
        dmg_type = base_info.get("dmg_type", get_damage_type_heuristic(champ, primary_role))
        cls = base_info.get("class", "Unknown")
        
        champion_data[champ] = {
            "primary_role": primary_role,
            "viable_roles": roles, # e.g. {"mid": 90.0, "top": 10.0}
            "dmg_type": dmg_type,
            "class": cls,
            "total_pro_games": int(total)
        }

    # Save to JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(champion_data, f, indent=2)
        
    print(f"✅ Generated metadata for {len(champion_data)} champions.")
    print(f"   Saved to: {OUTPUT_FILE}")
    print("   (You can now manually edit this JSON to fix specific damage types!)")

if __name__ == "__main__":
    generate_meta()
