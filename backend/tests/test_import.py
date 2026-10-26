from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
import pandas as pd

from backend.db_builder import init_db


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.csv, self.database = self.root/'worlds.csv', self.root/'games.db'
        rows = []
        for side, result in [('Blue', 1), ('Red', 0)]:
            for position in ['team', 'top', 'jng', 'mid', 'bot', 'sup']:
                rows.append(dict(gameid='worlds-1', side=side, result=result, league='W',
                                 position=position, date='2022-10-01', champion='Azir', teamname=side))
        self.data = pd.DataFrame(rows)
        self.data.to_csv(self.csv, index=False)

    def test_worlds_retained_and_reimport_does_not_duplicate(self):
        init_db([self.csv], self.database)
        result = init_db([self.csv], self.database)
        self.assertEqual(result['inserted_rows'], 0)
        with closing(sqlite3.connect(self.database)) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM team_stats').fetchone()[0], 2)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM player_stats').fetchone()[0], 10)
            self.assertEqual(conn.execute('SELECT league FROM team_stats LIMIT 1').fetchone()[0], 'W')

    def test_failed_import_preserves_original_database(self):
        init_db([self.csv], self.database)
        before = self.database.read_bytes()
        self.data['result'] = 1-self.data.result
        self.data.to_csv(self.csv, index=False)
        with self.assertRaises(ValueError):
            init_db([self.csv], self.database)
        self.assertEqual(before, self.database.read_bytes())


if __name__ == '__main__':
    unittest.main()
