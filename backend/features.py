"""Incremental pre-game features shared by replay and live inference."""
from collections import deque
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from itertools import groupby
import heapq
import math
import sqlite3

import numpy as np
import pandas as pd

POSITIONS = ('top', 'jungle', 'mid', 'bot', 'support')
FEATURES = ['elo_diff', 'player_elo_diff', 'form_diff', 'player_form_diff',
            'roster_stability_diff', 'patch_strength_diff', 'patch_coverage_diff',
            'comfort_diff', 'comfort_residual_diff', 'lane_counter_diff']


def normalize(value):
    return str(value or '').lower().replace(' ', '').replace("'", '').replace('.', '')


def patch_key(value):
    """SQLite stores OE patch numbers as floats, e.g. 15.1 means 15.10."""
    if value is None or str(value).lower() in ('nan', '', 'none'):
        return 'unknown'
    return f'{float(value):.2f}'


@dataclass
class Game:
    gameid: str
    date: datetime
    available: datetime
    blue: list
    red: list
    patch: str
    league: str
    target: int


def read_games(db_path):
    with closing(sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)) as conn:
        columns = {row[1] for row in conn.execute('pragma table_info(player_stats)')}
        required = ['gameid', 'date', 'side', 'teamname', 'result', 'position', 'champion']
        optional = ['playerid', 'playername', 'patch', 'league', 'gamelength']
        query = 'SELECT ' + ','.join(required + [c if c in columns else f'NULL AS {c}' for c in optional])
        query += ' FROM player_stats ORDER BY gameid'
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchall()
    games, skipped = [], 0
    for gameid, group in groupby(rows, key=lambda row: row['gameid']):
        records = [dict(row) for row in group]
        try:
            sides = []
            dates = {r['date'] for r in records}
            if len(dates) != 1:
                raise ValueError('Inconsistent game timestamps')
            date = datetime.fromisoformat(str(records[0]['date']).replace('Z', '+00:00'))
            date = date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date.astimezone(timezone.utc)
            for side in ('blue', 'red'):
                own = [r for r in records if str(r['side']).lower() == side]
                for r in own:
                    r['position'] = {'jng': 'jungle', 'sup': 'support'}.get(r['position'], r['position'])
                    r['champion'] = normalize(r['champion'])
                    r['player'] = str(r['playerid'] or normalize(r['playername']) or '')
                if (len(own) != 5 or {r['position'] for r in own} != set(POSITIONS)
                        or len({r['teamname'] for r in own}) != 1
                        or len({r['champion'] for r in own}) != 5
                        or any(not r['champion'] or not r['teamname'] for r in own)
                        or len({r['result'] for r in own}) != 1):
                    raise ValueError('Incomplete roster')
                sides.append(sorted(own, key=lambda r: POSITIONS.index(r['position'])))
            blue, red = sides
            if (len(records) != 10 or {blue[0]['result'], red[0]['result']} != {0, 1}
                    or blue[0]['teamname'] == red[0]['teamname']
                    or len({r['champion'] for r in records}) != 10):
                raise ValueError('Invalid game')
            # OE duration is seconds. Wait two hours beyond the recorded timestamp
            # (or longer if the duration requires it) so overlapping games cannot leak.
            duration = max(float(r['gamelength'] or 0) for r in records)
            available = date + timedelta(seconds=max(7200, duration + 900))
            games.append(Game(str(gameid), date, available, blue, red,
                              patch_key(records[0]['patch']), str(records[0]['league'] or 'Unknown'),
                              int(blue[0]['result'])))
        except (ValueError, TypeError, OverflowError):
            skipped += 1
    return sorted(games, key=lambda g: (g.date, g.gameid)), skipped


class FeatureState:
    def __init__(self, k=32, season_shrink=0.0):
        self.k, self.season_shrink = k, season_shrink
        self.elo, self.players, self.aliases = {}, {}, {}
        self.form, self.player_form, self.rosters = {}, {}, {}
        self.lineups = {}
        self.champions, self.matchups, self.roles = {}, {}, {}
        self.patch_stats, self.comfort, self.player_games = {}, {}, {}
        self.season = None
        self.latest_patch = 'unknown'

    def begin(self, year):
        if self.season is not None and year > self.season:
            factor = (1 - self.season_shrink) ** (year - self.season)
            self.elo = {key: 1200 + (value - 1200) * factor for key, value in self.elo.items()}
            self.players = {key: 1200 + (value - 1200) * factor for key, value in self.players.items()}
        self.season = max(year, self.season or year)

    @staticmethod
    def rate(stats, key, prior=20):
        count, total = stats.get(key, (0, 0.0))
        return total / (count + prior)

    @staticmethod
    def recent(store, key):
        values = store.get(key, ())
        n = len(values)
        return sum((i+1)*v for i, v in enumerate(values)) / (n*(n+1)/2+5) if n else 0.0

    def side_features(self, own, enemy, patch):
        team = normalize(own[0]['teamname'])
        roster = {r['player'] for r in own if r['player']}
        previous = self.rosters.get(team, set())
        out = dict(elo=self.elo.get(team, 1200), player_elo=0., form=self.recent(self.form, team),
                   player_form=0., roster_stability=len(roster & previous) / 5,
                   patch_strength=0., patch_coverage=0., comfort=0., comfort_residual=0., lane_counter=0.)
        for row, opponent in zip(own, enemy):
            player, champion, role = row['player'], row['champion'], row['position']
            out['player_elo'] += self.players.get(player, 1200) / 5
            out['player_form'] += self.recent(self.player_form, player) / 5
            key = (patch, champion, role)
            out['patch_strength'] += self.rate(self.patch_stats, key) / 5
            out['patch_coverage'] += self.patch_stats.get(key, (0, 0))[0] / (self.patch_stats.get(key, (0, 0))[0] + 20) / 5
            count = self.comfort.get((player, champion), (0, 0))[0]
            out['comfort'] += math.log1p(count) / 5
            out['comfort_residual'] += self.rate(self.comfort, (player, champion)) / 5
            pair = (champion, role, opponent['champion'])
            count, wins = self.matchups.get(pair, (0, 0))
            out['lane_counter'] += ((wins + 25) / (count + 50) - .5) / 5
        return out

    def vector(self, blue, red, patch):
        a, b = self.side_features(blue, red, patch), self.side_features(red, blue, patch)
        return [a[key[:-5]] - b[key[:-5]] for key in FEATURES]

    def update(self, game):
        blue_name, red_name = normalize(game.blue[0]['teamname']), normalize(game.red[0]['teamname'])
        a, b = self.elo.get(blue_name, 1200), self.elo.get(red_name, 1200)
        expected = 1 / (1 + 10 ** ((b - a) / 400))
        delta = self.k * (game.target - expected)
        self.elo[blue_name], self.elo[red_name] = a + delta, b - delta
        pa = sum(self.players.get(r['player'], 1200) for r in game.blue) / 5
        pb = sum(self.players.get(r['player'], 1200) for r in game.red) / 5
        player_delta = self.k * (game.target - 1 / (1 + 10 ** ((pb - pa) / 400)))
        for own, enemy, result, probability, change in ((game.blue, game.red, game.target, expected, player_delta),
                                                       (game.red, game.blue, 1-game.target, 1-expected, -player_delta)):
            team = normalize(own[0]['teamname'])
            self.form.setdefault(team, deque(maxlen=10)).append(result - probability)
            self.rosters[team] = {r['player'] for r in own if r['player']}
            self.lineups[team] = [r['player'] for r in own]
            for row, opponent in zip(own, enemy):
                player, champion, role = row['player'], row['champion'], row['position']
                if player:
                    self.players[player] = self.players.get(player, 1200) + change
                    self.player_games[player] = self.player_games.get(player, 0) + 1
                    self.aliases[normalize(row.get('playername'))] = player
                    self.player_form.setdefault(player, deque(maxlen=10)).append(result - probability)
                    self.add(self.comfort, (player, champion), result-probability)
                self.roles.setdefault(champion, set()).add(role)
                self.add(self.champions, champion, result)
                self.add(self.patch_stats, (game.patch, champion, role), result-probability)
                self.add(self.matchups, (champion, role, opponent['champion']), result)
        self.latest_patch = game.patch

    @staticmethod
    def add(store, key, value):
        count, total = store.get(key, (0, 0.))
        store[key] = (count+1, total+value)

    def snapshot(self):
        """Legacy stats endpoints use the same smoothed serving history."""
        matrix = {}
        for (champion, role, enemy), (count, wins) in self.matchups.items():
            matrix.setdefault(champion, {}).setdefault(role, {})[enemy] = {
                'games': count, 'winRate': 100*(wins+25)/(count+50)}
        return {'elo': self.elo, 'roles': {c: sorted(r) for c, r in self.roles.items()},
                'meta': {c: (wins+25)/(count+50) for c, (count, wins) in self.champions.items()},
                'games': {c: count for c, (count, _) in self.champions.items()}, 'matrix': matrix}


def replay(games, k=32, season_shrink=0.):
    state, pending, rows = FeatureState(k, season_shrink), [], []
    for game in games:
        # Update only results conservatively available strictly before this start.
        while pending and pending[0][0] < game.date:
            _, _, completed = heapq.heappop(pending)
            state.begin(completed.date.year)
            state.update(completed)
        state.begin(game.date.year)
        rows.append(dict(zip(FEATURES, state.vector(game.blue, game.red, game.patch))) |
                    {'gameid': game.gameid, 'date': game.date, 'year': game.date.year,
                     'target': game.target, 'league': game.league})
        heapq.heappush(pending, (game.available, game.gameid, game))
    while pending:
        _, _, game = heapq.heappop(pending)
        state.begin(game.date.year)
        state.update(game)
    return pd.DataFrame(rows), state


def request_roster(state, team, champions, names=None):
    if names is None:
        players = state.lineups.get(normalize(team), ['']*5)
        names = ['']*5
    else:
        players = [state.aliases.get(normalize(name), normalize(name)) for name in names]
    return [{'teamname': team, 'champion': normalize(champion), 'position': role,
             'player': player, 'playername': name}
            for role, champion, player, name in zip(POSITIONS, champions, players, names)]
