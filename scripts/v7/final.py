"""ONE attempt only. Never called by training or discovery tests."""
from datetime import datetime,timezone
import json
import os
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from threadpoolctl import threadpool_limits
from .lock import BASE,digest
from .freeze import verify_frozen
from .data import build,MAJOR
from .modeling import score,intervals,plot_calibration
from .reporting import write_final


def claim(path):
    with Path(path).open('x') as handle:
        handle.write(datetime.now(timezone.utc).isoformat())


def run():
    frozen=verify_frozen()
    sealed=json.loads((BASE/'holdout_manifest.json').read_text())
    raw=BASE/sealed['path']
    if digest(raw)!=sealed['sha256']:raise ValueError('Holdout hash mismatch')
    if (BASE/'final_report.json').exists():raise RuntimeError('Final results already exist')
    with (BASE/'artifacts/frozen_bundle.pkl').open('rb') as handle:bundle=pickle.load(handle)
    # Claim permanently before the first parser touches the sealed contents.
    claim(BASE/'final_run.claim')
    try:
        games,metadata,excluded=build([raw],BASE/'data/final_2026.sqlite',final=True)
        rows,v6rows,original_rows=[],[],[]
        for game in games:
            context=metadata[game.gameid]
            row=bundle['engine'].before(game,context)
            if row is not None:
                rows.append(row)
                v6rows.append(bundle['v6_engine'].before(game))
                original_rows.append(bundle['original_engine'].before(game))
                bundle['v6_engine'].push(game);bundle['original_engine'].push(game)
            bundle['engine'].push(game,context)
        frame=pd.DataFrame(rows)
        if frame.empty:raise ValueError('No eligible major-cohort games in sealed snapshot')
        v6frame,original_frame=pd.DataFrame(v6rows),pd.DataFrame(original_rows)
        predictions={'Elo':expit(frame.rating_logit.to_numpy()),
                     'v6_original_data':bundle['original_model'].predict_proba(original_frame)[:,1],
                     'v6_expanded_data':bundle['v6_model'].predict_proba(v6frame)[:,1],
                     'v7_raw':bundle['model'].predict(frame)}
        for name,key in [('Elo_calibrated','Elo'),('v6_calibrated','v6_expanded_data'),('v7','v7_raw')]:
            calibrator=bundle['calibrators']['v7' if key=='v7_raw' else key]
            predictions[name]=calibrator.predict(predictions[key])
        y=frame.target.to_numpy()
        metrics={name:score(y,p) for name,p in predictions.items()}
        for name,p in predictions.items():
            metrics[name]['vs_Elo']=intervals(frame,y,p,predictions['Elo'])
            metrics[name]['vs_v6']=intervals(frame,y,p,predictions['v6_expanded_data'])
        ablation={}
        for name,model in bundle['ablation_models'].items():
            p=model.predict(frame)
            ablation[name]={**score(y,p),'vs_Elo':intervals(frame,y,p,predictions['Elo']),
                            'vs_v6':intervals(frame,y,p,predictions['v6_expanded_data'])}
        plot_calibration(y,{name:predictions[name] for name in ['Elo','v6_expanded_data','v7']},
                         BASE/'final_calibration.png','2026: single frozen evaluation')
        records=frame[['gameid','date','league','cohort','target']].copy()
        for name,p in predictions.items():records[name]=p
        records.to_csv(BASE/'artifacts/final_predictions.csv',index=False)
        report={'phase':'FINAL 2026 — no subsequent changes permitted',
            'evaluated_utc':datetime.now(timezone.utc).isoformat(),'holdout_sha256':sealed['sha256'],
            'freeze_sha256':digest(BASE/'freeze.json'),'model':bundle['chosen'],
            'metrics':metrics,'ablation':ablation,'excluded_incomplete_games':excluded,
            'date_range':[str(frame.date.min()),str(frame.date.max())],
            'rating_only_games':len(games)-len(frame),'cohorts':frame.cohort.value_counts().to_dict(),
            'calibration_methods':{k:v.method for k,v in bundle['calibrators'].items()},
            'limitations':bundle['report']['limitations']+[
                'The 2026 yearly source is a snapshot at retrieval time, not guaranteed to be the full season.',
                'Ratings may update online using earlier completed 2026 results; model and calibration never refit.',
                'No v7 application deployment: the existing app still serves preserved v6.'],
            'integrity':{'v6_unchanged':True,'single_run_claim':'final_run.claim'}}
        write_final(report)
        verify_frozen()
        print(json.dumps({'final_metrics':metrics,'date_range':report['date_range'],'report':'scripts/v7/FINAL_REPORT.md'},indent=2),flush=True)
    except BaseException as exc:
        (BASE/'final_failure.json').write_text(json.dumps({'error':repr(exc),'policy':'claim retained; no automatic rerun'},indent=2))
        raise


if __name__=='__main__':
    os.environ.setdefault('MPLCONFIGDIR',str(BASE/'artifacts/mpl'))
    with threadpool_limits(limits=1):run()
