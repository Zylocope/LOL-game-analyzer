from copy import deepcopy
from datetime import timedelta
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from backend.features import FeatureState, FEATURES, read_games, replay, patch_key, request_roster
from backend.models import ProbabilityModel
from backend.tests.fixtures import fixture


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'fixture.db'
        fixture(str(self.path))
        self.games, _ = read_games(self.path)

    def test_own_future_and_overlapping_results_are_unavailable(self):
        before, _ = replay(self.games)
        changed = deepcopy(self.games)
        cutoff = changed[10].date
        for game in changed:
            if game.date >= cutoff:
                game.target = 1-game.target
        after, _ = replay(changed)
        mask = before.date <= cutoff
        pd.testing.assert_frame_equal(before.loc[mask, FEATURES], after.loc[mask, FEATURES])
        overlapping = deepcopy(self.games[:2])
        overlapping[1].date = overlapping[0].date + timedelta(minutes=30)
        data, _ = replay(overlapping)
        self.assertEqual(data.elo_diff.tolist(), [0, 0])

    def test_season_regression_occurs_once_and_never_moves_backwards(self):
        state = FeatureState(season_shrink=.2)
        state.begin(2024)
        state.elo['a'] = 1400
        state.begin(2025)
        self.assertEqual(state.elo['a'], 1360)
        state.begin(2024)
        state.begin(2025)
        self.assertEqual(state.elo['a'], 1360)

    def test_patch_and_player_comfort_are_isolated(self):
        state = FeatureState()
        game = deepcopy(self.games[0])
        for i, row in enumerate(game.blue + game.red):
            row['player'] = str(i)
            row['playername'] = f'Player {i}'
        game.patch = '15.01'
        state.update(game)
        before = state.side_features(game.blue, game.red, '15.01')
        after = state.side_features(game.blue, game.red, '15.02')
        self.assertNotEqual(before['patch_strength'], 0)
        self.assertEqual(after['patch_strength'], 0)
        self.assertGreater(before['comfort'], 0)
        newcomer = deepcopy(game.blue)
        for row in newcomer:
            row['player'] = 'unseen-' + row['player']
        self.assertEqual(state.side_features(newcomer, game.red, game.patch)['comfort'], 0)
        roster = request_roster(state, 'A', [r['champion'] for r in game.blue])
        self.assertEqual([r['player'] for r in roster], [r['player'] for r in game.blue])
        named = request_roster(state, 'A', [r['champion'] for r in game.blue],
                               [r['playername'] for r in game.blue])
        np.testing.assert_allclose(state.vector(named, game.red, game.patch),
                                   state.vector(game.blue, game.red, game.patch))

    def test_patch_float_keys_are_consistent(self):
        self.assertEqual(patch_key(15.1), patch_key('15.10'))
        self.assertEqual(patch_key(None), 'unknown')

    def test_estimators_preserve_side_symmetry(self):
        rng = np.random.default_rng(42)
        frame = pd.DataFrame(rng.normal(size=(100, len(FEATURES))), columns=FEATURES)
        target = (frame.elo_diff + frame.player_elo_diff > 0).astype(int)
        for family in ['elo', 'residual', 'logistic']:
            with self.subTest(family=family):
                model = ProbabilityModel(FEATURES, family=family).fit(frame, target)
                p = model.predict_proba(frame)[:, 1]
                q = model.predict_proba(-frame)[:, 1]
                np.testing.assert_allclose(p+q, 1)
                self.assertTrue(np.isfinite(p).all())


if __name__ == '__main__':
    unittest.main()
