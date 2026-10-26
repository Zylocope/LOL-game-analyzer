"""Adapter around unmodified v6 state and model classes."""
import heapq
import pandas as pd
from backend.features import FeatureState,FEATURES


class V6Replay:
    def __init__(self):self.state=FeatureState(16,.2);self.pending=[]
    def before(self,game):
        while self.pending and self.pending[0][0]<game.date:
            _,_,old=heapq.heappop(self.pending)
            self.state.begin(old.date.year);self.state.update(old)
        self.state.begin(game.date.year)
        row=dict(zip(FEATURES,self.state.vector(game.blue,game.red,game.patch)))
        row.update(gameid=game.gameid,date=game.date,year=game.date.year,target=game.target)
        return row
    def push(self,game):heapq.heappush(self.pending,(game.available,game.gameid,game))
    def finish(self):
        while self.pending:
            _,_,game=heapq.heappop(self.pending)
            self.state.begin(game.date.year);self.state.update(game)


def replay(games,engine=None,finish=True):
    engine=engine or V6Replay();rows=[]
    for game in games:
        rows.append(engine.before(game));engine.push(game)
    if finish:engine.finish()
    return pd.DataFrame(rows),engine
