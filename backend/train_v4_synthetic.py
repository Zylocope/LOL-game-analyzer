import json
import os
import pickle
import re
import sqlite3

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, log_loss


# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nexus_sight.db")
TAGS_PATH = os.path.join(BASE_DIR, "../data/championTags.ts")
CHAMP_STATS_PATH = os.path.join(BASE_DIR, "champion_stats_pro.json")
DATASET_OUTPUT_PATH = os.path.join(BASE_DIR, "dataset_v4.csv")
MODEL_OUTPUT_PATH = os.path.join(BASE_DIR, "match_predictor_v4.pkl")
MATRIX_PATH = os.path.join(BASE_DIR, "data", "matchup_matrix.json")
MIN_PRO_GAMES_FOR_CONFIDENT = 50

TRACKED_CLASSES = [
    "assassin",
    "catcher",
    "vanguard",
    "enchanter",
]

MODEL_FEATURES = [
    "elo_diff",
    "blue_score",
    "red_score",
    "blue_total_counter_score",
    "red_total_counter_score",
    "blue_meta_avg",
    "red_meta_avg",
    "blue_off_role_count",
    "red_off_role_count",
    "blue_unknown_role_count",
    "red_unknown_role_count",
    "blue_support_capable_count",
    "red_support_capable_count",
    "blue_jungle_capable_count",
    "red_jungle_capable_count",
    "blue_low_data_count",
    "red_low_data_count",
    "blue_zero_pro_count",
    "red_zero_pro_count",
] + [f"blue_{c}" for c in TRACKED_CLASSES] + [f"red_{c}" for c in TRACKED_CLASSES]


def normalize_name(value: str) -> str:
    return str(value).lower().replace(" ", "").replace("'", "").replace(".", "")


def normalize_position(value: str) -> str:
    value = str(value).lower()
    return {"jng": "jungle", "sup": "support"}.get(value, value)


def load_champion_meta():
    print("Parsing champion roles and classes...")
    if not os.path.exists(TAGS_PATH):
        print("Champion tags not found.")
        return {}, {}

    with open(TAGS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"=\s*({.*})", content, re.DOTALL)
    if not match:
        return {}, {}

    json_str = re.sub(r",(\s*[}\]])", r"\1", match.group(1))

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return {}, {}

    role_map = {}
    class_map = {}
    for name, details in data.items():
        norm_key = normalize_name(name)
        roles = [r.lower() for r in details.get("roles", [])]
        classes = [c.lower() for c in details.get("classes", [])]

        role_map[norm_key] = roles
        role_map[name.lower()] = roles
        class_map[norm_key] = classes
        class_map[name.lower()] = classes

    return role_map, class_map


def load_team_elo():
    ratings_path = os.path.join(BASE_DIR, "team_ratings.json")
    if not os.path.exists(ratings_path):
        return {}

    with open(ratings_path, "r", encoding="utf-8") as f:
        ratings_list = json.load(f)

    elo_map = {}
    for entry in ratings_list:
        norm_name = normalize_name(entry["team"])
        elo_map[norm_name] = entry["rating"]
        elo_map[entry["team"]] = entry["rating"]
    return elo_map


def load_champion_strengths(alpha: float = 50.0):
    """
    Loads champion-level pro meta strength from champion_stats_pro.json.
    Returns:
        meta_map: normalized champ name -> smoothed winrate (0-1)
        global_avg: global average pro winrate (0-1)
        games_map: normalized champ name -> pro games count
    """
    if not os.path.exists(CHAMP_STATS_PATH):
        return {}, 0.5, {}

    with open(CHAMP_STATS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_games = 0
    weighted_wins = 0.0
    for stats in data.values():
        games = max(0, stats.get("pro_games", 0))
        wr = stats.get("pro_win_rate", None)
        if wr is None:
            continue
        total_games += games
        weighted_wins += games * (wr / 100.0)

    global_avg = (weighted_wins / total_games) if total_games > 0 else 0.5

    meta_map = {}
    games_map = {}
    for name, stats in data.items():
        games = max(0, stats.get("pro_games", 0))
        raw_wr = stats.get("pro_win_rate", None)
        base_wr = global_avg if raw_wr is None else raw_wr / 100.0

        denom = games + alpha
        smoothed = (base_wr * games + alpha * global_avg) / denom if denom > 0 else global_avg

        norm_key = normalize_name(name)
        meta_map[norm_key] = smoothed
        meta_map[name.lower()] = smoothed
        games_map[norm_key] = games
        games_map[name.lower()] = games

    return meta_map, global_avg, games_map


def load_matchup_matrix():
    if not os.path.exists(MATRIX_PATH):
        return {}

    with open(MATRIX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_team_features(rows, team_name, enemy_rows, role_map, class_map, champ_meta_map, champ_global_avg, champ_games_map, matchup_matrix, elo_map):
    role_score = 0.0
    class_counts = {c: 0 for c in TRACKED_CLASSES}
    meta_sum = 0.0
    low_data_count = 0
    zero_pro_count = 0
    off_role_count = 0
    unknown_role_count = 0
    support_capable_count = 0
    jungle_capable_count = 0
    champs_by_position = {}

    for _, row in rows.iterrows():
        position = normalize_position(row["position"])
        champion = normalize_name(row["champion"])
        champs_by_position[position] = champion

        valid_roles = role_map.get(champion, [])
        if not valid_roles:
            role_score += 0.0
            unknown_role_count += 1
        elif position in valid_roles:
            role_score += 1.0
        else:
            role_score -= 1.0
            off_role_count += 1

        if "support" in valid_roles:
            support_capable_count += 1
        if "jungle" in valid_roles:
            jungle_capable_count += 1

        meta_val = champ_meta_map.get(champion, champ_global_avg)
        games = champ_games_map.get(champion, 0)
        meta_sum += meta_val * 100.0 - 50.0
        if games == 0:
            zero_pro_count += 1
        elif games < MIN_PRO_GAMES_FOR_CONFIDENT:
            low_data_count += 1

        for champion_class in class_map.get(champion, []):
            if champion_class in class_counts:
                class_counts[champion_class] += 1

    counter_score = 0.0
    for _, enemy_row in enemy_rows.iterrows():
        enemy_position = normalize_position(enemy_row["position"])
        enemy_champion = normalize_name(enemy_row["champion"])
        my_champion = champs_by_position.get(enemy_position)

        if not my_champion:
            continue

        matchup = matchup_matrix.get(my_champion, {}).get(enemy_position, {}).get(enemy_champion)
        if matchup:
            counter_score += matchup["winRate"] - 50.0

    elo = elo_map.get(normalize_name(team_name), elo_map.get(team_name, 1200))
    result = int(rows.iloc[0]["result"])
    meta_avg = meta_sum / max(1, len(rows))

    return {
        "elo": elo,
        "role_score": role_score,
        "result": result,
        "class_counts": class_counts,
        "counter_score": counter_score,
        "meta_avg": meta_avg,
        "low_data_count": low_data_count,
        "zero_pro_count": zero_pro_count,
        "off_role_count": off_role_count,
        "unknown_role_count": unknown_role_count,
        "support_capable_count": support_capable_count,
        "jungle_capable_count": jungle_capable_count,
    }


def build_training_row(blue_features, red_features, gameid, date, mirrored=False):
    row = {
        "gameid": gameid,
        "date": date,
        "mirrored": int(mirrored),
        "elo_diff": blue_features["elo"] - red_features["elo"],
        "blue_score": blue_features["role_score"],
        "red_score": red_features["role_score"],
        "blue_total_counter_score": blue_features["counter_score"],
        "red_total_counter_score": red_features["counter_score"],
        "blue_meta_avg": blue_features["meta_avg"],
        "red_meta_avg": red_features["meta_avg"],
        "target": blue_features["result"],
        "blue_low_data_count": blue_features["low_data_count"],
        "red_low_data_count": red_features["low_data_count"],
        "blue_zero_pro_count": blue_features["zero_pro_count"],
        "red_zero_pro_count": red_features["zero_pro_count"],
        "blue_off_role_count": blue_features["off_role_count"],
        "red_off_role_count": red_features["off_role_count"],
        "blue_unknown_role_count": blue_features["unknown_role_count"],
        "red_unknown_role_count": red_features["unknown_role_count"],
        "blue_support_capable_count": blue_features["support_capable_count"],
        "red_support_capable_count": red_features["support_capable_count"],
        "blue_jungle_capable_count": blue_features["jungle_capable_count"],
        "red_jungle_capable_count": red_features["jungle_capable_count"],
    }

    for champion_class in TRACKED_CLASSES:
        row[f"blue_{champion_class}"] = blue_features["class_counts"][champion_class]
        row[f"red_{champion_class}"] = red_features["class_counts"][champion_class]

    return row


def generate_data():
    print("Building V4 training data from real professional matches...")

    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT gameid, date, side, teamname, result, position, champion
    FROM player_stats
    WHERE gameid IN (
        SELECT gameid
        FROM team_stats
        WHERE year >= 2022 AND datacompleteness = 'complete'
    )
    """
    try:
        df_raw = pd.read_sql(query, conn)
    except Exception as exc:
        print(f"DB read failed: {exc}")
        conn.close()
        return pd.DataFrame()
    finally:
        conn.close()

    role_map, class_map = load_champion_meta()
    elo_map = load_team_elo()
    champ_meta_map, champ_global_avg, champ_games_map = load_champion_strengths()
    matchup_matrix = load_matchup_matrix()

    final_dataset = []
    skipped_games = 0

    for gameid, game_df in df_raw.groupby("gameid"):
        blue_rows = game_df[game_df["side"].str.lower() == "blue"]
        red_rows = game_df[game_df["side"].str.lower() == "red"]

        if len(blue_rows) != 5 or len(red_rows) != 5:
            teams = list(game_df["teamname"].dropna().unique())
            if len(teams) != 2:
                skipped_games += 1
                continue
            blue_rows = game_df[game_df["teamname"] == teams[0]]
            red_rows = game_df[game_df["teamname"] == teams[1]]

        if len(blue_rows) != 5 or len(red_rows) != 5:
            skipped_games += 1
            continue

        blue_name = blue_rows.iloc[0]["teamname"]
        red_name = red_rows.iloc[0]["teamname"]
        date = blue_rows.iloc[0]["date"]

        blue_features = get_team_features(
            blue_rows,
            blue_name,
            red_rows,
            role_map,
            class_map,
            champ_meta_map,
            champ_global_avg,
            champ_games_map,
            matchup_matrix,
            elo_map,
        )
        red_features = get_team_features(
            red_rows,
            red_name,
            blue_rows,
            role_map,
            class_map,
            champ_meta_map,
            champ_global_avg,
            champ_games_map,
            matchup_matrix,
            elo_map,
        )

        final_dataset.append(build_training_row(blue_features, red_features, gameid, date))
        final_dataset.append(build_training_row(red_features, blue_features, gameid, date, mirrored=True))

    df = pd.DataFrame(final_dataset)
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values(["date", "gameid", "mirrored"]).reset_index(drop=True)
    df.to_csv(DATASET_OUTPUT_PATH, index=False)

    real_games = df["gameid"].nunique()
    print(f"Generated {len(df)} rows from {real_games} real games; skipped {skipped_games} incomplete games.")
    print(f"Dataset written to {DATASET_OUTPUT_PATH}")
    return df


def make_recency_weights(dates):
    sorted_dates = pd.Series(pd.to_datetime(dates)).rank(method="dense").to_numpy()
    if len(sorted_dates) == 0 or sorted_dates.max() == sorted_dates.min():
        return np.ones(len(sorted_dates))

    normalized = (sorted_dates - sorted_dates.min()) / (sorted_dates.max() - sorted_dates.min())
    return 0.75 + normalized * 0.5


def time_based_split(df, test_size=0.2):
    unique_games = df[["gameid", "date"]].drop_duplicates().sort_values("date")
    cutoff = max(1, int(len(unique_games) * (1.0 - test_size)))
    train_games = set(unique_games.iloc[:cutoff]["gameid"])
    test_games = set(unique_games.iloc[cutoff:]["gameid"])

    train_df = df[df["gameid"].isin(train_games)].copy()
    test_df = df[df["gameid"].isin(test_games)].copy()
    return train_df, test_df


def train_model_v4():
    try:
        df = generate_data()
        if df.empty:
            return None

        missing_features = [feature for feature in MODEL_FEATURES if feature not in df.columns]
        if missing_features:
            raise ValueError(f"Training data missing model features: {missing_features}")

        train_df, test_df = time_based_split(df)
        X_train = train_df[MODEL_FEATURES]
        y_train = train_df["target"]
        X_test = test_df[MODEL_FEATURES]
        y_test = test_df["target"]
        train_weights = make_recency_weights(train_df["date"])

        candidates = [
            {"n_estimators": 80, "learning_rate": 0.05, "max_depth": 2, "subsample": 0.9},
            {"n_estimators": 120, "learning_rate": 0.05, "max_depth": 2, "subsample": 0.9},
            {"n_estimators": 120, "learning_rate": 0.03, "max_depth": 3, "subsample": 0.85},
            {"n_estimators": 160, "learning_rate": 0.03, "max_depth": 2, "subsample": 0.85},
            {"n_estimators": 200, "learning_rate": 0.02, "max_depth": 2, "subsample": 0.8},
        ]

        print(f"Training candidate models (train rows: {len(train_df)}, test rows: {len(test_df)})...")
        best = None
        for params in candidates:
            clf = GradientBoostingClassifier(random_state=42, **params)
            clf.fit(X_train, y_train, sample_weight=train_weights)

            y_pred = clf.predict(X_test)
            y_prob = clf.predict_proba(X_test)[:, 1]
            acc = accuracy_score(y_test, y_pred)
            loss = log_loss(y_test, y_prob)
            print(f"  params={params} accuracy={acc:.3f} log_loss={loss:.4f}")

            if best is None or loss < best["loss"]:
                best = {"params": params, "accuracy": acc, "loss": loss, "model": clf}

        print("\nBest validation result:")
        print(f"  params={best['params']}")
        print(f"  accuracy={best['accuracy']:.1%}")
        print(f"  log_loss={best['loss']:.4f}")
        print(classification_report(y_test, best["model"].predict(X_test), target_names=["Loss", "Win"]))

        final_weights = make_recency_weights(df["date"])
        final_model = GradientBoostingClassifier(random_state=42, **best["params"])
        final_model.fit(df[MODEL_FEATURES], df["target"], sample_weight=final_weights)

        print("\nFeature importance:")
        for name, score in sorted(zip(MODEL_FEATURES, final_model.feature_importances_), key=lambda item: item[1], reverse=True):
            print(f"  {name}: {score:.4f}")

        model_data = {
            "model": final_model,
            "features": MODEL_FEATURES,
            "version": "v4_blue_red_aligned_time_validated",
            "validation": {
                "accuracy": float(best["accuracy"]),
                "log_loss": float(best["loss"]),
                "params": best["params"],
                "train_rows": int(len(train_df)),
                "test_rows": int(len(test_df)),
            },
        }
        with open(MODEL_OUTPUT_PATH, "wb") as f:
            pickle.dump(model_data, f)

        print(f"Model V4 saved to {MODEL_OUTPUT_PATH}")
        return final_model

    except Exception as exc:
        print(f"Training failed: {exc}")
        raise


if __name__ == "__main__":
    train_model_v4()
