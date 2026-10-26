from contextlib import closing
import sqlite3

import pandas as pd


def fixture(path, count=12):
    rows = []
    for day in range(count):
        # Two games share each timestamp; neither may see the other's outcome.
        for match in range(2):
            for side, team, prefix, result in [('Blue', 'A', 'a', day % 2),
                                              ('Red', 'B', 'b', 1 - day % 2)]:
                for position in ['top', 'jungle', 'mid', 'bot', 'support']:
                    rows.append(dict(gameid=f'{day:02}-{match}', date=f'2024-01-{day+1:02}',
                                     side=side, teamname=team, champion=prefix+position,
                                     position=position, result=result))
    with closing(sqlite3.connect(path)) as conn:
        pd.DataFrame(rows).to_sql('player_stats', conn, index=False)


