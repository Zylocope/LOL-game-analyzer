"""Read-only coverage report; do not infer coverage from filenames."""
from contextlib import closing
import json
import sqlite3
from .db_builder import DB_PATH


def audit(path=DB_PATH):
    with closing(sqlite3.connect(f'file:{path}?mode=ro', uri=True)) as conn:
        coverage = [dict(year=int(year), league=league, games=count)
                    for year, league, count in conn.execute(
                        'SELECT year,league,COUNT(DISTINCT gameid) FROM team_stats GROUP BY year,league ORDER BY year,league')]
        years = {row['year'] for row in coverage}
        return {'games': conn.execute('SELECT COUNT(DISTINCT gameid) FROM team_stats').fetchone()[0],
                'missing_years': sorted(set(range(min(years),max(years)+1))-years),
                'has_lpl': any(row['league'] == 'LPL' for row in coverage),
                'has_worlds': any(row['league'] in ('W', 'Worlds') or str(row['league']).startswith('W2') for row in coverage),
                'coverage': coverage}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
