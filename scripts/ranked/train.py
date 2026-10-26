"""Train and evaluate the draft-only Ranked-mode model on collected solo queue matches.

Usage (from the repo root):
    python scripts/ranked/train.py                     # uses every data/ranked/matches_*.csv

Split by time: oldest 60% train, next 20% validation (chooses regularisation), newest 20% test (reported once).
Features: each champion in each role, +1 for blue and -1 for red, plus a blue-side term. Logistic regression with
side-symmetric data augmentation. Baselines: blue-side rate, and smoothed champion win rates.
Writes backend/ranked_model.pkl and scripts/ranked/REPORT.md.
"""
import glob
import json
import pickle
import random
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss

REPO = Path(__file__).resolve().parents[2]
ROLES = ["top", "jungle", "middle", "bottom", "utility"]
PRIOR = 20  # smoothing games for the champion-win-rate baseline


def load():
    files = sorted(glob.glob(str(REPO / "data" / "ranked" / "matches_*.csv")))
    if not files:
        raise SystemExit("No data/ranked/matches_*.csv yet. Run scripts/ranked/collect.py first.")
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True).drop_duplicates("match_id")
    df = df.dropna(subset=[f"{s}_{r}" for s in ("blue", "red") for r in ROLES] + ["blue_win"])
    return df.sort_values("game_start_ms").reset_index(drop=True)


def vocab(df):
    keys = sorted({f"{r}:{c}" for s in ("blue", "red") for r in ROLES for c in df[f"{s}_{r}"]})
    return {k: i for i, k in enumerate(keys)}


def design(df, index, swap=False):
    rows, cols, vals = [], [], []
    for i, rec in enumerate(df.itertuples(index=False)):
        rec = rec._asdict()
        for side, sign in (("blue", 1.0), ("red", -1.0)):
            if swap:
                sign = -sign
            for r in ROLES:
                j = index.get(f"{r}:{rec[f'{side}_{r}']}")
                if j is not None:
                    rows.append(i); cols.append(j); vals.append(sign)
    X = sparse.csr_matrix((vals, (rows, cols)), shape=(len(df), len(index)))
    side = np.full((len(df), 1), -1.0 if swap else 1.0)
    return sparse.hstack([X, sparse.csr_matrix(side)]).tocsr()


def metrics(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {"games": int(len(y)), "accuracy": float(accuracy_score(y, p > 0.5)),
            "log_loss": float(log_loss(y, p, labels=[0, 1])), "brier": float(brier_score_loss(y, p))}


def champ_rate_baseline(train, test):
    """Predict from the difference of smoothed champion-in-role win rates."""
    stats = {}
    for side, won in (("blue", train.blue_win), ("red", 1 - train.blue_win)):
        for r in ROLES:
            for c, w in zip(train[f"{side}_{r}"], won):
                g = stats.setdefault((r, c), [0, 0]); g[0] += w; g[1] += 1
    def rate(r, c):
        w, n = stats.get((r, c), (0, 0)); return (w + PRIOR * 0.5) / (n + PRIOR)
    blue_rate = train.blue_win.mean()
    logit = lambda q: np.log(q / (1 - q))
    out = []
    for rec in test.itertuples(index=False):
        d = rec._asdict()
        s = sum(logit(rate(r, d[f"blue_{r}"])) - logit(rate(r, d[f"red_{r}"])) for r in ROLES)
        out.append(1 / (1 + np.exp(-(s + logit(blue_rate)))))
    return np.array(out)


def bootstrap_improvement(y, p_base, p_model, reps=2000, seed=7):
    rng = np.random.default_rng(seed); n = len(y); diffs = []
    lb = -(y * np.log(np.clip(p_base, 1e-6, 1)) + (1 - y) * np.log(np.clip(1 - p_base, 1e-6, 1)))
    lm = -(y * np.log(np.clip(p_model, 1e-6, 1)) + (1 - y) * np.log(np.clip(1 - p_model, 1e-6, 1)))
    for _ in range(reps):
        idx = rng.integers(0, n, n); diffs.append(lb[idx].mean() - lm[idx].mean())
    return [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]


def main():
    df = load()
    n = len(df)
    if n < 500:
        raise SystemExit(f"Only {n} matches. Collect at least a few thousand for a meaningful result.")
    a, b = int(n * 0.6), int(n * 0.8)
    train, val, test = df.iloc[:a], df.iloc[a:b], df.iloc[b:]
    y_tr, y_va, y_te = train.blue_win.to_numpy(), val.blue_win.to_numpy(), test.blue_win.to_numpy()

    def fit(frame, y, C, index):
        X = sparse.vstack([design(frame, index), design(frame, index, swap=True)])
        yy = np.concatenate([y, 1 - y])
        # the side column flips sign under swap, so a true blue-side advantage stays learnable
        return LogisticRegression(C=C, max_iter=2000, fit_intercept=False).fit(X, yy)

    index = vocab(train)
    search = {}
    for C in (0.01, 0.03, 0.1, 0.3, 1.0):
        m = fit(train, y_tr, C, index)
        search[C] = metrics(y_va, m.predict_proba(design(val, index))[:, 1])["log_loss"]
    best_C = min(search, key=search.get)

    fit_frame = pd.concat([train, val]); y_fit = fit_frame.blue_win.to_numpy()
    index = vocab(fit_frame)
    model = fit(fit_frame, y_fit, best_C, index)
    p_model = model.predict_proba(design(test, index))[:, 1]
    p_side = np.full(len(test), y_fit.mean())
    p_champ = champ_rate_baseline(fit_frame, test)

    report = {
        "matches": n, "train": len(train), "validation": len(val), "test": len(test),
        "test_period": [str(pd.to_datetime(test.game_start_ms.min(), unit="ms").date()),
                        str(pd.to_datetime(test.game_start_ms.max(), unit="ms").date())],
        "patches_in_test": sorted(test.patch.astype(str).unique().tolist()),
        "chosen_C": best_C, "validation_log_loss_by_C": search,
        "test": {"blue_side_rate": metrics(y_te, p_side), "champion_win_rates": metrics(y_te, p_champ),
                 "draft_model": metrics(y_te, p_model)},
        "log_loss_improvement_vs_blue_side_95": bootstrap_improvement(y_te, p_side, p_model),
        "log_loss_improvement_vs_champion_rates_95": bootstrap_improvement(y_te, p_champ, p_model),
    }
    with open(REPO / "backend" / "ranked_model.pkl", "wb") as f:
        pickle.dump({"model": model, "index": index, "roles": ROLES, "report": report}, f)
    t = report["test"]
    lines = ["# Ranked mode (draft only): evaluation", "",
             f"{n:,} Master+ solo queue matches. Time split: {len(train):,} train / {len(val):,} validation / "
             f"{len(test):,} test ({report['test_period'][0]} to {report['test_period'][1]}).", "",
             "| Model | Accuracy | Log loss | Brier |", "|---|---:|---:|---:|"]
    for name, key in (("Blue-side rate", "blue_side_rate"), ("Champion win rates", "champion_win_rates"),
                      ("Draft model", "draft_model")):
        m = t[key]; lines.append(f"| {name} | {m['accuracy']:.2%} | {m['log_loss']:.4f} | {m['brier']:.4f} |")
    lo, hi = report["log_loss_improvement_vs_champion_rates_95"]
    lines += ["", f"Log-loss improvement vs champion win rates: 95% interval {lo:+.4f} to {hi:+.4f} (match bootstrap).",
              f"Regularisation C={best_C} chosen on validation log loss.", "",
              "Draft-only prediction in matchmade games is expected to be weak (about 52-56% accuracy):",
              "matchmaking makes both teams similar in skill, so the draft is a small part of the outcome."]
    (REPO / "scripts" / "ranked" / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPO / "scripts" / "ranked" / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
