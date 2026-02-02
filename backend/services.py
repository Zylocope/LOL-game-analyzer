import sqlite3
import pandas as pd
from typing import Dict, List, Optional
import os
from .champion_meta import get_champ_profile

# Database is in the backend folder
DB_PATH = os.path.join("backend", "nexus_sight.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_mastery_tag(games, win_rate):
    """Helpers to assign a 'Badge' to the player"""
    if games < 3: return "New Pick"
    if games >= 10 and win_rate >= 60: return "Signature Pick"
    if games >= 5 and win_rate >= 55: return "Comfort Pick"
    if games >= 5 and win_rate <= 40: return "Weakness"
    return "Standard"

def get_team_stats(team_name: str) -> Dict:
    """
    Fetches aggregated stats and the most recent roster for a specific team.
    """
    conn = get_db_connection()
    
    # 1. Fetch Stats
    stats_query = """
    SELECT 
        AVG(result) * 100 as win_rate,
        AVG(golddiffat15) as avg_gd15,
        AVG(dragons) / (AVG(dragons) + AVG(opp_dragons)) * 100 as dragon_control,
        AVG(ckpm) as aggression_score
    FROM team_stats 
    WHERE teamname = ? 
    """
    
    # 2. Fetch Most Recent Roster (Top, Jng, Mid, Bot, Sup)
    # We find the most recent game for this team and get the players from it
    roster_query = """
    SELECT position, playername
    FROM player_stats
    WHERE teamname = ? 
    AND gameid = (SELECT gameid FROM player_stats WHERE teamname = ? ORDER BY date DESC LIMIT 1)
    """
    
    try:
        # Get Stats
        df_stats = pd.read_sql(stats_query, conn, params=(team_name,))
        
        # Get Roster
        df_roster = pd.read_sql(roster_query, conn, params=(team_name, team_name))
        conn.close()
        
        if df_stats.empty or pd.isna(df_stats.iloc[0]['win_rate']):
            return None
            
        row = df_stats.iloc[0]
        
        # Format Roster
        role_map = {"top": "Top", "jng": "Jungle", "mid": "Mid", "bot": "Bot", "sup": "Support"}
        roster = []
        for _, r in df_roster.iterrows():
            pos = r['position'].lower()
            if pos in role_map:
                roster.append({"role": role_map[pos], "name": r['playername']})
        
        # Ensure correct order if possible, though draft board handles it
        
        return {
            "winRateSeason": f"{row['win_rate']:.1f}%",
            "recentAchievements": ["Data Powered by Oracle's Elixir"],
            "playstyle": f"Aggression: {row['aggression_score']:.1f} kills/min",
            "roster": roster,
            "advancedStats": {
                "goldDiff15": f"{row['avg_gd15']:+.0f}",
                "dragonControl": f"{row['dragon_control']:.0f}%",
                "aggressionRating": int(row['aggression_score'] * 30),
                "firstBloodRate": "50%" 
            }
        }
    except Exception as e:
        print(f"Error fetching team {team_name}: {e}")
        return None

def get_player_stats(player_name: str, champion: str):
    """
    Calculates a specific player's historical performance on a specific champion.
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT 
            COUNT(*) as games_played,
            SUM(CASE WHEN result = 1 THEN 1 ELSE 0 END) as wins
        FROM player_stats 
        WHERE playername = ? COLLATE NOCASE AND champion = ? COLLATE NOCASE
        """
        
        df = pd.read_sql(query, conn, params=(player_name, champion))
        conn.close()

        if df.empty or df.iloc[0]['games_played'] == 0:
            return None

        games = int(df.iloc[0]['games_played'])
        wins = int(df.iloc[0]['wins'])
        win_rate = (wins / games) * 100

        return {
            "found": True,
            "games": games,
            "winRate": round(win_rate, 1),
            "mastery_tag": get_mastery_tag(games, win_rate)
        }
        
    except Exception as e:
        print(f"Error fetching player stats: {e}")
        return None

def get_matchup_stats(my_champ: str, enemy_champ: str, role: str):
    conn = get_db_connection()
    try:
        role_map = {
            "Top": "top",
            "Jungle": "jng",  
            "Mid": "mid",
            "Bot": "bot",
            "Support": "sup"  
        }
        
        clean_role = role.replace(" Laner", "").strip()
        db_pos = role_map.get(clean_role, clean_role.lower())

        print(f"   Searching: {my_champ} vs {enemy_champ} in position '{db_pos}'...")

        query = """
        SELECT 
            COUNT(*) as games,
            SUM(CASE WHEN p1.result = 1 THEN 1 ELSE 0 END) as wins
        FROM player_stats p1
        JOIN player_stats p2 ON p1.gameid = p2.gameid 
        WHERE 
            p1.champion = ? COLLATE NOCASE AND 
            p2.champion = ? COLLATE NOCASE AND 
            p1.position = ? COLLATE NOCASE AND 
            p1.position = p2.position
        """
        
        df = pd.read_sql(query, conn, params=(my_champ, enemy_champ, db_pos))
        conn.close()

        if df.empty or df.iloc[0]['games'] == 0:
            print(f"   No games found.")
            return None 

        games = int(df.iloc[0]['games'])
        wins = int(df.iloc[0]['wins'])
        win_rate = (wins / games) * 100
        
        print(f"   FOUND: {win_rate:.1f}% Win Rate over {games} games")

        if win_rate >= 50.1:
            return {"type": "advantage", "winRate": win_rate, "games": games}
        elif win_rate <= 49.9:
            return {"type": "disadvantage", "winRate": win_rate, "games": games}
        else:
            return None

    except Exception as e:
        print(f"Error fetching matchup: {e}")
        return None

def get_composition_analysis(champions: List[str]):
    """
    Analyzes a list of 5 champions for Damage Profile and Synergy.
    """
    if not champions or len(champions) != 5:
        return {"damage": "Unknown", "cc": 0, "synergy": 0}

    # 1. Profile Analysis (AD/AP/Tank)
    dmg_counts = {"ad": 0, "ap": 0, "tank": 0, "hybrid": 0, "utility": 0}
    total_cc = 0
    
    for champ in champions:
        if not champ: continue
        profile = get_champ_profile(champ)
        dmg_type = profile['dmg']
        dmg_counts[dmg_type] = dmg_counts.get(dmg_type, 0) + 1
        total_cc += profile['cc']

    # Classify Team Type
    if dmg_counts['ad'] >= 4:
        dmg_profile = "Heavy AD"
    elif dmg_counts['ap'] >= 4:
        dmg_profile = "Heavy AP"
    elif dmg_counts['tank'] >= 3:
        dmg_profile = "Tank Wall"
    else:
        dmg_profile = "Balanced"

    # 2. Synergy Analysis (Mid+Jng, Bot+Sup)
    # Positions are fixed in the list: [Top, Jng, Mid, Bot, Sup]
    jng = champions[1]
    mid = champions[2]
    bot = champions[3]
    sup = champions[4]
    
    synergy_score = 0
    pairs_found = 0
    
    conn = get_db_connection()
    try:
        # Check Mid-Jungle
        query = """
        SELECT AVG(p1.result) as wr, COUNT(*) as count 
        FROM player_stats p1 JOIN player_stats p2 ON p1.gameid = p2.gameid
        WHERE p1.champion = ? AND p2.champion = ? AND p1.teamid = p2.teamid
        """
        
        # Mid-Jungle Check
        if mid and jng:
            df = pd.read_sql(query, conn, params=(mid, jng))
            if not df.empty and df.iloc[0]['count'] > 5:
                wr = df.iloc[0]['wr']
                if wr > 0.55: synergy_score += 1
                if wr < 0.45: synergy_score -= 1
                pairs_found += 1

        # Bot-Sup Check
        if bot and sup:
            df = pd.read_sql(query, conn, params=(bot, sup))
            if not df.empty and df.iloc[0]['count'] > 5:
                wr = df.iloc[0]['wr']
                if wr > 0.55: synergy_score += 1
                if wr < 0.45: synergy_score -= 1
                pairs_found += 1
                
    except Exception as e:
        print(f"Synergy check error: {e}")
    finally:
        conn.close()

    return {
        "damage_profile": dmg_profile,
        "cc_score": total_cc,
        "synergy_bonus": synergy_score
    }

def get_all_teams() -> List[str]:
    conn = get_db_connection()
    # Filter: >250 games OR Active in 2024+ (New teams)
    # Explicitly exclude "NRG Kia" as it is an incorrect naming mix-up.
    query = """
    SELECT teamname 
    FROM team_stats 
    WHERE teamname != 'NRG Kia'
    GROUP BY teamname 
    HAVING COUNT(*) > 250 OR MAX(date) >= '2024-01-01'
    ORDER BY teamname ASC
    """
    try:
        df = pd.read_sql(query, conn)
        conn.close()
        return df['teamname'].tolist()
    except Exception as e:
        print(f"Error fetching team list: {e}")
        return []
