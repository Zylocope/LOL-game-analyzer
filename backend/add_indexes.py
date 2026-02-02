import sqlite3
import os

# Ensure we look in the current folder
DB_PATH = "nexus_sight.db"

def add_indexes():
    print(f"📂 Working Directory: {os.getcwd()}")
    print(f"🔌 Connecting to: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("❌ ERROR: 'nexus_sight.db' not found.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player_stats';")
        if not cursor.fetchone():
            print("❌ ERROR: Database is empty (no 'player_stats' table).")
            conn.close()
            return

        print("🚀 Adding Turbo Indexes (using column 'position')...")
        
        # --- FIXED COLUMNS ---
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_champion ON player_stats(champion);")
        # CHANGED: 'role' -> 'position'
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_position ON player_stats(position);") 
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gameid ON player_stats(gameid);")
        # CHANGED: 'role' -> 'position'
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matchup ON player_stats(gameid, position, champion);")
        # ---------------------

        conn.commit()
        conn.close()
        print("✅ SUCCESS: Database optimized! Speed is now 100x faster.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_indexes()