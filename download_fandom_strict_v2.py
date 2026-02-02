
import requests
import os
import time
import re

TARGETS = [
    ("Ascension Gaming", "ascensiongaming.png"),
    ("BNK FEARX", "bnkfearx.png"),
    ("BRION", "brion.png"),
    ("Bombers", "bombers.png"),
    ("CTBC Flying Oyster", "ctbcflyingoyster.png"),
    ("DetonatioN FocusMe", "detonationfocusme.png"),
    ("DN Freecs", "dnfreecs.png"),
    ("Dominus Esports", "dominusesports.png"),
    ("ES Sharks", "essharks.png"),
    ("EVOS Esports", "evosesports.png"),
    ("Ever8 Winners", "ever8winners.png"),
    ("Excel Esports", "excelesports.png"),
    ("FC Schalke 04 Esports", "fcschalke04esports.png"),
    ("FURIA", "furia.png"),
    ("Fenerbahçe Esports", "fenerbaheesports.png"),
    ("Flash Wolves", "flash_wolves.png"),
    ("Gambit Esports", "gambitesports.png"),
    ("GiantX", "giantx.png"),
    ("Griffin", "griffin.png"),
    ("INTZ", "intz.png"),
    ("Isurus", "isurus.png"),
    ("Jin Air Green Wings", "jinairgreenwings.png"),
    ("KOI", "koi.png"),
    ("KSV eSports", "ksvesports.png"),
    ("KaBuM! Esports", "kabumesports.png"),
    ("Kaos Latin Gamers", "kaoslatingamers.png"),
    ("Kingzone DragonX", "kingzonedragonx.png"),
    ("Kongdoo Monster", "kongdoomonster.png"),
    ("Liiv SANDBOX", "liivsandbox.png"),
    ("MEGA", "mega.png"),
    ("MVP", "mvp.png"),
    ("Misfits Gaming", "misfits_gaming.png"),
    ("Movistar KOI", "movistarkoi.png"),
    ("Movistar R7", "movistarr7.png"),
    ("NRG Kia", "nrgkia.png"),
    ("OKSavingsBank BRION", "oksavingsbankbrion.png"),
    ("OpTic Gaming", "optic_gaming.png"),
    ("Origen", "origen.png"),
    ("PENTAGRAM", "pentagram.png"),
    ("Papara SuperMassive", "paparasupermassive.png"),
    ("Pentanet.GG", "pentanetgg.png"),
    ("Phong Vũ Buffalo", "phongvbuffalo.png"),
    ("ROX Tigers", "roxtigers.png"),
    ("Rogue Warriors", "roguewarriors.png"),
    ("SK Telecom T1", "sktelecomt1.png"),
    ("SeolHaeOne Prince", "seolhaeoneprince.png"),
    ("Seorabeol Gaming", "seorabeolgaming.png"),
    ("Shopify Rebellion", "shopifyrebellion.png"),
    ("SinoDragon Gaming", "sinodragongaming.png"),
    ("Snake Esports", "snakeesports.png"),
    ("Splyce", "splyce.png"),
    ("Suning", "suning.png"),
    ("TALON", "talon.png"),
    ("Team BattleComics", "teambattlecomics.png"),
    ("Team Dynamics", "teamdynamics.png"),
    ("ThunderTalk Gaming", "thundertalkgaming.png"),
    ("Ultra Prime", "ultraprime.png"),
    ("Unicorns of Love.CIS", "unicornsoflovecis.png"),
    ("VSG", "vsg.png"),
    ("Vega Squadron", "vegasquadron.png"),
    ("Vici Gaming", "vicigaming.png"),
    ("Victory Five", "victoryfive.png"),
    ("bbq Olivers", "bbqolivers.png"),
    ("eStar", "estar.png"),
    ("Infinity", "inf.png"),
    ("paiN Gaming", "paingaming.png"),
    ("İstanbul Wildcats", "istanbulwildcats.png")
]

SAVE_DIR = r"D:\C_analyzer\LOL-game-analyzer\public\teams"

def get_fandom_logo(team_name, filename):
    # Try 1: Direct Profile Image URL Pattern
    # This is the cleanest high-res source usually
    base_urls = [
        f"https://lol.fandom.com/wiki/Special:FilePath/{team_name.replace(' ', '_')}logo_square.png",
        f"https://lol.fandom.com/wiki/Special:FilePath/{team_name.replace(' ', '_')}logo_std.png",
        f"https://lol.fandom.com/wiki/Special:FilePath/{team_name.replace(' ', '_')}logo_profile.png"
    ]
    
    print(f"Processing: {team_name}...")
    
    found_url = None
    
    # Method 1: Check Special:FilePath redirects
    for url in base_urls:
        try:
            r = requests.head(url, allow_redirects=True, timeout=5)
            if r.status_code == 200 and 'image' in r.headers.get('Content-Type', ''):
                found_url = r.url # The final redirected URL
                # Ensure it's not the "placeholder" image
                if "site-logo" not in found_url and "Logo_Placeholder" not in found_url:
                    break
                else:
                    found_url = None
        except:
            pass
            
    # Method 2: Scrape the wiki page if Method 1 fails
    if not found_url:
        wiki_url = f"https://lol.fandom.com/wiki/{team_name.replace(' ', '_')}"
        try:
            r = requests.get(wiki_url, timeout=5)
            if r.status_code == 200:
                # Regex to find the infobox image
                # Look for <img ... src="..." ... class="pi-image-thumbnail" ... >
                match = re.search(r'class="pi-image-thumbnail"[\s\S]*?src="(https://static\.wikia\.nocookie\.net/[^"]+)"', r.text)
                if match:
                    found_url = match.group(1)
                    # Clean up /revision/ scale params to get original
                    # usually just removing everything after .png/
                    if "/revision/" in found_url:
                         found_url = found_url.split("/revision/")[0]
        except Exception as e:
            print(f"  Wiki scrape error: {e}")

    # Download if found
    if found_url:
        try:
            print(f"  Downloading: {found_url}")
            img_r = requests.get(found_url, timeout=10)
            if img_r.status_code == 200:
                full_path = os.path.join(SAVE_DIR, filename)
                with open(full_path, 'wb') as f:
                    f.write(img_r.content)
                print(f"  [SUCCESS] Saved to {filename}")
            else:
                print(f"  [FAIL] Status code {img_r.status_code}")
        except Exception as e:
            print(f"  [ERROR] {e}")
    else:
        print("  [SKIP] No logo found on Fandom.")

# Execution
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

for team, fname in TARGETS:
    get_fandom_logo(team, fname)
    time.sleep(0.5) # Polite delay
