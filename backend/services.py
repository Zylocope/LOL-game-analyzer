import sqlite3
import pandas as pd
import json
import os
from typing import Dict, List, Optional
try:
    from .champion_meta import get_champ_profile
except ImportError:
    from champion_meta import get_champ_profile

# Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nexus_sight.db")
MATRIX_PATH = os.path.join(BASE_DIR, "data", "matchup_matrix.json")

# --- LOAD COUNTER MATRIX ---
MATCHUP_MATRIX = {}
if os.path.exists(MATRIX_PATH):
    try:
        with open(MATRIX_PATH, 'r') as f:
            MATCHUP_MATRIX = json.load(f)
        print(f"✅ Loaded {len(MATCHUP_MATRIX)} champions from Matchup Matrix.")
    except Exception as e:
        print(f"❌ Failed to load matchup matrix: {e}")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_mastery_tag(games, win_rate):
    if games < 3: return "New Pick"
    if games >= 10 and win_rate >= 60: return "Signature Pick"
    if games >= 5 and win_rate >= 55: return "Comfort Pick"
    if games >= 5 and win_rate <= 40: return "Weakness"
    return "Standard"

def get_team_stats(team_name: str) -> Dict:
    conn = get_db_connection()
    stats_query = """
    SELECT 
        AVG(result) * 100 as win_rate,
        AVG(golddiffat15) as avg_gd15,
        AVG(dragons) / (AVG(dragons) + AVG(opp_dragons)) * 100 as dragon_control,
        AVG(ckpm) as aggression_score
    FROM team_stats 
    WHERE teamname = ? AND date >= (SELECT datetime(MAX(date), '-365 days') FROM team_stats)
    """
    roster_query = """
    SELECT position, playername
    FROM player_stats
    WHERE teamname = ? 
    AND gameid = (SELECT gameid FROM player_stats WHERE teamname = ? ORDER BY date DESC LIMIT 1)
    """
    try:
        df_stats = pd.read_sql(stats_query, conn, params=(team_name,))
        df_roster = pd.read_sql(roster_query, conn, params=(team_name, team_name))
        conn.close()
        
        recent = not (df_stats.empty or pd.isna(df_stats.iloc[0]['win_rate']))
        if not recent:
            # No games in the last 12 months: use the full history for the roster and style numbers.
            conn = get_db_connection()
            df_stats = pd.read_sql(stats_query.replace(
                "AND date >= (SELECT datetime(MAX(date), '-365 days') FROM team_stats)", ""), conn, params=(team_name,))
            conn.close()
            if df_stats.empty or pd.isna(df_stats.iloc[0]['win_rate']):
                return None

        row = df_stats.iloc[0]
        role_map = {"top": "Top", "jng": "Jungle", "mid": "Mid", "bot": "Bot", "sup": "Support"}
        roster = []
        for _, r in df_roster.iterrows():
            pos = r['position'].lower()
            if pos in role_map:
                roster.append({"role": role_map[pos], "name": r['playername']})
        
        return {
            "winRateSeason": f"{row['win_rate']:.1f}%" if recent else "No games in last 12 months",
            "recentAchievements": ["Data Powered by Oracle's Elixir"],
            "playstyle": f"Aggression: {row['aggression_score']:.1f} kills/min",
            "roster": roster,
            "advancedStats": {
                "goldDiff15": f"{row['avg_gd15']:+.0f}",
                "dragonControl": f"{row['dragon_control']:.0f}%",
                "aggressionRating": int(row['aggression_score'] * 30),
                "firstBloodRate": "N/A" 
            }
        }
    except Exception as e:
        print(f"Error fetching team {team_name}: {e}")
        return None
    finally:
        conn.close()

def get_player_stats(player_name: str, champion: str):
    conn = get_db_connection()
    try:
        query = """
        SELECT COUNT(*) as games_played, SUM(CASE WHEN result = 1 THEN 1 ELSE 0 END) as wins
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
    finally:
        conn.close()


# --- Recent pro statistics (computed from the database, never hard-coded) ---
RECENT_DAYS = 365          # win/pick rates use the last 12 months of pro games in the database
PRIOR_GAMES = 10           # Bayesian smoothing: every champion starts as if it had 10 games at 50%
POS_DB = {"top": "top", "jungle": "jng", "jng": "jng", "mid": "mid", "bot": "bot", "adc": "bot",
          "support": "sup", "sup": "sup"}
_CACHE = {}


def norm_champion(name: str) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def smoothed_win_rate(wins: float, games: float) -> float:
    return round(100.0 * (wins + PRIOR_GAMES * 0.5) / (games + PRIOR_GAMES), 1)


def _recent_window(conn):
    end = conn.execute("SELECT MAX(date) FROM player_stats").fetchone()[0]
    start = conn.execute("SELECT datetime(?, ?)", (end, f"-{RECENT_DAYS} days")).fetchone()[0]
    return start, end


def get_champion_pro_stats(champion: str, role: Optional[str] = None):
    """
    Pro stats for a champion (optionally in one role) over the last 12 months of the database.
    winRate is smoothed toward 50% so small samples don't show extreme numbers; rawWinRate is unsmoothed.
    """
    conn = get_db_connection()
    try:
        start, end = _recent_window(conn)
        role_sql, role_params = "", []
        if role:
            role_sql = "AND position = ?"
            role_params = [POS_DB.get(role.lower(), role.lower())]
        recent = conn.execute(
            f"SELECT COUNT(*) AS g, COALESCE(SUM(result), 0) AS w FROM player_stats "
            f"WHERE champion = ? COLLATE NOCASE AND date >= ? {role_sql}", [champion, start] + role_params).fetchone()
        all_time = conn.execute(
            f"SELECT COUNT(*) AS g FROM player_stats WHERE champion = ? COLLATE NOCASE {role_sql}",
            [champion] + role_params).fetchone()
        games, wins = int(recent["g"]), int(recent["w"])
        if games == 0:
            return None
        return {
            "games": games,
            "winRate": smoothed_win_rate(wins, games),
            "rawWinRate": round(100.0 * wins / games, 1),
            "allTimeGames": int(all_time["g"]),
            "period": f"{start[:10]} to {end[:10]}",
            "mastery_tag": "Pro, last 12 months",
        }
    except Exception as e:
        print(f"Error fetching champion pro stats: {e}")
        return None
    finally:
        conn.close()


def get_recent_champion_table():
    """Win rate, pick rate and role split for every champion over the last 12 months (cached)."""
    if "recent" in _CACHE:
        return _CACHE["recent"]
    conn = get_db_connection()
    try:
        start, end = _recent_window(conn)
        total = conn.execute("SELECT COUNT(DISTINCT gameid) FROM player_stats WHERE date >= ?", (start,)).fetchone()[0]
        rows = conn.execute(
            "SELECT champion, position, COUNT(*) AS g, COALESCE(SUM(result), 0) AS w FROM player_stats "
            "WHERE date >= ? GROUP BY champion, position", (start,)).fetchall()
    finally:
        conn.close()
    champs = {}
    for r in rows:
        c = champs.setdefault(r["champion"], {"games": 0, "wins": 0, "roles": {}})
        c["games"] += r["g"]; c["wins"] += r["w"]; c["roles"][r["position"]] = r["g"]
    data = {
        "from": start[:10], "to": end[:10], "games": total, "priorGames": PRIOR_GAMES,
        "champions": {name: {"games": v["games"], "winRate": smoothed_win_rate(v["wins"], v["games"]),
                             "pickRate": round(100.0 * v["games"] / max(1, total), 1), "roles": v["roles"]}
                      for name, v in champs.items()},
    }
    _CACHE["recent"] = data
    return data


def get_champion_usage():
    """All-time pro games per champion and per position, keyed by normalized name (cached)."""
    if "usage" in _CACHE:
        return _CACHE["usage"]
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT champion, position, COUNT(*) AS g FROM player_stats GROUP BY champion, position").fetchall()
    finally:
        conn.close()
    usage = {}
    for r in rows:
        u = usage.setdefault(norm_champion(r["champion"]), {"games": 0, "roles": {}})
        u["games"] += r["g"]; u["roles"][r["position"]] = r["g"]
    _CACHE["usage"] = usage
    return usage

def get_matchup_stats(my_champ: str, enemy_champ: str, role: str):
    if not my_champ or not enemy_champ: return None
    
    # 1. MATRIX LOOKUP
    c1 = my_champ.lower().replace(" ", "").replace("'", "").replace(".", "")
    c2 = enemy_champ.lower().replace(" ", "").replace("'", "").replace(".", "")
    role_clean = role.replace(" Laner", "").strip().lower()
    role_clean = {'jng': 'jungle', 'sup': 'support', 'mid': 'mid', 'top': 'top', 'bot': 'bot'}.get(role_clean, role_clean)

    if c1 in MATCHUP_MATRIX and role_clean in MATCHUP_MATRIX[c1]:
        if c2 in MATCHUP_MATRIX[c1][role_clean]:
            data = MATCHUP_MATRIX[c1][role_clean][c2]
            win_rate = data['winRate']
            games = data['games']
            if win_rate > 51.0:
                 return {"type": "advantage", "winRate": win_rate, "games": games}
            elif win_rate < 49.0:
                 return {"type": "disadvantage", "winRate": win_rate, "games": games}
            else:
                 return {"type": "neutral", "winRate": win_rate, "games": games}

    # 2. DB FALLBACK
    conn = get_db_connection()
    try:
        role_map = {"Top": "top", "Jungle": "jng", "Mid": "mid", "Bot": "bot", "Support": "sup"}
        db_pos = {"jungle": "jng", "support": "sup"}.get(role.lower(), role.lower())
        query = """
        SELECT COUNT(*) as games, SUM(CASE WHEN p1.result = 1 THEN 1 ELSE 0 END) as wins
        FROM player_stats p1 JOIN player_stats p2 ON p1.gameid = p2.gameid 
        WHERE p1.champion = ? COLLATE NOCASE AND p2.champion = ? COLLATE NOCASE 
        AND p1.position = ? COLLATE NOCASE AND p1.position = p2.position AND p1.teamid != p2.teamid
        """
        df = pd.read_sql(query, conn, params=(my_champ, enemy_champ, db_pos))
        conn.close()

        if df.empty or df.iloc[0]['games'] == 0: return None 
        games = int(df.iloc[0]['games'])
        wins = int(df.iloc[0]['wins'])
        win_rate = (wins / games) * 100
        
        if win_rate >= 50.1: return {"type": "advantage", "winRate": win_rate, "games": games}
        elif win_rate <= 49.9: return {"type": "disadvantage", "winRate": win_rate, "games": games}
        return None
    except Exception as e:
        print(f"Error fetching matchup: {e}")
        return None
    finally:
        conn.close()

def get_composition_analysis(champions: List[str]):
    if not champions or len(champions) != 5:
        return {"damage": "Unknown", "cc": 0, "synergy": 0}

    dmg_counts = {"ad": 0, "ap": 0, "tank": 0, "hybrid": 0, "utility": 0}
    total_cc = 0
    for champ in champions:
        if not champ: continue
        profile = get_champ_profile(champ)
        dmg_type = profile['dmg']
        dmg_counts[dmg_type] = dmg_counts.get(dmg_type, 0) + 1
        total_cc += profile['cc']

    if dmg_counts['ad'] >= 4: dmg_profile = "Heavy AD"
    elif dmg_counts['ap'] >= 4: dmg_profile = "Heavy AP"
    elif dmg_counts['tank'] >= 3: dmg_profile = "Tank Wall"
    else: dmg_profile = "Balanced"

    jng = champions[1]
    mid = champions[2]
    bot = champions[3]
    sup = champions[4]
    
    synergy_score = 0
    conn = get_db_connection()
    try:
        query = """
        SELECT AVG(p1.result) as wr, COUNT(*) as count 
        FROM player_stats p1 JOIN player_stats p2 ON p1.gameid = p2.gameid
        WHERE p1.champion = ? AND p2.champion = ? AND p1.teamid = p2.teamid
        """
        if mid and jng:
            df = pd.read_sql(query, conn, params=(mid, jng))
            if not df.empty and df.iloc[0]['count'] > 5:
                wr = df.iloc[0]['wr']
                if wr > 0.55: synergy_score += 1
                if wr < 0.45: synergy_score -= 1
        if bot and sup:
            df = pd.read_sql(query, conn, params=(bot, sup))
            if not df.empty and df.iloc[0]['count'] > 5:
                wr = df.iloc[0]['wr']
                if wr > 0.55: synergy_score += 1
                if wr < 0.45: synergy_score -= 1
    except Exception as e:
        print(f"Synergy check error: {e}")
    finally:
        conn.close()

    return {"damage_profile": dmg_profile, "cc_score": total_cc, "synergy_bonus": synergy_score}

def get_all_teams() -> List[str]:
    conn = get_db_connection()
    query = """
    SELECT teamname FROM team_stats WHERE teamname != 'NRG Kia'
    GROUP BY teamname HAVING COUNT(*) > 250 OR MAX(date) >= '2024-01-01'
    ORDER BY teamname ASC
    """
    try:
        df = pd.read_sql(query, conn)
        conn.close()
        return df['teamname'].tolist()
    except Exception as e:
        print(f"Error fetching team list: {e}")
        return []
    finally:
        conn.close()
