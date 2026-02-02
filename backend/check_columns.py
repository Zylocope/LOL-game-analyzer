import sqlite3

DB_PATH = "nexus_sight.db"

def check_columns():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Ask the database for its own structure
        print(f"🕵️ Inspecting {DB_PATH}...")
        cursor.execute("PRAGMA table_info(player_stats)")
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ Error: Table 'player_stats' not found or empty.")
            return

        print("\n✅ Found these columns:")
        found_role_candidate = None
        for col in columns:
            col_name = col[1]
            print(f"   - {col_name}")
            
            # Smart detection
            if col_name.lower() in ['position', 'pos', 'lane', 'role']:
                found_role_candidate = col_name

        print("-" * 30)
        if found_role_candidate:
            print(f"💡 PREDICTION: Your role column is named '{found_role_candidate}'")
        else:
            print("⚠️ I couldn't guess which column stores 'Top/Mid/Jungle'. You need to pick one.")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_columns()