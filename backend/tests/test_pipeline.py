import unittest
import numpy as np
import pandas as pd
from backend.experiment import seasons, walk_forward
from backend.features import FEATURES


class EvaluationTests(unittest.TestCase):
    def test_walk_forward_excludes_reporting_labels(self):
        rows = []
        for year in [2020, 2021, 2023, 2024, 2025]:
            for i in range(600):
                rows.append(dict.fromkeys(FEATURES, 0.) | {'year': year, 'target': i % 2})
        frame = pd.DataFrame(rows)
        years = seasons(frame, 2025)
        self.assertEqual(years, [2021, 2023, 2024])
        spec = {'features': ['elo_diff'], 'family': 'elo'}
        before, folds = walk_forward(frame, spec, years)
        frame.loc[frame.year == 2025, 'target'] = 0
        after, _ = walk_forward(frame, spec, years)
        self.assertEqual(before, after)
        self.assertEqual([fold['year'] for fold in folds], years)
        self.assertEqual([fold['train_games'] for fold in folds], [600, 1200, 1800])


if __name__ == '__main__':
    unittest.main()
