import joblib
import pandas as pd
import sqlite3
import os
import sys

# Add current directory to path so we can import services if needed, 
# though we might just define helpers here for a standalone test.
sys.path.append(os.getcwd())

from services import get_composition_analysis

DB_PATH = "/opt/clawdbot/projects/LOL-game-analyzer/backend/nexus_sight.db"
MODEL_PATH = "/opt/clawdbot/projects/LOL-game-analyzer/backend/match_predictor_v2.pkl"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def simulate(blue_name, red_name, blue_draft, red_draft):
    print(f"\n🔮 SIMULATING MATCH: {blue_name} (Blue) vs {red_name} (Red)")
    print(f"   Blue Draft: {', '.join(blue_draft)}")
    print(f"   Red Draft:  {', '.join(red_draft)}")
    
    # 1. Load Model
    if not os.path.exists(MODEL_PATH):
        print("❌ Model not found!")
        return
        
    model_data = joblib.load(MODEL_PATH)
    model = model_data['model']
    champ_stats = model_data['champ_stats']
    
    conn = get_db_connection()
    
    # A. Get Team Identity
    def get_identity(team):
        try:
            query = """
            SELECT 
                AVG(golddiffat15) as gd,
                AVG(firstblood) as fb,
                AVG(firstdragon) as fd,
                SUM(dragons) as d,
                SUM(opp_dragons) as od,
                AVG(ckpm) as aggro
            FROM team_stats WHERE teamname = ?
            """
            df = pd.read_sql(query, conn, params=(team,))
            if df.empty or pd.isna(df.iloc[0]['gd']):
                return {'gd': 0.0, 'fb': 0.5, 'fd': 0.5, 'drag': 0.5, 'aggro': 0.8}
            
            row = df.iloc[0]
            # Avoid div by zero
            total_drags = (row['d'] or 0) + (row['od'] or 0)
            drag_rate = (row['d'] or 0) / (total_drags + 0.1)
            return {
                'gd': row['gd'], 
                'fb': row['fb'], 
                'fd': row['fd'], 
                'drag': drag_rate, 
                'aggro': row['aggro']
            }
        except Exception as e:
            print(f"Warning getting identity for {team}: {e}")
            return {'gd': 0.0, 'fb': 0.5, 'fd': 0.5, 'drag': 0.5, 'aggro': 0.8}

    t1_id = get_identity(blue_name)
    t2_id = get_identity(red_name)
    conn.close()
    
    print(f"\n📊 Team Stats (Historic):")
    print(f"   {blue_name}: GD@15 {t1_id['gd']:.1f}, Drag% {t1_id['drag']:.1%}")
    print(f"   {red_name}:  GD@15 {t2_id['gd']:.1f}, Drag% {t2_id['drag']:.1%}")

    # B. Draft Scores
    def get_draft_score(champs):
        if not champs: return 0.5
        scores = [champ_stats.get(c, 0.5) for c in champs if c]
        return sum(scores) / len(scores)

    t1_draft = get_draft_score(blue_draft)
    t2_draft = get_draft_score(red_draft)
    
    print(f"\n🧠 Draft Score (Meta Strength):")
    print(f"   Blue: {t1_draft:.3f} | Red: {t2_draft:.3f}")

    # C. Composition Analysis (Synergy)
    t1_comp = get_composition_analysis(blue_draft)
    t2_comp = get_composition_analysis(red_draft)
    
    print(f"\n🤝 Synergy & Profile:")
    print(f"   Blue: {t1_comp['damage_profile']} (Bonus: {t1_comp['synergy_bonus']})")
    print(f"   Red:  {t2_comp['damage_profile']} (Bonus: {t2_comp['synergy_bonus']})")

    # D. Predict
    # The model strictly wants ['t1_gd15' 't2_gd15' 't1_draft' 't2_draft']
    input_df = pd.DataFrame([{
        't1_gd15': t1_id['gd'], 
        't2_gd15': t2_id['gd'],
        't1_draft': t1_draft, 
        't2_draft': t2_draft
    }])
    
    probs = model.predict_proba(input_df)[0]
    raw_blue_win = probs[1] * 100
    
    synergy_diff = (t1_comp['synergy_bonus'] - t2_comp['synergy_bonus']) * 2.5 
    final_blue_win = max(10, min(90, raw_blue_win + synergy_diff))
    
    print(f"\n🎯 PREDICTION:")
    print(f"   Raw Model Confidence: {raw_blue_win:.1f}% for {blue_name}")
    print(f"   Synergy Adjustment:   {synergy_diff:+.1f}%")
    print(f"   FINAL WIN PROBABILITY: {final_blue_win:.1f}% for {blue_name}")
    
    if final_blue_win > 50:
        print(f"   🏆 WINNER: {blue_name}")
    else:
        print(f"   🏆 WINNER: {red_name}")

if __name__ == "__main__":
    # T1 vs Gen.G Scenario
    # T1: Known for heavy engage/control (Zeus/Oner/Faker/Guma/Keria)
    # Gen.G: Known for Chovy carry + macro
    
    blue_team = "T1"
    red_team = "Gen.G"
    
    # Hypothetical Drafts
    # T1: Standard strong meta (e.g., Ahri/Vi combo)
    blue_picks = ["Jayce", "Vi", "Ahri", "Varus", "Ashe"]
    
    # Gen.G: Scaling/Control
    red_picks = ["K'Sante", "Sejuani", "Azir", "Zeri", "Lulu"]
    
    simulate(blue_team, red_team, blue_picks, red_picks)
