import requests
import os

# 1. Configuration
VERSION = "14.23.1" # Current LoL Patch
SAVE_DIR = "../public/champions" # Saves to your React public folder

# 2. Setup
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

print(f"🚀 Starting download for Patch {VERSION}...")

# 3. Get the list of all champions
response = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{VERSION}/data/en_US/champion.json")
data = response.json()
champions = data['data']

# 4. Loop and Download
count = 0
total = len(champions)

for champ_id in champions:
    # Riot uses "MonkeyKing" for Wukong, but the ID handles that automatically
    url = f"https://ddragon.leagueoflegends.com/cdn/{VERSION}/img/champion/{champ_id}.png"
    
    img_data = requests.get(url).content
    
    with open(f"{SAVE_DIR}/{champ_id}.png", 'wb') as handler:
        handler.write(img_data)
    
    count += 1
    print(f"[{count}/{total}] Downloaded {champ_id}")

print("✅ Done! All icons are in your 'public/champions' folder.")