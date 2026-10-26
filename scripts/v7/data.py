"""Allowlisted raw fields; development imports reject any year above 2025."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import pandas as pd
from .lock import BASE, ROOT, digest
from backend.features import read_games

MAJOR = {'LCK':'LCK','LPL':'LPL','LEC':'LEC','EU LCS':'LEC','LCS':'NA','NA LCS':'NA',
         'LTA':'NA','LTA N':'NA','MSI':'International','W':'International','WLDs':'International',
         'Worlds':'International'}
SECONDARY = {'LCKC':'KR','LCK CL':'KR','CK':'KR','LDL':'CN','PCS':'APAC','LCP':'APAC',
             'LMS':'APAC','VCS':'VN','CBLOL':'BR','LTA S':'BR','LJL':'JP'}
REGIONS = {'LCK':'KR','LPL':'CN','LEC':'EU','EU LCS':'EU','LCS':'NA','NA LCS':'NA',
           'LTA N':'NA', **SECONDARY}
COLUMNS = ['gameid','date','side','teamname','teamid','result','position','champion',
           'playerid','playername','patch','league','gamelength','game','playoffs','split','firstPick','year']


def build(raw_paths, destination, final=False):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('Database already exists; never silently overwrite a benchmark input')
    with closing(sqlite3.connect(destination)) as conn:
        for path in raw_paths:
            with pd.read_csv(path, chunksize=25000, usecols=lambda c:c in COLUMNS, low_memory=False) as reader:
                for chunk in reader:
                    years = pd.to_datetime(chunk.date, errors='coerce', utc=True).dt.year
                    if (years > (2026 if final else 2025)).any() or (final and (years.dropna() != 2026).any()):
                        raise ValueError('Temporal boundary violation')
                    chunk = chunk[chunk.league.isin(set(MAJOR)|set(SECONDARY)) & (chunk.position != 'team')].copy()
                    if not chunk.empty:
                        chunk.to_sql('player_stats',conn,if_exists='append',index=False)
        conn.execute('CREATE INDEX games ON player_stats(gameid)')
        conn.commit()
    return load(destination)


def load(destination):
    games, skipped = read_games(destination)
    with closing(sqlite3.connect(destination)) as conn:
        conn.row_factory=sqlite3.Row
        metadata={r['gameid']:dict(r) for r in conn.execute("SELECT gameid,game,playoffs,split,firstPick FROM player_stats WHERE lower(side)='blue' GROUP BY gameid")}
    sessions, meta = {}, {}
    for game in games:
        r=metadata[game.gameid]
        number=int(r['game'] or 1)
        key=(game.league,str(game.date.date()),tuple(sorted([game.blue[0]['teamname'],game.red[0]['teamname']])))
        if key not in sessions or number==1:
            sessions[key]=sessions.get(key,0)+1
        meta[game.gameid]={'game_number':number,'series_key':(key,sessions[key]),
                          'playoffs':int(r['playoffs'] or 0),'first_pick':float(r['firstPick']) if r['firstPick'] is not None else -1}
    return games,meta,skipped


def development():
    manifest=json.loads((BASE/'development_manifest.json').read_text())
    paths=[]
    for year in range(2018,2026):
        record=manifest[str(year)]
        path=BASE/record['path']
        if digest(path)!=record['sha256']:
            raise ValueError('Development source hash mismatch')
        paths.append(path)
    db=BASE/'data/development.sqlite'
    return build(paths,db)


if __name__=='__main__':
    games,meta,skipped=development()
    coverage=pd.DataFrame([{'year':g.date.year,'league':g.league,'major':g.league in MAJOR} for g in games])
    report={'usable_games':len(games),'excluded_games':skipped,
            'coverage':coverage.groupby(['year','league','major']).size().reset_index(name='games').to_dict('records')}
    (BASE/'coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Development database built; coverage saved. Holdout untouched.')
