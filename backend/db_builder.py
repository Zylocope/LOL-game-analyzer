"""Append OE CSVs safely; retain Worlds and avoid duplicate game rows."""
import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR/'Data'
DB_PATH = BASE_DIR/'nexus_sight.db'
KEYS = ['gameid', 'side', 'position']
LEAGUES = {'LCK', 'LPL', 'LEC', 'LCS', 'LTA', 'LTA N', 'LTA S', 'MSI', 'W', 'Worlds', 'WLDs'}  # OE labels Worlds as WLDs


def supported_league(value):
    value = str(value)
    return value in LEAGUES or (value.startswith('W') and value[1:].isdigit())


def init_db(paths=None, db_path=DB_PATH, replace=False):
    paths = list(paths or sorted(DATA_FOLDER.glob('*.csv')))
    if not paths:
        raise ValueError(f'No CSVs in {DATA_FOLDER}; database unchanged')
    destination = Path(db_path).resolve()
    staged = destination.with_suffix('.import.tmp')
    if staged.exists():
        raise FileExistsError(f'Unfinished import exists: {staged}')
    written = 0
    try:
        with closing(sqlite3.connect(staged)) as conn:
            if destination.exists() and not replace:
                with closing(sqlite3.connect(f'file:{destination}?mode=ro', uri=True)) as old:
                    old.backup(conn)
            # Index before merging; otherwise each incoming row scans the live table.
            for table in ['team_stats', 'player_stats']:
                if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
                    conn.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS {table}_identity ON {table}(gameid,side,position)')
            for path in paths:
                with pd.read_csv(path, chunksize=25000, low_memory=False) as reader:
                    for chunk in reader:
                        required = set(KEYS + ['league', 'result', 'date', 'champion', 'teamname'])
                        if not required.issubset(chunk.columns):
                            raise ValueError(f'{path}: missing required columns')
                        chunk = chunk[chunk.league.map(supported_league)].copy()
                        chunk['result'] = pd.to_numeric(chunk.result, errors='coerce')
                        chunk = chunk.dropna(subset=KEYS+['date', 'teamname', 'result'])
                        chunk = chunk[chunk.result.isin([0, 1])]
                        if (chunk.groupby(KEYS).result.nunique() > 1).any():
                            raise ValueError('Conflicting outcomes within incoming data')
                        chunk = chunk.drop_duplicates(KEYS)
                        for table, selected in [('team_stats', chunk[chunk.position == 'team']),
                                                ('player_stats', chunk[chunk.position != 'team'])]:
                            if selected.empty:
                                continue
                            exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
                            if exists:
                                columns = {r[1] for r in conn.execute(f'PRAGMA table_info({table})')}
                                for column in selected.columns:
                                    if column not in columns:
                                        quoted = column.replace('"', '""')
                                        conn.execute(f'ALTER TABLE {table} ADD COLUMN "{quoted}"')
                                selected.to_sql('_incoming', conn, if_exists='replace', index=False)
                                condition = 'i.gameid=t.gameid AND i.side=t.side AND i.position=t.position'
                                if conn.execute(f'SELECT 1 FROM _incoming i JOIN {table} t ON {condition} WHERE i.result!=t.result LIMIT 1').fetchone():
                                    raise ValueError('Conflicting outcomes for existing games')
                                names = ','.join('"'+c.replace('"','""')+'"' for c in selected.columns)
                                cursor = conn.execute(f'INSERT INTO {table} ({names}) SELECT {names} FROM _incoming i WHERE NOT EXISTS (SELECT 1 FROM {table} t WHERE {condition})')
                                written += cursor.rowcount
                                conn.execute('DROP TABLE _incoming')
                            else:
                                selected.to_sql(table, conn, index=False)
                                written += len(selected)
                                conn.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS {table}_identity ON {table}(gameid,side,position)')
                        conn.commit()
            for table in ['team_stats', 'player_stats']:
                if not conn.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone():
                    raise ValueError(f'Import has no {table} rows')
                if conn.execute(f'SELECT 1 FROM {table} GROUP BY gameid,side,position HAVING COUNT(*)>1 LIMIT 1').fetchone():
                    raise ValueError(f'Duplicate identities in {table}')
                conn.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS {table}_identity ON {table}(gameid,side,position)')
            conn.commit()
        os.replace(staged, destination)
    except BaseException:
        if staged.exists():
            staged.unlink()  # Only the exact staging file created by this call.
        raise
    return {'inserted_rows': written, 'database': str(destination)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', nargs='*', type=Path)
    parser.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    print(init_db(args.csv, replace=args.replace))
