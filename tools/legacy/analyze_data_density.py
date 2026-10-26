
import sqlite3
import pandas as pd
import os

db_path = r"D:\C_analyzer\LOL-game-analyzer\backend\nexus_sight.db"

try:
    conn = sqlite3.connect(db_path)
    
    # Check team game counts
    query_teams = """
    SELECT teamname, COUNT(*) as games
    FROM team_stats 
    GROUP BY teamname 
    ORDER BY games DESC
    """
    df_teams = pd.read_sql(query_teams, conn)
    
    # Check player stats density per team
    # (Approximation: Count player_stats entries per team / 5 roles)
    query_players = """
    SELECT teamname, COUNT(*) as player_entries
    FROM player_stats
    GROUP BY teamname
    ORDER BY player_entries DESC
    """
    df_players = pd.read_sql(query_players, conn)
    
    conn.close()
    
    print(f"Total Teams in DB: {len(df_teams)}")
    print("\n--- Top 20 Data Density ---")
    print(df_teams.head(20))
    
    print("\n--- Distribution ---")
    print(f"Teams with > 100 games: {len(df_teams[df_teams['games'] > 100])}")
    print(f"Teams with > 50 games: {len(df_teams[df_teams['games'] > 50])}")
    print(f"Teams with > 20 games: {len(df_teams[df_teams['games'] > 20])}")
    print(f"Teams with > 10 games: {len(df_teams[df_teams['games'] > 10])}")
    
    # Suggest a cut-off
    print("\n--- Recommendation ---")
    recommended = df_teams[df_teams['games'] >= 30]
    print(f"Teams with >= 30 games (Solid Sample Size): {len(recommended)}")
    
except Exception as e:
    print(e)
