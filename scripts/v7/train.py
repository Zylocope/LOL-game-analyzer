"""Development folds and 2025 calibration only. Never opens the sealed path."""
from datetime import datetime,timezone
import json
import pickle
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from scipy.special import expit
from threadpoolctl import threadpool_limits
from backend.features import read_games as old_read,FEATURES as V6_FEATURES
from backend.models import ProbabilityModel
from .lock import BASE,ROOT,digest
from .data import load,MAJOR
from .features import replay,RATING_FEATURES,CONTEXT_FEATURES,FORM_FEATURES,DRAFT_FEATURES
from .baseline import replay as v6_replay
from .modeling import Estimator,folds,evaluate_spec,score,calibrate,intervals,plot_calibration


def run():
    if (BASE/'freeze.json').exists():raise RuntimeError('Experiment frozen; training prohibited')
    if not (BASE/'holdout_manifest.json').exists():raise RuntimeError('Holdout must be locked first')
    started=perf_counter()
    games,metadata,skipped=load(BASE/'data/development.sqlite')
    if any(g.date.year>2025 for g in games):raise ValueError('Development year violation')
    protocol=json.loads((BASE/'protocol.json').read_text())
    rating_search=[];best=None
    for k,shrink,decay in protocol['rating_grid']:
        frame,engine=replay(games,metadata,k,shrink,decay,advanced=False)
        valid=frame.year.isin(folds(frame))
        metric=score(frame.loc[valid,'target'],expit(frame.loc[valid,'rating_logit']))
        record={'k':k,'shrink':shrink,'decay':decay,'development':metric}
        rating_search.append(record)
        if best is None or metric['log_loss']<best['development']['log_loss']:best=record
    print('Rating hyperparameters selected on development:',best,flush=True)
    frame,engine=replay(games,metadata,best['k'],best['shrink'],best['decay'],advanced=True,finish=False)
    artifact=BASE/'artifacts';artifact.mkdir(exist_ok=True)
    frame.to_pickle(artifact/'development_features.pkl')
    rating=['elo_diff','player_elo_diff','roster_stability_diff',*RATING_FEATURES]
    groups={'elo_ratings':['elo_diff','broad_elo_diff','broad_player_diff','regional_diff'],
            'glicko_ratings':['elo_diff','broad_elo_diff','broad_player_diff','regional_diff','glicko_diff','glicko_rd_diff','glicko_rd_sum'],
            'trueskill_ratings':['elo_diff','broad_elo_diff','broad_player_diff','regional_diff','ts_diff','ts_uncertainty_diff','ts_uncertainty_sum'],
            'all_ratings':rating, 'add_form':rating+FORM_FEATURES,
            'add_context':rating+FORM_FEATURES+CONTEXT_FEATURES,
            'full':rating+FORM_FEATURES+CONTEXT_FEATURES+DRAFT_FEATURES}
    candidates={}
    for group,features in groups.items():
        for C in protocol['logistic_C']:
            candidates[f'{group}_logistic_{C}']={'features':features,'family':'logistic','C':C}
    for trees,leaves in protocol['lightgbm_grid']:
        candidates[f'full_lightgbm_{trees}_{leaves}']={'features':groups['full'],'family':'lightgbm','trees':trees,'leaves':leaves}
    development=frame[frame.year<=2024]
    validation=frame[frame.year==2025].reset_index(drop=True)
    assessments={}
    for name,spec in candidates.items():
        assessments[name]=evaluate_spec(development,spec)
        print(name,round(assessments[name]['pooled']['log_loss'],5),flush=True)
    chosen=min(assessments,key=lambda name:assessments[name]['pooled']['log_loss'])
    group_winners={group:min([name for name in candidates if name.startswith(group+'_')],
        key=lambda name:assessments[name]['pooled']['log_loss']) for group in groups}
    # Include boosted in full-stage choice; no 2025 labels used in this choice.
    group_winners['full']=min([name for name in candidates if name.startswith('full_')],
        key=lambda name:assessments[name]['pooled']['log_loss'])
    fitted={};probabilities={};ablation={}
    elo=expit(validation.rating_logit.to_numpy())
    for group,name in group_winners.items():
        model=Estimator(**candidates[name]).fit(development)
        p=model.predict(validation)
        fitted[group]=model;probabilities[group]=p
        ablation[group]={'candidate':name,**score(validation.target,p)}
    selected=Estimator(**candidates[chosen]).fit(development)
    selected_p=selected.predict(validation)
    primary=[game for game in games if game.league in MAJOR]
    v6frame,v6engine=v6_replay(primary,finish=False)
    old_report=json.loads((ROOT/'backend/evaluation_v6.json').read_text())
    v6spec=old_report['validation'][old_report['selected_on_validation']]['spec']
    v6model=ProbabilityModel(**v6spec).fit(v6frame[v6frame.year<=2024],v6frame.loc[v6frame.year<=2024,'target'])
    v6validation=v6frame[v6frame.year==2025].reset_index(drop=True)
    if v6validation.gameid.tolist()!=validation.gameid.tolist():raise ValueError('Cohorts not aligned')
    v6p=v6model.predict_proba(v6validation)[:,1]
    # Original-data control isolates the impact of adding 2022/Worlds/aliases.
    original,_=old_read(ROOT/'backend/nexus_sight.db')
    original_frame,original_engine=v6_replay([g for g in original if g.date.year<=2024],finish=False)
    original_model=ProbabilityModel(**v6spec).fit(original_frame,original_frame.target)
    original_validation,original_engine=v6_replay([g for g in primary if g.date.year==2025],original_engine,finish=False)
    original_p=original_model.predict_proba(original_validation)[:,1]
    raw={'Elo':elo,'v6_original_data':original_p,'v6_expanded_data':v6p,'v7':selected_p}
    calibration={};calibrators={};tail_report={}
    for label,p in raw.items():
        model,selection,fit_mask=calibrate(validation,p)
        calibration[label]=selection;calibrators[label]=model
        # Honest 2025 calibration selection split, not all-data fitted calibration scores.
        from .modeling import Calibration
        tail=Calibration(selection['selected']).fit(p[fit_mask],validation.target.to_numpy()[fit_mask])
        tail_p=tail.predict(p[~fit_mask])
        tail_report[label]={'raw':score(validation.target.to_numpy()[~fit_mask],p[~fit_mask]),
                            'calibrated':score(validation.target.to_numpy()[~fit_mask],tail_p)}
    validation_metrics={label:score(validation.target,p) for label,p in raw.items()}
    for label,p in raw.items():
        validation_metrics[label]['vs_Elo']=intervals(validation,validation.target,p,elo)
        validation_metrics[label]['vs_v6']=intervals(validation,validation.target,p,v6p)
    for label,p in probabilities.items():
        ablation[label]['vs_Elo']=intervals(validation,validation.target,p,elo)
        ablation[label]['vs_v6']=intervals(validation,validation.target,p,v6p)
    report={'phase':'2025 validation (not final test)','chosen':chosen,'protocol':protocol,
            'rating_search':rating_search,'rating_selected':best,'development':assessments,
            'validation_raw':validation_metrics,'ablation_validation_raw':ablation,
            'calibration_selection':calibration,'calibration_selection_tail':tail_report,
            'coverage':json.loads((BASE/'coverage.json').read_text()),
            'feature_availability':{'scheduled_best_of_known_games':int(frame.format_known.sum()),
                                    'series_score_known_fraction':float(frame.series_score_known.mean()),
                                    'first_pick_known_fraction':float(frame.first_pick_known.mean())},
            'limitations':[
                'Scheduled best-of absent in OE source: masked unknown; no BO inferred from completed series length.',
                'Series linkage is same-day team pair plus source game ordinal, not an authoritative series ID.',
                'Fearless era flag is a time proxy, not a tournament-specific rule; constant pre-2025, so its effect is not learned.',
                'Glicko-2 player updates approximate the opponent team by mean rating and aggregate deviation; TrueSkill uses actual 5v5.',
                'Validation-tail calibration selection is optimistic; final 2026 is the only locked final evaluation.',
                'CIs cluster by UTC date and condition on selected models; selection uncertainty is not included.',
                'v6 code unchanged; v6 expanded-data control and original-data control both refit only through 2024.',
                'Conservative outcome availability uses max(2 hours, recorded duration + 15 minutes).'],
            'seconds':perf_counter()-started}
    (BASE/'validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
    plot_calibration(validation.target,raw,BASE/'validation_calibration.png','2025 validation: uncalibrated models')
    bundle={'model':selected,'engine':engine,'v6_model':v6model,'v6_engine':v6engine,
            'original_model':original_model,'original_engine':original_engine,
            'calibrators':calibrators,'chosen':chosen,'rating':best,'features':candidates[chosen]['features'],
            'ablation_models':fitted,'report':report}
    with (artifact/'frozen_bundle.pkl').open('wb') as handle:pickle.dump(bundle,handle)
    print(json.dumps({'chosen':chosen,'validation':validation_metrics,'seconds':report['seconds']},indent=2),flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=1):run()
