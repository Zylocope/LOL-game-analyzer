
import requests
import os
import time

API_KEY = "BSAVUls-OkkKUJ1uKM58W4WtFi0TiLI"
SAVE_DIR = r"D:\C_analyzer\LOL-game-analyzer\public\teams"

# Exact list from user request + previous matches
TARGETS = {
    "100 Thieves": "100thieves.png",
    "Astralis": "astralis.png",
    "Bilibili Gaming": "bilibili_gaming.png",
    "Cloud9": "cloud9.png",
    "DRX": "drx.png",
    "Dignitas": "dignitas.png",
    "Dplus KIA": "dplus_kia.png",
    "Evil Geniuses": "evil_geniuses_na.png",
    "FlyQuest": "flyquest.png",
    "Fnatic": "fnatic.png",
    "G2 Esports": "g2esports.png",
    "Gen.G": "gen_g.png",
    "Hanwha Life Esports": "hanwha_life_esports.png",
    "Immortals": "immortals.png",
    "Invictus Gaming": "invictus_gaming.png",
    "JD Gaming": "jd_gaming.png",
    "KT Rolster": "kt_rolster.png",
    "Karmine Corp": "karmine_corp.png",
    "LNG Esports": "lngesports.png",
    "LOUD": "loud.png",
    "MAD Lions KOI": "mad_lions.png",
    "Ninjas in Pyjamas": "ninjas_in_pyjamas_cn.png",
    "Nongshim RedForce": "nongshim_redforce.png",
    "Rare Atom": "rare_atom.png",
    "Rogue": "rogue.png",
    "SK Gaming": "sk_gaming.png",
    "TSM": "tsm.png",
    "Team BDS": "team_bds.png",
    "Team Liquid": "team_liquid.png",
    "Team Vitality": "teamvitality.png",
    "Team WE": "team_we.png",
    "Top Esports": "top_esports.png",
    "Weibo Gaming": "weibo_gaming.png"
}

headers = {
    "Accept": "application/json",
    "X-Subscription-Token": API_KEY
}

def download_logo_strict(team_name, filename):
    search_url = "https://api.search.brave.com/res/v1/images/search"
    
    # STRICT SEARCH: site:lol.fandom.com ensures we get the clean wiki logos
    query = f"site:lol.fandom.com {team_name} logo png"
    
    params = {
        "q": query,
        "count": 10, 
        "safesearch": "off"
    }
    
    print(f"[{team_name}] Searching Fandom...")
    try:
        r = requests.get(search_url, headers=headers, params=params)
        if r.status_code != 200:
            print(f"  API Error: {r.status_code}")
            return

        data = r.json()
        results = data.get('results', [])
        
        best_url = None
        
        # Heuristic: Find the square or profile logo from the wiki
        for res in results:
            url = res.get('properties', {}).get('url', '')
            title = res.get('title', '').lower()
            
            # Skip "Old" logos if possible, look for standard profile/logo
            if 'old' in title or 'history' in title:
                continue
                
            if 'static.wikia.nocookie.net' in url:
                # This is a raw image url from fandom, usually high quality png
                best_url = url
                break
        
        # Fallback to first result if no wikia specific match (unlikely with site: operator)
        if not best_url and results:
            best_url = results[0].get('properties', {}).get('url')

        if best_url:
            print(f"  Downloading: {best_url}")
            img_r = requests.get(best_url, timeout=10)
            if img_r.status_code == 200:
                full_path = os.path.join(SAVE_DIR, filename)
                with open(full_path, 'wb') as f:
                    f.write(img_r.content)
                print(f"  SAVED: {full_path}")
            else:
                print("  Download failed.")
        else:
            print("  No suitable image found.")

    except Exception as e:
        print(f"  Exception: {e}")

# Run
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

print("Starting Strict Fandom Download...")
for team, fname in TARGETS.items():
    download_logo_strict(team, fname)
    time.sleep(0.5) 
