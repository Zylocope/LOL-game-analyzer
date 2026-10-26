from contextlib import closing
import json
import os
import pickle
import re
import sqlite3

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, log_loss


# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nexus_sight.db")
TAGS_PATH = os.path.join(BASE_DIR, "../data/championTags.ts")
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



# Final aggregate JSON files are deliberately never used for training.
try:
    from .history import History
except ImportError:
    from history import History

MODEL_OUTPUT_PATH = os.path.join(BASE_DIR, 'model_v5.pkl')
REPORT_PATH = os.path.join(BASE_DIR, 'evaluation.json')
VERSION = 'v5_past_only'


def generate_data(db_path=DB_PATH, persist=True):
    with closing(sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)) as conn:
        raw = pd.read_sql('SELECT gameid,date,side,teamname,result,position,champion FROM player_stats', conn)
    raw['date'] = pd.to_datetime(raw['date'], errors='coerce', utc=True)
    raw = raw.dropna(subset=['date', 'champion', 'teamname', 'position', 'side', 'result'])
    raw['position'] = raw.position.map(normalize_position)
    _, classes = load_champion_meta()
    history, dataset = History(), []
    skipped = 0
    positions = {'top', 'jungle', 'mid', 'bot', 'support'}
    for date, batch in raw.sort_values('date').groupby('date'):
        snapshot = history.snapshot()
        pending = []
        for gameid, game in batch.groupby('gameid'):
            blue = game[game.side.str.lower() == 'blue']
            red = game[game.side.str.lower() == 'red']
            valid = all(len(rows) == 5 and set(rows.position) == positions
                        and rows.teamname.nunique() == 1 and rows.result.nunique() == 1
                        and rows.champion.nunique() == 5 for rows in (blue, red))
            if not valid or blue.iloc[0].teamname == red.iloc[0].teamname or set(game.result) != {0, 1}:
                skipped += 1
                continue
            features = []
            for own, enemy in ((blue, red), (red, blue)):
                features.append(get_team_features(own, own.iloc[0].teamname, enemy,
                    snapshot['roles'], classes, snapshot['meta'], .5, snapshot['games'],
                    snapshot['matrix'], snapshot['elo']))
            dataset.append(build_training_row(*features, gameid, date))
            dataset.append(build_training_row(*reversed(features), gameid, date, mirrored=True))
            pending.append((blue, red))
        # Equal timestamps cannot reveal results to one another.
        for blue, red in pending:
            history.update(blue, red)
    df = pd.DataFrame(dataset)
    if df.empty:
        raise ValueError('No complete, dated games in database')
    df = df.sort_values(['date', 'gameid', 'mirrored']).reset_index(drop=True)
    if persist:
        df.to_csv(os.path.join(BASE_DIR, 'dataset_v5.csv'), index=False)
    return df, history.snapshot(), {'skipped_games': skipped, 'games': int(df.gameid.nunique()),
        'first_date': str(df.date.min()), 'last_date': str(df.date.max())}


def chronological_split(df):
    dates = sorted(df.date.unique())
    if len(dates) < 10:
        raise ValueError('At least ten distinct timestamps required for evaluation')
    validation_start = dates[int(len(dates) * .6)]
    test_start = dates[int(len(dates) * .8)]
    return (df[df.date < validation_start].copy(),
            df[(df.date >= validation_start) & (df.date < test_start)].copy(),
            df[df.date >= test_start].copy())


def symmetric_probability(model, frame, features):
    probability = model.predict_proba(frame[features])[:, 1]
    # Rows are paired original/mirrored; deployment uses the same averaging.
    return (probability + 1 - probability.reshape(-1, 2)[:, ::-1].reshape(-1)) / 2


def metrics(frame, probability):
    from sklearn.metrics import brier_score_loss
    # Score actual blue-side games once; mirrors are training augmentation only.
    mask = frame.mirrored.to_numpy() == 0
    target, probability = frame.target.to_numpy()[mask], np.asarray(probability)[mask]
    return {'accuracy': float(accuracy_score(target, probability >= .5)),
            'log_loss': float(log_loss(target, probability, labels=[0, 1])),
            'brier_score': float(brier_score_loss(target, probability)), 'games': int(mask.sum())}


def train_model():
    df, snapshot, data_info = generate_data()
    train, validation, test = chronological_split(df)
    candidates = [dict(n_estimators=n, learning_rate=.05, max_depth=d, random_state=42)
                  for n, d in [(80, 2), (120, 2), (120, 3)]]
    selected = {}
    validation_scores = {}
    for label, features in [('draft_and_elo', MODEL_FEATURES), ('elo_model', ['elo_diff'])]:
        best = None
        for params in candidates:
            model = GradientBoostingClassifier(**params).fit(train[features], train.target)
            score = metrics(validation, symmetric_probability(model, validation, features))
            if best is None or score['log_loss'] < best[0]:
                best = (score['log_loss'], params)
        validation_scores[label] = {"log_loss": float(best[0]), "params": best[1]}
        development = pd.concat([train, validation])
        fitted = GradientBoostingClassifier(**best[1]).fit(development[features], development.target)
        selected[label] = (features, best[1], fitted)
    # Model family and parameters are fixed before reading test outcomes.
    chosen = min(validation_scores, key=lambda label: validation_scores[label]['log_loss'])
    report = {'version': VERSION, 'data': data_info, 'selected_on_validation': chosen, 'validation': validation_scores,
        'protocol': '60/20/20 timestamp split; past-only rolling features; same timestamps isolated; test scored once',
        'limitations': ['Champion class taxonomy is a current static annotation, not patch-versioned.',
                       'Rolling test features include earlier completed test matches (online evaluation).',
                       'No claim of causal draft advantage or betting calibration.'],
        'periods': {name: {'start': str(part.date.min()), 'end': str(part.date.max()),
                          'games': int(part.gameid.nunique())}
                    for name, part in [('train', train), ('validation', validation), ('test', test)]},
        'test': {label: metrics(test, symmetric_probability(model, test, features))
                 for label, (features, _, model) in selected.items()}}
    elo_probability = 1 / (1 + 10 ** (-test.elo_diff.to_numpy() / 400))
    report['test']['elo_formula'] = metrics(test, elo_probability)
    report['test']['draft_log_loss_improvement_over_elo_model'] = (
        report['test']['elo_model']['log_loss'] - report['test']['draft_and_elo']['log_loss'])
    features, params, _ = selected[chosen]
    final_model = GradientBoostingClassifier(**params).fit(df[features], df.target)
    bundle = {'version': VERSION, 'model': final_model, 'features': features,
              'snapshot': snapshot, 'evaluation': report}
    with open(MODEL_OUTPUT_PATH + '.tmp', 'wb') as handle:
        pickle.dump(bundle, handle)
    os.replace(MODEL_OUTPUT_PATH + '.tmp', MODEL_OUTPUT_PATH)
    with open(REPORT_PATH, 'w', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))
    return final_model


