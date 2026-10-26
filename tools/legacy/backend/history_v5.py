"""Outcome aggregates updated only after a complete timestamp batch is featured."""
from collections import defaultdict


def normalize(value):
    return str(value).lower().replace(' ', '').replace("'", '').replace('.', '')


class History:
    def __init__(self):
        self.elo = {}
        self.champions = defaultdict(lambda: [0, 0])
        self.matchups = defaultdict(lambda: [0, 0])
        self.roles = defaultdict(set)

    def snapshot(self):
        meta, games, matrix = {}, {}, {}
        for champion, (count, wins) in self.champions.items():
            games[champion] = count
            meta[champion] = (wins + 25) / (count + 50)
        for (champion, role, enemy), (count, wins) in self.matchups.items():
            matrix.setdefault(champion, {}).setdefault(role, {})[enemy] = {
                'games': count, 'winRate': 100 * (wins + 25) / (count + 50)
            }
        return {
            'elo': dict(self.elo), 'meta': meta, 'games': games,
            'matrix': matrix, 'roles': {c: sorted(r) for c, r in self.roles.items()},
        }

    def update(self, blue, red):
        blue_name, red_name = normalize(blue.iloc[0].teamname), normalize(red.iloc[0].teamname)
        a, b = self.elo.get(blue_name, 1200), self.elo.get(red_name, 1200)
        delta = 32 * (int(blue.iloc[0].result) - 1 / (1 + 10 ** ((b - a) / 400)))
        self.elo[blue_name], self.elo[red_name] = a + delta, b - delta
        for own, other in ((blue, red), (red, blue)):
            enemies = dict(zip(other.position, other.champion))
            for row in own.itertuples():
                champion = normalize(row.champion)
                self.roles[champion].add(row.position)
                self.champions[champion][0] += 1
                self.champions[champion][1] += int(row.result)
                key = (champion, row.position, normalize(enemies[row.position]))
                self.matchups[key][0] += 1
                self.matchups[key][1] += int(row.result)
