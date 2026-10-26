"""Seal executable sources and fitted artifacts before opening 2026."""
from datetime import datetime,timezone
import json
from pathlib import Path
from .lock import BASE,ROOT,digest


def verify_v6():
    for path,expected in json.loads((BASE/'v6_manifest.json').read_text()).items():
        if digest(ROOT/path)!=expected:raise ValueError('v6 baseline changed: '+path)


def verify_frozen():
    record=json.loads((BASE/'freeze.json').read_text())
    for path,expected in record['files'].items():
        if digest(ROOT/path)!=expected:raise ValueError('Frozen experiment changed: '+path)
    verify_v6()
    return record


def freeze():
    verify_v6()
    if (BASE/'freeze.json').exists():raise FileExistsError('Already frozen')
    if not (BASE/'artifacts/frozen_bundle.pkl').exists():raise ValueError('Train first')
    paths=list(BASE.glob('*.py'))+list(BASE.glob('*.json'))+[BASE/'requirements.txt',BASE/'DATA_DICTIONARY.md',
        BASE/'artifacts/frozen_bundle.pkl',BASE/'data/development.sqlite']
    files={str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in paths}
    record={'frozen_utc':datetime.now(timezone.utc).isoformat(),'files':files,
            'policy':'single final evaluator attempt; only deterministic reports may be written afterward'}
    with (BASE/'freeze.json').open('x') as handle:json.dump(record,handle,indent=2)
    print('Experiment frozen. Source, data, protocol, models and calibration fingerprinted.')


if __name__=='__main__':freeze()
