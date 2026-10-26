import shap
import pickle
import pandas as pd
import numpy as np
import os

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "match_predictor_v4.pkl")
DATASET_PATH = os.path.join(BASE_DIR, "dataset_v4.csv")

def analyze():
    print("🕵️‍♂️ Starting SHAP Analysis...")
    
    # 1. Load Resources
    if not os.path.exists(MODEL_PATH):
        print("❌ Model not found. Train it first.")
        return
        
    with open(MODEL_PATH, 'rb') as f:
        data = pickle.load(f)
        model = data['model']
        features = data['features']
        print(f"✅ Loaded Model (trained on {len(features)} features)")

    if not os.path.exists(DATASET_PATH):
        print("❌ Dataset not found.")
        return
        
    df = pd.read_csv(DATASET_PATH)
    X = df[features]
    
    # 2. Compute SHAP Values
    # We use TreeExplainer for XGBoost/GradientBoosting (it's fast)
    print("🧮 Computing SHAP values (this might take a moment)...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # Note: shap_values for binary classification might be a list [class0, class1] or just class1.
    # For sklearn GradientBoosting, it's usually just the raw log-odds for class 1 if binary.
    # Let's check shape.
    vals = shap_values
    if isinstance(vals, list):
        vals = vals[1] # Class 1 (Win)
        
    # 3. Analyze Directionality
    # We want to know: When Feature X is HIGH, does Win Rate go UP or DOWN?
    
    print("\n📊 SHAP Insights (Direction of Impact):")
    print(f"{'Feature':<20} | {'Impact':<10} | {'Interpretation'}")
    print("-" * 60)
    
    for i, feature in enumerate(features):
        # correlation between feature value and its shap value
        # If corr > 0: Higher Feature -> Higher Win Rate (Good)
        # If corr < 0: Higher Feature -> Lower Win Rate (Bad)
        
        feature_vals = X.iloc[:, i]
        shap_vals = vals[:, i]
        
        corr = np.corrcoef(feature_vals, shap_vals)[0, 1]
        mean_abs_impact = np.mean(np.abs(shap_vals))
        
        direction = "📈 GOOD" if corr > 0 else "📉 BAD"
        strength = abs(corr)
        
        if mean_abs_impact < 0.01:
            impact_desc = "Neutral"
        elif corr > 0.3:
            impact_desc = "Strongly Positive"
        elif corr > 0.1:
            impact_desc = "Positive"
        elif corr < -0.3:
            impact_desc = "Strongly Negative"
        elif corr < -0.1:
            impact_desc = "Negative"
        else:
            impact_desc = "Mixed/Noisy"
            
        print(f"{feature:<20} | {direction}    | {impact_desc}")

if __name__ == "__main__":
    analyze()
