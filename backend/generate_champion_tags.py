import requests
import json
import os

# 1. Configuration
VERSION = "14.23.1" # Keep this matched with your icons
URL = f"https://ddragon.leagueoflegends.com/cdn/{VERSION}/data/en_US/champion.json"
OUTPUT_FILE = "../data/championTags.ts"

print(f"⏳ Fetching official data for Patch {VERSION}...")
data = requests.get(URL).json()['data']

# 2. Map Riot Classes to our Tags
# Riot Classes: Fighter, Tank, Mage, Assassin, Marksman, Support
# We want: "ad", "ap", "tank", "utility", etc.

ts_content = """// AUTO-GENERATED FILE. DO NOT EDIT MANUALLY.
// Source: Riot DataDragon API

export interface ChampionData {
  id: string;
  name: string;
  classes: string[];
  tags: string[]; // Our custom simplified tags
}

export const CHAMPION_DATA: Record<string, ChampionData> = {
"""

count = 0
for champ_id, champ_data in data.items():
    name = champ_data['name']
    riot_classes = champ_data['tags'] # e.g. ["Mage", "Support"]
    
    # Generate Custom Tags for Logic
    custom_tags = []
    
    # 1. Damage Type Inference (Rough approximation)
    if "Mage" in riot_classes or "Support" in riot_classes:
        custom_tags.append("ap")
    if "Marksman" in riot_classes or "Fighter" in riot_classes or "Assassin" in riot_classes:
        custom_tags.append("ad")
    if "Tank" in riot_classes:
        custom_tags.append("tank")
        
    # 2. Role Inference
    if "Assassin" in riot_classes: custom_tags.append("burst")
    if "Support" in riot_classes: custom_tags.append("utility")
    if "Fighter" in riot_classes: custom_tags.append("skirmish")
    
    # 3. Special Manual Overrides (Example: Akali is Assassin but AP)
    # You can expand this logic later for hybrid champs like Kai'Sa
    
    # Write to TS string
    classes_str = json.dumps(riot_classes)
    tags_str = json.dumps(custom_tags)
    
    ts_content += f'  "{name}": {{ id: "{champ_id}", name: "{name}", classes: {classes_str}, tags: {tags_str} }},\n'
    count += 1

ts_content += "};\n"

# 3. Save to Frontend Folder
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(ts_content)

print(f"✅ Generated 'championTags.ts' with {count} champions.")