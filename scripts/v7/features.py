"""Pre-start v7 replay; secondary leagues affect Ratings only."""
import heapq
import math
import pandas as pd
from backend.features import FeatureState, FEATURES as V6_FEATURES, normalize
from .data import MAJOR
from .ratings import Ratings

RATING_FEATURES=['broad_elo_diff','broad_player_diff','regional_diff','ts_diff','ts_uncertainty_diff',
                 'ts_uncertainty_sum','glicko_diff','glicko_rd_diff','glicko_rd_sum']
CONTEXT_FEATURES=['rest_days_diff','roster_change_diff','game_number','series_score_diff',
                  'series_score_known','fearless_era','blue_first_pick','first_pick_known',
                  'bo1','bo3','bo5','format_known']
FORM_FEATURES=['form_diff','player_form_diff']
DRAFT_FEATURES=['patch_strength_diff','patch_coverage_diff','comfort_diff','comfort_residual_diff','lane_counter_diff']


class Replay:
    def __init__(self,k=16,shrink=.2,decay=0.,advanced=True):
        self.core=FeatureState(k,shrink)
        self.ratings=Ratings(k,shrink,decay,advanced)
        self.series={}
        self.primary_last={}
        self.pending=[]

    def update(self,game,metadata):
        self.ratings.update(game)
        if game.league in MAJOR:
            self.core.begin(game.date.year)
            self.core.update(game)
            self.primary_last[normalize(game.blue[0]['teamname'])]=game.date
            self.primary_last[normalize(game.red[0]['teamname'])]=game.date
            key=metadata['series_key']
            score=self.series.setdefault(key,{})
            for own,result in [(game.blue,game.target),(game.red,1-game.target)]:
                name=normalize(own[0]['teamname'])
                wins,count=score.get(name,(0,0))
                score[name]=(wins+result,count+1)

    def before(self,game,metadata):
        while self.pending and self.pending[0][0]<game.date:
            _,_,old,context=heapq.heappop(self.pending)
            self.update(old,context)
        self.core.begin(game.date.year)
        ratings=self.ratings.features(game)
        if game.league not in MAJOR:
            return None
        vector=dict(zip(V6_FEATURES,self.core.vector(game.blue,game.red,game.patch)))
        vector.update(ratings)
        names=[normalize(rows[0]['teamname']) for rows in [game.blue,game.red]]
        rest=[min(365.,max(0.,(game.date-self.primary_last[name]).total_seconds()/86400)) if name in self.primary_last else 365. for name in names]
        vector['rest_days_diff']=rest[0]-rest[1]
        score=self.series.get(metadata['series_key'],{})
        a,b=[score.get(name,(0,0)) for name in names]
        known=int(a[1]==b[1]==metadata['game_number']-1)
        # Format is genuinely pre-game only. Missing scheduled best-of is masked,
        # never derived from the final number of games or a series winner.
        best_of=metadata.get('best_of',0)
        vector.update(roster_change_diff=-vector['roster_stability_diff'],
                      game_number=metadata['game_number'], series_score_diff=(a[0]-b[0]) if known else 0.,
                      series_score_known=known,fearless_era=int(game.date.year>=2025),
                      blue_first_pick=max(0.,metadata['first_pick']),first_pick_known=int(metadata['first_pick']>=0),
                      bo1=int(best_of==1),bo3=int(best_of==3),bo5=int(best_of==5),format_known=int(best_of in (1,3,5)))
        vector.update(gameid=game.gameid,date=game.date,year=game.date.year,league=game.league,
                      target=game.target,cohort=MAJOR[game.league])
        return vector

    def push(self,game,metadata):
        heapq.heappush(self.pending,(game.available,game.gameid,game,metadata))

    def finish(self):
        while self.pending:
            _,_,game,metadata=heapq.heappop(self.pending)
            self.update(game,metadata)


def replay(games,metadata,k=16,shrink=.2,decay=0.,advanced=True,finish=True):
    engine=Replay(k,shrink,decay,advanced)
    rows=[]
    for index,game in enumerate(games):
        context=metadata[game.gameid]
        row=engine.before(game,context)
        if row is not None: rows.append(row)
        engine.push(game,context)
        if advanced and (index+1)%10000==0: print(f'Advanced ratings replay: {index+1} development games',flush=True)
    if finish:engine.finish()
    return pd.DataFrame(rows),engine
