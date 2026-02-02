# Simplified Metadata for Feature Engineering
# In a real production app, this would be a database table or fetched from Riot API.

# Class -> Damage/CC Mapping
CLASS_DEFAULTS = {
    "Mage": {"dmg": "ap", "cc": 2},
    "Support": {"dmg": "utility", "cc": 2},
    "Tank": {"dmg": "tank", "cc": 3},
    "Fighter": {"dmg": "ad", "cc": 1},
    "Marksman": {"dmg": "ad", "cc": 0},
    "Assassin": {"dmg": "ad", "cc": 1},
}

# Manual Overrides for "Rule Breakers"
CHAMPION_OVERRIDES = {
    "Akali": {"dmg": "ap", "cc": 1},
    "Katarina": {"dmg": "ap", "cc": 0},
    "Sylas": {"dmg": "ap", "cc": 2},
    "Gwen": {"dmg": "ap", "cc": 1},
    "Mordekaiser": {"dmg": "ap", "cc": 2},
    "Rumble": {"dmg": "ap", "cc": 2},
    "Vladimir": {"dmg": "ap", "cc": 1},
    "Karthus": {"dmg": "ap", "cc": 1},
    "Nidalee": {"dmg": "ap", "cc": 0},
    "Elise": {"dmg": "ap", "cc": 2},
    "Evelynn": {"dmg": "ap", "cc": 1},
    "Fiddlesticks": {"dmg": "ap", "cc": 3},
    "Lillia": {"dmg": "ap", "cc": 2},
    "Taliyah": {"dmg": "ap", "cc": 2},
    "Corki": {"dmg": "hybrid", "cc": 1},
    "Ezreal": {"dmg": "hybrid", "cc": 0},
    "Kaisa": {"dmg": "hybrid", "cc": 0},
    "KogMaw": {"dmg": "hybrid", "cc": 0},
    "Varus": {"dmg": "hybrid", "cc": 2},
    "Kayle": {"dmg": "hybrid", "cc": 1},
    "Jax": {"dmg": "hybrid", "cc": 1},
    "Shaco": {"dmg": "ad", "cc": 2},
    "Teemo": {"dmg": "ap", "cc": 1},
}

def get_champ_profile(name):
    """
    Returns {'dmg': 'ad'|'ap'|'tank', 'cc': int}
    """
    if name in CHAMPION_OVERRIDES:
        return CHAMPION_OVERRIDES[name]
    
    # Fallback: Assume Fighter/AD if unknown (most common)
    return {"dmg": "ad", "cc": 1}
