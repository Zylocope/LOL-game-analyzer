"""Collect high-rank solo queue matches (Master+) from the Riot API for the draft-only "Ranked mode" model.

Usage (from the repo root, PowerShell):
    python scripts/ranked/collect.py                  # Korea, runs until stopped (Ctrl+C) or the key expires
    python scripts/ranked/collect.py --platform euw1 --max-matches 5000

The API key is read from RIOT_API_KEY in the environment or in the repo's .env file (git-ignored).
It is never printed or saved anywhere else. Re-running resumes: already-saved matches are skipped.

Only the draft and the result are stored (champions, roles, bans, patch, duration, winner).
No player names or IDs are written to disk.
Standard library only; works with the free 24-hour development key (20 requests/s, 100 requests/2 min).
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "data" / "ranked"
REGION_OF = {"kr": "asia", "jp1": "asia", "euw1": "europe", "eun1": "europe", "tr1": "europe", "ru": "europe",
             "na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas",
             "oc1": "sea", "sg2": "sea", "tw2": "sea", "vn2": "sea"}
TIERS = ["challengerleagues", "grandmasterleagues", "masterleagues"]
QUEUE = 420                     # ranked solo/duo
POSITIONS = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
MIN_DURATION = 300              # seconds; shorter games are remakes
REQUEST_GAP = 1.25              # seconds between calls keeps under 100 requests / 2 minutes

FIELDS = (["match_id", "platform", "patch", "game_start_ms", "duration_s", "blue_win"]
          + [f"{side}_{p.lower()}" for side in ("blue", "red") for p in POSITIONS]
          + [f"{side}_ban{i}" for side in ("blue", "red") for i in range(1, 6)])


class KeyProblem(Exception):
    pass


def load_key():
    key = os.environ.get("RIOT_API_KEY", "").strip()
    env = REPO / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("RIOT_API_KEY"):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("No RIOT_API_KEY found. Add a line  RIOT_API_KEY=your-key  to the .env file in the repo root.")
    return key


class Riot:
    def __init__(self, key):
        self.key, self.last, self.calls = key, 0.0, 0

    def get(self, host, path, params=None):
        url = f"https://{host}.api.riotgames.com{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        for attempt in range(6):
            wait = REQUEST_GAP - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            self.calls += 1
            req = urllib.request.Request(url, headers={"X-Riot-Token": self.key, "User-Agent": "nexus-sight-research"})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    raise KeyProblem("The API key was rejected (expired or invalid).")
                if e.code == 404:
                    return None
                if e.code == 429:
                    time.sleep(int(e.headers.get("Retry-After", "10")) + 1)
                    continue
                if e.code >= 500:
                    time.sleep(2 ** attempt)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError):
                time.sleep(2 ** attempt)
        return None


def row_from_match(match, platform):
    info = match.get("info", {})
    if info.get("queueId") != QUEUE or info.get("gameDuration", 0) < MIN_DURATION:
        return None
    picks = {}
    for p in info.get("participants", []):
        side = "blue" if p.get("teamId") == 100 else "red"
        pos = p.get("teamPosition") or ""
        if pos not in POSITIONS:
            return None
        picks[f"{side}_{pos.lower()}"] = p.get("championName")
    if len(picks) != 10:
        return None
    row = {"match_id": match["metadata"]["matchId"], "platform": platform,
           "patch": ".".join(str(info.get("gameVersion", "")).split(".")[:2]),
           "game_start_ms": info.get("gameStartTimestamp") or info.get("gameCreation"),
           "duration_s": info.get("gameDuration"), **picks}
    for team in info.get("teams", []):
        side = "blue" if team.get("teamId") == 100 else "red"
        if side == "blue":
            row["blue_win"] = int(bool(team.get("win")))
        bans = sorted(team.get("bans", []), key=lambda b: b.get("pickTurn", 0))
        for i, ban in enumerate(bans[:5], 1):
            row[f"{side}_ban{i}"] = ban.get("championId", -1)
    return row if "blue_win" in row else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platform", default="kr", choices=sorted(REGION_OF))
    ap.add_argument("--max-matches", type=int, default=0, help="stop after this many new matches (0 = no limit)")
    ap.add_argument("--per-player", type=int, default=20, help="recent ranked matches to check per player")
    ap.add_argument("--days", type=int, default=30, help="only matches from the last N days")
    args = ap.parse_args()

    riot = Riot(load_key())
    region = REGION_OF[args.platform]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"matches_{args.platform}.csv"
    seen = set()
    if out_path.exists():
        with out_path.open(newline="", encoding="utf-8") as f:
            seen = {r["match_id"] for r in csv.DictReader(f)}
    start_time = int(time.time()) - args.days * 86400
    new = 0
    print(f"Collecting {args.platform} Master+ solo queue. Already saved: {len(seen)} matches -> {out_path}")

    try:
        players = []
        for tier in TIERS:
            league = riot.get(args.platform, f"/lol/league/v4/{tier}/by-queue/RANKED_SOLO_5x5") or {}
            entries = sorted(league.get("entries", []), key=lambda e: -e.get("leaguePoints", 0))
            players += [e for e in entries]
            print(f"  {tier.replace('leagues', '')}: {len(entries)} players")
        with out_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
            if out_path.stat().st_size == 0:
                writer.writeheader()
            for i, entry in enumerate(players, 1):
                puuid = entry.get("puuid")
                if not puuid and entry.get("summonerId"):
                    summoner = riot.get(args.platform, f"/lol/summoner/v4/summoners/{entry['summonerId']}") or {}
                    puuid = summoner.get("puuid")
                if not puuid:
                    continue
                ids = riot.get(region, f"/lol/match/v5/matches/by-puuid/{puuid}/ids",
                               {"queue": QUEUE, "type": "ranked", "startTime": start_time,
                                "count": args.per_player}) or []
                for match_id in ids:
                    if match_id in seen:
                        continue
                    seen.add(match_id)
                    match = riot.get(region, f"/lol/match/v5/matches/{match_id}")
                    row = row_from_match(match, args.platform) if match else None
                    if row:
                        writer.writerow(row)
                        new += 1
                    if new and new % 50 == 0:
                        f.flush()
                        print(f"  {new} new matches saved (player {i}/{len(players)}, {riot.calls} requests)")
                    if args.max_matches and new >= args.max_matches:
                        print("Reached --max-matches.")
                        return
        print("Went through every Master+ player. Run again later (or with --days) for more matches.")
    except KeyProblem as e:
        print(f"\nStopped: {e}\nRegenerate the key at developer.riotgames.com, update RIOT_API_KEY in .env, "
              "and run the same command again. It continues where it stopped.")
    except KeyboardInterrupt:
        print("\nStopped by you. Run the same command again to continue.")
    finally:
        print(f"New matches this run: {new}. Saved in {out_path}")


if __name__ == "__main__":
    main()
