"""Fast feature replay and season-based comparisons; never select on 2025."""
from pathlib import Path
from time import perf_counter
import json
import os
import pickle

import numpy as np
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss

from .features import FEATURES, read_games, replay
from .models import ProbabilityModel

BASE = Path(__file__).resolve().parent
VERSION = 'v6_elo_corrections'
GROUPS = {
    'elo_only': ['elo_diff'],
    'players': ['elo_diff', 'player_elo_diff', 'roster_stability_diff'],
    'form': ['elo_diff', 'player_elo_diff', 'roster_stability_diff', 'form_diff', 'player_form_diff'],
    'draft': FEATURES,
}


def metrics(y, p):
    return {'accuracy': float(accuracy_score(y, p >= .5)),
            'log_loss': float(log_loss(y, p, labels=[0, 1])),
            'brier_score': float(brier_score_loss(y, p)), 'games': len(y)}


def seasons(frame, before):
    return [int(year) for year in sorted(frame.year.unique()) if year < before
            and (frame.year < year).sum() >= 500 and (frame.year == year).sum() >= 100][-3:]


def walk_forward(frame, spec, years):
    predictions, targets = [], []
    folds = []
    for year in years:
        train, valid = frame[frame.year < year], frame[frame.year == year]
        model = ProbabilityModel(**spec).fit(train, train.target)
        p = model.predict_proba(valid)[:, 1]
        predictions.extend(p)
        targets.extend(valid.target)
        folds.append({'year': year, 'train_games': len(train), **metrics(valid.target, p)})
    return metrics(np.array(targets), np.array(predictions)), folds


def paired_intervals(frame, target, p, baseline):
    """Bootstrap calendar days, keeping correlated same-day games together."""
    eps = 1e-12
    loss = lambda probability: -(target*np.log(np.clip(probability,eps,1-eps)) +
                                 (1-target)*np.log(np.clip(1-probability,eps,1-eps)))
    delta_loss = loss(baseline) - loss(p)
    delta_acc = ((p >= .5) == target).astype(float) - ((baseline >= .5) == target).astype(float)
    groups = frame.date.dt.floor('D').to_numpy()
    unique = np.unique(groups)
    sums = np.array([[delta_loss[groups == day].sum(), delta_acc[groups == day].sum(),
                      (groups == day).sum()] for day in unique])
    rng = np.random.default_rng(42)
    samples = sums[rng.integers(0, len(sums), size=(2000, len(sums)))].sum(axis=1)
    return {'method': '2000 paired calendar-day bootstrap replicates; positive favors candidate',
            'accuracy_delta_95': np.quantile(samples[:, 1]/samples[:, 2], [.025,.975]).tolist(),
            'log_loss_improvement_95': np.quantile(samples[:, 0]/samples[:, 2], [.025,.975]).tolist()}


def run(db_path=BASE/'nexus_sight.db', output_dir=BASE):
    started = perf_counter()
    games, skipped = read_games(db_path)
    if not games or games[-1].date.year < 2025:
        raise ValueError('This benchmark requires a 2025 reporting season and earlier training seasons')
    print(f'Read {len(games)} complete games; {skipped} excluded.', flush=True)
    # 2025 has already been inspected in v5. This is a retrospective benchmark,
    # never described as a pristine unseen holdout.
    evaluation_year = 2025
    tuning = []
    best_data, best_rating = None, None
    for k, shrink in [(16,0.), (32,0.), (48,0.), (16,.2), (32,.2), (48,.2)]:
        feature_start = perf_counter()
        frame, state = replay(games, k, shrink)
        years = seasons(frame, evaluation_year)
        if len(years) < 2:
            raise ValueError('At least two eligible development seasons required')
        score, _ = walk_forward(frame, dict(features=['elo_diff'], family='elo'), years)
        entry = {'k': k, 'season_shrink': shrink, 'validation': score,
                 'replay_seconds': perf_counter()-feature_start}
        tuning.append(entry)
        if best_rating is None or score['log_loss'] < best_rating['validation']['log_loss']:
            best_rating, best_data = entry, (frame, state)
    frame, state = best_data
    development, test = frame[frame.year < evaluation_year], frame[frame.year == evaluation_year]
    years = seasons(frame, evaluation_year)
    candidates = {'elo_formula': dict(features=['elo_diff'], family='elo')}
    for group, features in GROUPS.items():
        for alpha in [.01,.1,1.]:
            candidates[f'{group}_residual_{alpha}'] = dict(features=features, family='residual', regularization=alpha)
    for group in ['elo_only', 'draft']:
        candidates[f'{group}_logistic'] = dict(features=GROUPS[group], family='logistic', regularization=.1)
    candidates['draft_boosted'] = dict(features=FEATURES, family='boosted')
    validation = {}
    for name, spec in candidates.items():
        score, folds = walk_forward(frame, spec, years)
        validation[name] = {'aggregate': score, 'folds': folds, 'spec': spec}
    chosen = min(validation, key=lambda name: validation[name]['aggregate']['log_loss'])
    # Fix group winners on development folds before looking at reporting outcomes.
    winners = {'elo_formula': 'elo_formula'}
    for group in GROUPS:
        options = [name for name in candidates if name.startswith(group+'_')]
        winners[group] = min(options, key=lambda name: validation[name]['aggregate']['log_loss'])
    winners['selected'] = chosen
    results, predictions = {}, {}
    for label, name in winners.items():
        model = ProbabilityModel(**candidates[name]).fit(development, development.target)
        p = model.predict_proba(test)[:, 1]
        predictions[label] = p
        results[label] = {'candidate': name, **metrics(test.target, p)}
    for label in results:
        if label != 'elo_formula':
            results[label]['paired_vs_elo'] = paired_intervals(test, test.target.to_numpy(),
                                                              predictions[label], predictions['elo_formula'])
    report = {
        'version': VERSION, 'selected_on_validation': chosen,
        'protocol': 'Expanding-season development folds; 2025 retrospective reporting only; 2h minimum outcome delay',
        'data': {'games': len(games), 'skipped_games': skipped,
                 'first_date': str(frame.date.min()), 'last_date': str(frame.date.max()),
                 'coverage': frame.groupby(['year','league']).size().reset_index(name='games').to_dict('records')},
        'rating_search': tuning, 'rating_selected': {key: best_rating[key] for key in ['k','season_shrink']},
        'validation': validation, 'development_years': years, 'reporting_year': evaluation_year,
        'test': results,
        'limitations': ['2025 was previously inspected in v5; these are retrospective comparisons, not a new untouched holdout.',
                       'Rating parameters and model hyperparameters share development folds; selection bias remains possible.',
                       'Outcome availability approximated by max(2 hours, duration + 15 minutes), not official completion timestamps.',
                       'No 2022 or Worlds games in the supplied database. LPL and MSI are present.',
                       'Bootstrap intervals do not capture model-selection uncertainty or future data shifts.'],
    }
    final_model = ProbabilityModel(**candidates[chosen]).fit(frame, frame.target)
    report['timing'] = {'total_seconds': perf_counter()-started,
                        'selected_replay_seconds': best_rating['replay_seconds']}
    bundle = {'version': VERSION, 'model': final_model, 'features': candidates[chosen]['features'],
              'state': state, 'snapshot': state.snapshot(), 'evaluation': report}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir/'model_v6.pkl'
    with model_path.with_suffix('.tmp').open('wb') as handle:
        pickle.dump(bundle, handle)
    os.replace(model_path.with_suffix('.tmp'), model_path)
    (output_dir/'evaluation_v6.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    frame.to_csv(output_dir/'dataset_v6.csv', index=False)
    print(json.dumps({'chosen': chosen, 'ratings': report['rating_selected'],
                      'results': results, 'timing': report['timing']}, indent=2), flush=True)
    return report


if __name__ == '__main__':
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        run()
