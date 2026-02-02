import sqlite3
import pandas as pd
import os

DB_PATH = "nexus_sight.db"

def diagnose():
    print(f"🔍 DIAGNOSTIC REPORT for: {os.path.abspath(DB_PATH)}")
    
    if not os.path.exists(DB_PATH):
        print("❌ CRITICAL ERROR: Database file not found in this folder!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. CHECK COLUMN NAMES
        print("\n--- 1. TABLE COLUMNS (player_stats) ---")
        try:
            cursor.execute("PRAGMA table_info(player_stats)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "position" in columns:
                print(f"✅ FOUND 'position' column (Correct)")
            elif "role" in columns:
                print(f"⚠️ FOUND 'role' column (You need to update code to use 'role')")
            else:
                print(f"❌ ERROR: Neither 'position' nor 'role' found. Columns are:\n{columns}")
                
        except Exception as e:
            print(f"❌ Error checking columns: {e}")

        # 2. CHECK PLAYER NAMES (T1 Sample)
        print("\n--- 2. PLAYER NAME FORMAT (T1 Sample) ---")
        try:
            # We look for T1 to see if it's "Faker" or "T1 Faker"
            query = "SELECT DISTINCT playername, position FROM player_stats WHERE teamname LIKE '%T1%' LIMIT 5"
            df = pd.read_sql(query, conn)
            
            if df.empty:
                print("⚠️ No data found for 'T1'. Trying 'SKT'...")
                query = "SELECT DISTINCT playername, position FROM player_stats WHERE teamname LIKE '%SKT%' LIMIT 5"
                df = pd.read_sql(query, conn)

            if not df.empty:
                print(df)
                name_sample = df.iloc[0]['playername']
                if "T1" in name_sample:
                    print(f"\n⚠️ WARNING: Names include Team Tag (e.g. '{name_sample}')")
                    print("   -> Fix: You need to adjust queries to add 'T1 %' or strip it.")
                else:
                    print(f"\n✅ SUCCESS: Names are clean (e.g. '{name_sample}')")
            else:
                print("❌ ERROR: Could not find any T1/SKT players. Database might be empty or use different team codes.")

        except Exception as e:
            print(f"❌ Error checking names: {e}")

        conn.close()

    except Exception as e:
        print(f"❌ Fatal Connection Error: {e}")

if __name__ == "__main__":
    diagnose()