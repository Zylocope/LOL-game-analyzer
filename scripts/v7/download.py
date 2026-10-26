"""Development-only yearly downloads. 2026 is intentionally impossible here."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import urllib.request
from .lock import BASE, digest


def run():
    if not (BASE/'holdout_manifest.json').exists():
        raise RuntimeError('Seal 2026 before any development')
    sources = json.loads((BASE/'sources.json').read_text())['files']
    folder = BASE/'data/development_raw'
    folder.mkdir(parents=True, exist_ok=True)
    old = json.loads((BASE/'development_manifest.json').read_text()) if (BASE/'development_manifest.json').exists() else {}

    def download(year):
        year = str(year)
        path = folder/(year+'.csv')
        if year in old and path.exists():
            if digest(path) != old[year]['sha256']:
                raise ValueError(f'{year}: bytes changed')
            return year, old[year]
        url = 'https://drive.usercontent.google.com/download?id='+sources[year]['file_id']+'&export=download&confirm=t'
        tmp = path.with_suffix('.part')
        with urllib.request.urlopen(url, timeout=180) as response, tmp.open('wb') as out:
            if 'html' in response.headers.get('Content-Type','').lower():
                raise ValueError(f'{year}: returned HTML')
            shutil.copyfileobj(response, out, 1024*1024)
        tmp.replace(path)
        record = {'source':url,'sha256':digest(path),'path':str(path.relative_to(BASE)),
                  'retrieved_utc':datetime.now(timezone.utc).isoformat()}
        print(f'{year}: downloaded and fingerprinted', flush=True)
        return year,record

    results = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        for year, record in pool.map(download, range(2018,2026)):
            results[year] = record
            (BASE/'development_manifest.json').write_text(json.dumps(results,indent=2)+'\n')
    return results


if __name__ == '__main__':
    run()
