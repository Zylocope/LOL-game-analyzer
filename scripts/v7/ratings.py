"""Online Elo, player TrueSkill, and Glicko-2; updates happen only on available results."""
from copy import deepcopy
import math
import numpy as np
from scipy.special import expit
from scipy.stats import norm
from glicko2 import Player
from trueskill import TrueSkill, Rating
from backend.features import normalize
from .data import REGIONS


class Ratings:
    def __init__(self,k=16,shrink=.2,decay=0.,advanced=False):
        self.k,self.shrink,self.decay,self.advanced=k,shrink,decay,advanced
        self.elo,self.players,self.last,self.player_last,self.regions,self.team_region={},{},{},{},{},{}
        self.ts,self.gl,self.gl_team={},{},{}
        self.ts_env=TrueSkill(draw_probability=0.)
        self.year=None
        self.decayed={}

    def __getstate__(self):
        state=self.__dict__.copy()
        state.pop('ts_env',None)
        return state

    def __setstate__(self,state):
        self.__dict__.update(state)
        self.ts_env=TrueSkill(draw_probability=0.)

    @staticmethod
    def ids(own):
        return [r['player'] or 'unknown:'+normalize(r['teamname'])+':'+r['position'] for r in own]

    def prepare(self,date):
        if self.year and date.year>self.year:
            factor=(1-self.shrink)**(date.year-self.year)
            self.elo={k:1200+(v-1200)*factor for k,v in self.elo.items()}
            self.players={k:1200+(v-1200)*factor for k,v in self.players.items()}
            self.regions={k:v*factor for k,v in self.regions.items()}
            self.ts={k:Rating(25+(r.mu-25)*factor,min(25/3,math.sqrt(r.sigma**2+4))) for k,r in self.ts.items()}
            for store in [self.gl,self.gl_team]:
                for r in store.values():
                    r.rating=1500+(r.rating-1500)*factor
                    r.rd=min(350,math.sqrt(r.rd*r.rd+2500))
        self.year=max(date.year,self.year or date.year)

    def team(self,name,date):
        key=normalize(name)
        value=self.elo.get(key,1200)
        previous=self.decayed.get(key)
        if previous and self.decay:
            days=max(0.,(date-previous).total_seconds()/86400)
            value=1200+(value-1200)*math.exp(-self.decay*days)
            self.elo[key]=value
        self.decayed[key]=date
        return value

    def features(self,game):
        self.prepare(game.date)
        names=[normalize(rows[0]['teamname']) for rows in [game.blue,game.red]]
        own=[self.ids(game.blue),self.ids(game.red)]
        teams=[self.team(name,game.date) for name in names]
        reg=[self.regions.get(self.team_region.get(name,'Unknown'),0.) for name in names]
        players=[sum(self.players.get(p,1200) for p in ids)/5 for ids in own]
        days=[min(365.,max(0.,(game.date-self.last[name]).total_seconds()/86400)) if name in self.last else 365. for name in names]
        out={'broad_elo_diff':teams[0]-teams[1], 'broad_player_diff':players[0]-players[1],
             'regional_diff':reg[0]-reg[1],'rest_days_diff':days[0]-days[1]}
        out['rating_logit']=(out['broad_elo_diff']+out['regional_diff'])*math.log(10)/400
        if self.advanced:
            ts=[[self.ts.get(p,Rating()) for p in ids] for ids in own]
            mu=[sum(r.mu for r in group) for group in ts]
            var=[sum(r.sigma**2 for r in group) for group in ts]
            gl=[[self.gl.get(p,Player()) for p in ids] for ids in own]
            out.update(ts_diff=(mu[0]-mu[1])/5,ts_uncertainty_diff=(math.sqrt(var[0])-math.sqrt(var[1]))/5,
                       ts_uncertainty_sum=(math.sqrt(var[0])+math.sqrt(var[1]))/5,
                       glicko_diff=(sum(r.rating for r in gl[0])-sum(r.rating for r in gl[1]))/5,
                       glicko_rd_diff=(sum(r.rd for r in gl[0])-sum(r.rd for r in gl[1]))/5,
                       glicko_rd_sum=(sum(r.rd for r in gl[0])+sum(r.rd for r in gl[1]))/5)
        return out

    def update(self,game):
        self.prepare(game.available)
        names=[normalize(rows[0]['teamname']) for rows in [game.blue,game.red]]
        ids=[self.ids(game.blue),self.ids(game.red)]
        if game.league in REGIONS:
            for name in names:self.team_region[name]=REGIONS[game.league]
        regions=[self.team_region.get(name,'Unknown') for name in names]
        values=[self.team(name,game.available)+self.regions.get(region,0.) for name,region in zip(names,regions)]
        expected=float(expit((values[0]-values[1])*math.log(10)/400))
        delta=self.k*(game.target-expected)
        for i,name in enumerate(names):
            self.elo[name]=self.elo.get(name,1200)+delta*(1 if i==0 else -1)
            self.last[name]=game.date
        if game.league in ('MSI','WLDs','W','Worlds') and regions[0]!=regions[1] and 'Unknown' not in regions:
            self.regions[regions[0]]=self.regions.get(regions[0],0.)+delta*.5
            self.regions[regions[1]]=self.regions.get(regions[1],0.)-delta*.5
        player_means=[sum(self.players.get(p,1200) for p in group)/5 for group in ids]
        player_delta=self.k*(game.target-float(expit((player_means[0]-player_means[1])*math.log(10)/400)))
        for i,group in enumerate(ids):
            for p in group:
                self.players[p]=self.players.get(p,1200)+player_delta*(1 if i==0 else -1)
                self.player_last[p]=game.date
        if self.advanced:
            groups=[tuple(self.ts.get(p,Rating()) for p in group) for group in ids]
            rated=self.ts_env.rate(groups,ranks=[0,1] if game.target else [1,0])
            for group,ratings in zip(ids,rated):
                for p,rating in zip(group,ratings):self.ts[p]=rating
            # Glicko-2 is head-to-head. Player updates use a documented
            # mean-opponent-team approximation; TrueSkill above is actual 5v5.
            old=[[deepcopy(self.gl.get(p,Player())) for p in group] for group in ids]
            for i,group in enumerate(ids):
                opponents=old[1-i]
                mean=sum(r.rating for r in opponents)/5
                rd=math.sqrt(sum(r.rd**2 for r in opponents))/5
                for p,r in zip(group,old[i]):
                    r.update_player([mean],[rd],[game.target if i==0 else 1-game.target])
                    self.gl[p]=r
