import sqlite3
import pandas as pd
import json
import os
import urllib.request

# CONFIG
DB_PATH = "/opt/clawdbot/projects/LOL-game-analyzer/backend/nexus_sight.db"
OUTPUT_FILE = "/opt/clawdbot/projects/LOL-game-analyzer/backend/champion_stats_pro.json"
MERAKI_RATES_URL = "https://cdn.merakianalytics.com/riot/lol/resources/latest/en-US/championrates.json"

def generate_stats():
    print("📊 Mining PRO Stats from Database...")
    if not os.path.exists(DB_PATH):
        print("❌ Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # 1. Calculate Pro Win Rates & Pick Counts
    query = """
    SELECT 
        champion, 
        COUNT(*) as games_played,
        SUM(CASE WHEN result = 1 THEN 1 ELSE 0 END) as wins
    FROM player_stats
    GROUP BY champion
    HAVING games_played > 5
    """
    df = pd.read_sql(query, conn)
    
    # Get Total Match Count to calc Pick Rate
    total_matches = pd.read_sql("SELECT COUNT(*) as count FROM team_stats", conn).iloc[0]['count'] // 2
    print(f"   Based on {total_matches} pro matches.")
    
    pro_stats = {}
    for _, row in df.iterrows():
        champ = row['champion']
        games = int(row['games_played'])
        wins = int(row['wins'])
        win_rate = round((wins / games) * 100, 1)
        pick_rate = round((games / total_matches) * 100, 1)
        
        pro_stats[champ] = {
            "pro_win_rate": win_rate,
            "pro_pick_rate": pick_rate,
            "pro_games": games
        }
        
    conn.close()
    
    # 2. Fetch Global Pick Rates (Meraki)
    print("🌍 Fetching GLOBAL Stats from Meraki...")
    global_stats = {}
    try:
        with urllib.request.urlopen(MERAKI_RATES_URL) as url:
            data = json.loads(url.read().decode())['data']
            
            # Meraki uses IDs (e.g. "266"), we need to map to Names if possible.
            # But we can just store by ID and let the frontend map it if we have ID map.
            # Wait, our `championTags.ts` uses Names as keys. 
            # We need an ID -> Name map.
            
            # Let's load the champion list we downloaded earlier to map ID->Name
            with open("/opt/clawdbot/projects/LOL-game-analyzer/backend/datadragon_champions.json", 'r') as f:
                dd_data = json.load(f)['data']
                
            id_to_name = {v['key']: v['name'] for k, v in dd_data.items()}
            
            for cid, rates in data.items():
                if cid in id_to_name:
                    name = id_to_name[cid]
                    # Sum pick rates across roles
                    total_pr = sum([r.get('playRate', 0) for r in rates.values()])
                    global_stats[name] = {
                        "global_pick_rate": round(total_pr, 1)
                    }
                    
    except Exception as e:
        print(f"⚠️ Failed to fetch Global Stats: {e}")

    # 3. Merge & Save
    final_stats = {}
    all_champs = set(pro_stats.keys()) | set(global_stats.keys())
    
    for champ in all_champs:
        p = pro_stats.get(champ, {"pro_win_rate": 0, "pro_pick_rate": 0, "pro_games": 0})
        g = global_stats.get(champ, {"global_pick_rate": 0})
        
        # We don't have Global Win Rate source yet (requires scraping), 
        # so we set it to 0 or null to indicate missing.
        
        final_stats[champ] = {
            **p,
            **g,
            "global_win_rate": None # Placeholder
        }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_stats, f, indent=2)
        
    print(f"✅ Saved stats for {len(final_stats)} champions to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_stats()
