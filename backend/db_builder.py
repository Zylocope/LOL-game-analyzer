import sqlite3
import pandas as pd
import os
import glob

# CONFIG: Matches your folder name "Data"
DATA_FOLDER = "Data"  
DB_PATH = "nexus_sight.db"

def init_db():
    # 1. Find all CSV files in the backend/Data folder
    # We use os.path.join to work on both Windows and Mac
    search_path = os.path.join(os.getcwd(), DATA_FOLDER, "*.csv")
    csv_files = glob.glob(search_path)
    
    if not csv_files:
        # Fallback: try relative path if running from inside backend folder
        csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))

    if not csv_files:
        print(f"❌ No CSV files found in '{DATA_FOLDER}/'.")
        print(f"   Current Working Directory: {os.getcwd()}")
        return

    print(f"📂 Found {len(csv_files)} files.")

    all_data = []

    # 2. Loop through files and combine them
    for file in csv_files:
        print(f"   Reading {os.path.basename(file)}...")
        try:
            df = pd.read_csv(file)
            
            # Filter for Major Regions (LCK, LPL, LEC, LCS) + International
            major_regions = ['LCK', 'LPL', 'LEC', 'LCS', 'MSI', 'W25', 'W24', 'W23', 'W22', 'W21', 'W20', 'W19', 'W18']
            df = df[df['league'].isin(major_regions)]
            
            all_data.append(df)
        except Exception as e:
            print(f"⚠️ Error reading {file}: {e}")

    if not all_data:
        print("❌ No data loaded after filtering. Exiting.")
        return

    # Combine into one giant DataFrame
    master_df = pd.concat(all_data, ignore_index=True)
    
    # 3. Clean Data
    master_df['result'] = pd.to_numeric(master_df['result'], errors='coerce')
    
    # 4. Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    
    print("💾 Writing to database... (this takes 10-20 seconds)")
    
    # Save Team Stats
    teams_df = master_df[master_df['position'] == 'team']
    teams_df.to_sql('team_stats', conn, if_exists='replace', index=False)
    
    # Save Player Stats
    players_df = master_df[master_df['position'] != 'team']
    players_df.to_sql('player_stats', conn, if_exists='replace', index=False)
    
    conn.close()
    print(f"✅ Success! Database built at '{DB_PATH}' with {len(teams_df)} matches.")

if __name__ == "__main__":
    init_db()