import sqlite3, csv, math, random, collections

import os; D=os.path.expanduser("~/mnt/LOL-game-analyzer/scripts/v7")
def rows(f):
    c=sqlite3.connect(f'file:{D}/data/{f}?mode=ro',uri=True)
    return c.execute("select gameid,date,position,champion,side,result from player_stats where position in ('top','jng','mid','bot','sup') order by date").fetchall()
dev=rows('development.sqlite'); fin=rows('final_2026.sqlite')
preds={r['gameid']:r for r in csv.DictReader(open(f'{D}/artifacts/final_predictions.csv'))}
# history counts from dev
champ=collections.Counter(); champpos=collections.Counter()
seen=set()
for g,d,p,c,s,r in dev:
    champ[c]+=1; champpos[(c,p)]+=1
# group final rows by game, process chronologically (update history after each game)
games=collections.OrderedDict()
for g,d,p,c,s,r in fin:
    games.setdefault(g,{'date':d,'picks':[]})['picks'].append((p,c,s,r))
out=[]
for g,info in sorted(games.items(), key=lambda kv: kv[1]['date']):
    picks=info['picks']
    if g in preds and len(picks)==10:
        rare50=sum(champ[c]<50 for p,c,s,r in picks)
        rare20=sum(champ[c]<20 for p,c,s,r in picks)
        off=sum(champ[c]>=10 and champpos[(c,p)]/champ[c]<0.10 or (champ[c]<10 and champpos[(c,p)]==0) for p,c,s,r in picks)
        blue_res=[r for p,c,s,r in picks if s=='Blue'][0]
        pr=preds[g]; y=int(pr['target'])
        out.append(dict(y=y,blue=blue_res,v6=float(pr['v6_original_data']),elo=float(pr['Elo']),rare50=rare50,rare20=rare20,off=off))
    for p,c,s,r in picks: champ[c]+=1; champpos[(c,p)]+=1
print('games analysed',len(out),'target==blue result:',sum(o['y']==o['blue'] for o in out))
def metr(sub,k):
    n=len(sub); acc=sum((o[k]>0.5)==(o['y']==1) for o in sub)/n
    ll=-sum(math.log(o[k] if o['y'] else 1-o[k]) for o in sub)/n
    return n,acc,ll
def ci(sub,k,B=2000):
    random.seed(1); a=[]
    for _ in range(B):
        s=[random.choice(sub) for _ in sub]; a.append(metr(s,k)[1])
    a.sort(); return a[int(.025*B)],a[int(.975*B)]
def show(name,cond):
    for lab,sub in [('yes',[o for o in out if cond(o)]),('no',[o for o in out if not cond(o)])]:
        if not sub: continue
        n,acc,ll=metr(sub,'v6'); lo,hi=ci(sub,'v6'); _,ea,el=metr(sub,'elo')
        print(f"{name:28s} {lab:3s} n={n:5d} v6 acc={acc:.3f} [{lo:.3f},{hi:.3f}] ll={ll:.4f} | elo acc={ea:.3f} ll={el:.4f}")
show('any champ <50 prior games',lambda o:o['rare50']>0)
show('any champ <20 prior games',lambda o:o['rare20']>0)
show('2+ champs <50 prior games',lambda o:o['rare50']>=2)
show('any off-role pick',lambda o:o['off']>0)
print('all', metr(out,'v6'), metr(out,'elo'))
