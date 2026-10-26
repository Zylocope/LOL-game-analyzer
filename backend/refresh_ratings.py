"""Refresh the served model's ratings with every game in the database. The fitted model is NOT retrained.

    python -m backend.refresh_ratings

Why: the v6 estimator was frozen and tested once on sealed 2026 games. After that test, the live app should rate
teams, players and form on the newest results. This replays the same rating/feature history (with the K-factor and
season shrink chosen during development) through the latest game, swaps in the new state, and keeps the estimator,
feature list and evaluation exactly as they were. It also rebuilds team_ratings.json and attaches the sealed 2026
holdout result so the app can show it.

The original bundle is kept once as model_v6.original.pkl.
"""
import json
import os
import pickle
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

from .features import normalize, read_games, replay

BASE = Path(__file__).resolve().parent
MODEL = BASE / "model_v6.pkl"
BACKUP = BASE / "model_v6.original.pkl"
DB = BASE / "nexus_sight.db"
RATINGS = BASE / "team_ratings.json"
HOLDOUT = BASE.parent / "scripts" / "v7" / "final_report.json"
REGION = {"LCK": "LCK", "LPL": "LPL", "LEC": "LEC", "LCS": "LCS", "LTA": "LTA", "LTA N": "LTA", "LTA S": "LTA",
          "MSI": "International", "WLDs": "International"}


def holdout_summary():
    if not HOLDOUT.exists():
        return None
    report = json.loads(HOLDOUT.read_text(encoding="utf-8"))
    metrics = report.get("metrics", {})
    if "v6_original_data" not in metrics or "Elo" not in metrics:
        return None
    pick = lambda m: {k: m[k] for k in ("games", "accuracy", "log_loss", "brier")}
    v6 = metrics["v6_original_data"]
    return {"label": "Sealed 2026 holdout (tested once)", "date_range": report.get("date_range"),
            "model": pick(v6), "elo": pick(metrics["Elo"]),
            "log_loss_improvement_95": v6.get("vs_Elo", {}).get("log_loss_improvement")}


def team_list(elo):
    """Teams with a game in the last 12 months: display name, region (latest league) and current rating."""
    with closing(sqlite3.connect(f"file:{DB}?mode=ro", uri=True)) as conn:
        end = conn.execute("SELECT MAX(date) FROM player_stats").fetchone()[0]
        rows = conn.execute(
            "SELECT teamname, league, COUNT(DISTINCT gameid) FROM player_stats "
            "WHERE date >= datetime(?, '-365 days') GROUP BY teamname, league", (end,)).fetchall()
    # Region = the home league with the most games; international events only if nothing else.
    latest = {}
    for team, league, games in rows:
        home = REGION.get(league, league) != "International"
        best = latest.get(team)
        if best is None or (home, games) > best[1]:
            latest[team] = (league, (home, games))
    teams = [{"team": t, "rating": round(elo.get(normalize(t), 1200)), "region": REGION.get(lg, lg)}
             for t, (lg, _) in latest.items()]
    teams.sort(key=lambda x: -x["rating"])
    for rank, entry in enumerate(teams, 1):
        entry["rank"] = rank
    return [{"rank": e["rank"], "team": e["team"], "rating": e["rating"], "region": e["region"]} for e in teams]


def main():
    with MODEL.open("rb") as f:
        bundle = pickle.load(f)
    chosen = bundle["evaluation"]["rating_selected"]
    games, skipped = read_games(DB)
    _, state = replay(games, chosen["k"], chosen["season_shrink"])
    if not BACKUP.exists():
        shutil.copy2(MODEL, BACKUP)
    bundle.update({
        "state": state, "snapshot": state.snapshot(),
        "ratings_through": str(games[-1].date), "ratings_games": len(games),
        "ratings_note": "Ratings refreshed after the sealed 2026 evaluation; estimator unchanged.",
        "holdout": holdout_summary(),
    })
    tmp = MODEL.with_suffix(".tmp")
    with tmp.open("wb") as f:
        pickle.dump(bundle, f)
    os.replace(tmp, MODEL)
    teams = team_list(state.elo)
    RATINGS.write_text(json.dumps(teams, indent=2) + "\n", encoding="utf-8")
    print(f"Replayed {len(games):,} games ({skipped} skipped) through {games[-1].date:%Y-%m-%d}. "
          f"Latest patch {state.latest_patch}. {len(teams)} active teams; top 5:")
    for e in teams[:5]:
        print(f"  {e['rank']}. {e['team']} ({e['region']}) {e['rating']}")


if __name__ == "__main__":
    main()
