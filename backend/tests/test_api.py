import unittest
from unittest.mock import patch
from pydantic import ValidationError
from fastapi import HTTPException
from backend import main


def request():
    return dict(blueTeam='T1', redTeam='Gen.G',
                blueDraft=["K'Sante", 'Sejuani', 'Azir', "Kai'Sa", 'Rakan'],
                redDraft=['Renekton', 'Vi', 'Orianna', 'Aphelios', 'Nautilus'])


class RequestTests(unittest.TestCase):
    def test_invalid_drafts_are_rejected(self):
        for change in [dict(bluePlayers=['Faker']), dict(patch='15.1'), dict(blueDraft=['Azir']), dict(blueDraft=['Azir'] * 5),
                       dict(blueDraft=[1, 2, 3, 4, 5]),
                       dict(blueDraft=['unknown', 'Sejuani', 'Azir', "Kai'Sa", 'Rakan'])]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                main.PredictionRequest(**(request() | change))

    def test_missing_model_is_unavailable_instead_of_fabricated_probability(self):
        with patch.object(main, 'model', None), self.assertRaises(HTTPException) as raised:
            main.predict_match(main.PredictionRequest(**request()))
        self.assertEqual(raised.exception.status_code, 503)

    @unittest.skipIf(main.model is None, 'Train a v5 model to check serving integration')
    def test_swapping_sides_complements_probability(self):
        original = request()
        swapped = dict(blueTeam=original['redTeam'], redTeam=original['blueTeam'],
                       blueDraft=original['redDraft'], redDraft=original['blueDraft'])
        a = main.predict_match(main.PredictionRequest(**original))
        b = main.predict_match(main.PredictionRequest(**swapped))
        self.assertAlmostEqual(a['blueWinChance'] + b['blueWinChance'], 1)
        self.assertGreaterEqual(a['blueWinChance'], 0)
        self.assertLessEqual(a['blueWinChance'], 1)


if __name__ == '__main__':
    unittest.main()

