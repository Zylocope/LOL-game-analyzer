"""Lock the opaque 2026 download and the unchanged v6 baseline before development."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'scripts/v7'
SOURCE = 'https://drive.usercontent.google.com/download?id=1hnpbrUpBMS1TZI7IovfpKeZfWJH1Aptm&export=download&confirm=t'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def lock():
    manifest_path = BASE/'holdout_manifest.json'
    if manifest_path.exists():
        record = json.loads(manifest_path.read_text())
        if digest(BASE/record['path']) != record['sha256']:
            raise ValueError('Sealed bytes changed')
        print('Existing holdout lock verified; no contents read or exposed.')
        return
    sealed = BASE/'data/sealed/2026.csv'
    sealed.parent.mkdir(parents=True, exist_ok=True)
    if sealed.exists():
        raise FileExistsError('Unmanifested holdout exists; refusing to replace it')
    with urllib.request.urlopen(SOURCE, timeout=120) as response, sealed.open('xb') as out:
        if 'html' in response.headers.get('Content-Type', '').lower():
            raise ValueError('Source returned HTML')
        shutil.copyfileobj(response, out, 1024*1024)
    record = {'source': SOURCE, 'path': 'data/sealed/2026.csv', 'sha256': digest(sealed),
              'downloaded_utc': datetime.now(timezone.utc).isoformat(),
              'policy': 'Opaque bytes only until the frozen final evaluator runs once; never parse in development.'}
    manifest_path.write_text(json.dumps(record, indent=2)+'\n')
    files = ['backend/features.py','backend/models.py','backend/experiment.py',
             'backend/model_v6.pkl','backend/evaluation_v6.json','backend/nexus_sight.db']
    (BASE/'v6_manifest.json').write_text(json.dumps({p:digest(ROOT/p) for p in files},indent=2)+'\n')
    print('2026 raw bytes sealed; SHA-256 recorded. v6 code/model/database locked. No rows inspected.')


if __name__ == '__main__':
    lock()
