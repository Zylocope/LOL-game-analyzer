# Ranked mode: draft-only prediction for high-rank solo queue

Goal: predict the winner of a Master+ ranked game from the draft alone (no teams or players).

## 1. Add your Riot key (once per day)

Get the free development key at https://developer.riotgames.com (it expires every 24 hours).
Add this line to the `.env` file in the repo root (create the file if needed). `.env` is git-ignored:

```
RIOT_API_KEY=paste-your-key-here
```

Never commit the key or paste it into chats.

## 2. Collect matches (run overnight)

```powershell
python scripts/ranked/collect.py
```

- Korea Master+ by default; add `--platform euw1` or `--platform na1` for other servers.
- Saves to `data/ranked/matches_<platform>.csv` (only champions, roles, bans, patch, duration and the winner).
- About 2,500 matches per hour with a development key. Stop any time with Ctrl+C; running it again continues.
- When the key expires, the script stops and says so: regenerate the key, update `.env`, run the same command.

## 3. Train and evaluate

```powershell
python scripts/ranked/train.py
```

Writes `scripts/ranked/REPORT.md` (results vs baselines with a 95% interval) and `backend/ranked_model.pkl`.
Aim for at least 20,000 matches from the same few patches.

## What to expect

In matchmade games both teams have similar skill, so the draft decides only a small part of the outcome.
Draft-only models usually land around 52–56% accuracy. The honest comparison is against two baselines:
the blue-side win rate and simple champion win rates.
