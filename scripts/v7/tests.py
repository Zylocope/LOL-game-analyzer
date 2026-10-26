"""Synthetic pre-freeze checks; this module never opens sealed data."""

from copy import deepcopy

from datetime import datetime,timezone,timedelta

from pathlib import Path

import tempfile

import unittest
import pickle

import numpy as np

import pandas as pd

from backend.features import Game,FEATURES as V6_FEATURES,replay as original_replay

from .baseline import replay as adapted_replay

from .features import replay

from .data import build

from .final import claim

from .modeling import calibrate,evaluate_spec

from .freeze import verify_v6
from .ratings import Ratings
from . import reporting
from unittest.mock import patch
import json,io,contextlib
from . import final as final_module
from .lock import BASE,digest





def fixture(n=12):

    games=[];metadata={}

    for i in range(n):

        date=datetime(2024,1,1,tzinfo=timezone.utc)+timedelta(days=i)

        teams=[]

        for side,prefix in [('A','a'),('B','b')]:

            teams.append([dict(teamname=side,champion=prefix+role,position=role,player=prefix+role,playername=prefix+role,result=i%2 if side=='A' else 1-i%2)

                          for role in ['top','jungle','mid','bot','support']])

        game=Game(str(i),date,date+timedelta(hours=2),*teams,'14.01','LCK',i%2)

        games.append(game)

        metadata[str(i)]={'game_number':1,'series_key':str(i),'first_pick':-1,'playoffs':0}

    return games,metadata





class V7Tests(unittest.TestCase):

    def test_rating_state_serializes_without_loss(self):
        games,metadata=fixture(2)
        _,engine=replay(games,metadata,advanced=True)
        restored=pickle.loads(pickle.dumps(engine))
        a=engine.ratings.features(games[-1]);b=restored.ratings.features(games[-1])
        self.assertEqual(a,b)

    def test_report_writer_is_predetermined_and_complete(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            root=Path(temp)
            (root/'README.md').write_text('Before<!-- V7_FINAL_START -->pending<!-- V7_FINAL_END -->After')
            metrics={'Elo':{'games':10,'accuracy':.6,'log_loss':.65,'brier':.22}}
            report={'metrics':metrics,'ablation':metrics,'limitations':['Synthetic smoke test']}
            with patch.object(reporting,'BASE',root),patch.object(reporting,'ROOT',root):
                reporting.write_final(report)
            self.assertTrue((root/'final_report.json').exists())
            self.assertIn('60.00%',(root/'README.md').read_text(encoding='utf-8'))
            self.assertTrue((root/'FINAL_REPORT.md').exists())

    def test_v6_baseline_is_unchanged(self):verify_v6()



    def test_adapter_matches_original_v6(self):

        games,_=fixture()

        a,_=original_replay(games,k=16,season_shrink=.2)

        b,_=adapted_replay(games)

        np.testing.assert_array_equal(a[V6_FEATURES],b[V6_FEATURES])



    def test_future_and_current_labels_cannot_change_features(self):

        games,metadata=fixture()

        a,_=replay(games,metadata,advanced=False)

        changed=deepcopy(games)

        for game in changed[6:]:game.target=1-game.target

        b,_=replay(changed,metadata,advanced=False)

        columns=[c for c in a.columns if c not in ['target','gameid','date','year','league','cohort']]

        np.testing.assert_array_equal(a.iloc[:7][columns],b.iloc[:7][columns])



    def test_overlapping_results_remain_unavailable(self):

        games,metadata=fixture(2)

        games[1].date=games[0].date+timedelta(minutes=30)

        games[1].available=games[1].date+timedelta(hours=2)

        frame,_=replay(games,metadata,advanced=False)

        self.assertEqual(frame.broad_elo_diff.tolist(),[0.,0.])

        self.assertEqual(frame.comfort_diff.tolist(),[0.,0.])



    def test_secondary_leagues_update_ratings_only(self):

        games,metadata=fixture(2)

        games[0].league='LDL'

        frame,engine=replay(games,metadata,advanced=False,finish=False)

        self.assertEqual(len(frame),1)

        self.assertNotEqual(frame.iloc[0].broad_elo_diff,0)

        self.assertEqual(frame.iloc[0].elo_diff,0)

        self.assertEqual(len(engine.core.champions),0)
        self.assertEqual(frame.iloc[0].rest_days_diff,0)

        self.assertEqual(frame.iloc[0].format_known,0)

        self.assertEqual(frame.iloc[0].bo5,0)



    def test_cross_year_results_are_not_flushed_into_earlier_test_start(self):

        games,metadata=fixture(1)

        games[0].date=datetime(2025,12,31,23,tzinfo=timezone.utc)

        games[0].available=games[0].date+timedelta(hours=2)

        _,engine=replay(games,metadata,advanced=False,finish=False)

        next_game=deepcopy(games[0]);next_game.gameid='next'

        next_game.date=datetime(2026,1,1,0,tzinfo=timezone.utc)

        row=engine.before(next_game,metadata['0'])

        self.assertEqual(row['broad_elo_diff'],0)



    def test_calibration_refuses_other_years(self):

        frame=pd.DataFrame({'date':pd.date_range('2026-01-01',periods=20,tz='UTC'),'year':2026,'target':[0,1]*10})

        with self.assertRaises(ValueError):calibrate(frame,np.full(20,.5))



    def test_complete_final_pipeline_on_synthetic_data_only(self):
        artifact=BASE/'artifacts/frozen_bundle.pkl'
        if not artifact.exists():self.skipTest('Train before end-to-end preflight')
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            root=Path(temp);(root/'artifacts').mkdir();(root/'data').mkdir()
            (root/'artifacts/frozen_bundle.pkl').write_bytes(artifact.read_bytes())
            (root/'freeze.json').write_text('{}')
            (root/'README.md').write_text('<!-- V7_FINAL_START --><!-- V7_FINAL_END -->')
            records=[]
            for day in range(4):
                for side,team,result,prefix in [('Blue','Synthetic A',day%2,'a'),('Red','Synthetic B',1-day%2,'b')]:
                    for role in ['top','jng','mid','bot','sup']:
                        records.append(dict(gameid='synthetic-'+str(day),date=f'2026-01-{day+5:02} 10:00:00',
                            side=side,teamname=team,result=result,position=role,champion=prefix+role,
                            playerid=prefix+role,playername=prefix+role,patch=16.01,league='LCK',
                            gamelength=1800,game=1,playoffs=0,split='Spring',firstPick=0,year=2026))
            raw=root/'data/synthetic.csv';pd.DataFrame(records).to_csv(raw,index=False)
            (root/'holdout_manifest.json').write_text(json.dumps({'path':'data/synthetic.csv','sha256':digest(raw)}))
            with patch.object(final_module,'BASE',root),patch.object(final_module,'verify_frozen',return_value={}), \
                 patch.object(reporting,'BASE',root),patch.object(reporting,'ROOT',root),contextlib.redirect_stdout(io.StringIO()):
                final_module.run()
                with self.assertRaises(RuntimeError):final_module.run()
            report=json.loads((root/'final_report.json').read_text())
            self.assertEqual(report['metrics']['v7']['games'],4)
            self.assertTrue((root/'final_run.claim').exists())
            self.assertTrue((root/'final_calibration.png').exists())

    def test_final_claim_is_exclusive(self):

        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:

            path=Path(temp)/'claim'

            claim(path)

            with self.assertRaises(FileExistsError):claim(path)



    def test_development_import_refuses_2026(self):

        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:

            path=Path(temp)/'source.csv'

            pd.DataFrame([dict(gameid='x',date='2026-01-01',league='LCK',position='top')]).to_csv(path,index=False)

            with self.assertRaises(ValueError):build([path],Path(temp)/'dev.sqlite')





if __name__=='__main__':unittest.main()

