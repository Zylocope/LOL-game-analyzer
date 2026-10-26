import React, { useEffect, useState } from 'react';
import { ChampionSelectModal } from './ChampionSelectModal';
import { API_URL } from '../services/api';
import { championIcon, championId } from '../services/champions';

const ROLES = ['Top', 'Jungle', 'Mid', 'Bot', 'Support'] as const;
type Side = 'blue' | 'red';
type Draft = Record<Side, string[]>;

interface Summary { matches: number; test_games: number; accuracy: number; blue_side_accuracy: number; patches: string[]; server: string }
interface Result {
  blueWinChance: number; redWinChance: number; factors: string[];
  picks: { side: Side; role: string; champion: string; effect: number }[];
}

const empty = (): Draft => ({ blue: ['', '', '', '', ''], red: ['', '', '', '', ''] });

const Icon: React.FC<{ name: string }> = ({ name }) => {
  const [failed, setFailed] = useState(false);
  if (!name) return <div className="h-11 w-11 rounded-lg border border-dashed border-gray-700 bg-gray-900" />;
  return failed
    ? <div className="grid h-11 w-11 place-items-center rounded-lg bg-gray-800 text-xs font-bold text-gray-300">{name.slice(0, 2)}</div>
    : <img src={championIcon(name)} alt="" onError={() => setFailed(true)} className="h-11 w-11 rounded-lg object-cover" />;
};

export const RankedDraft: React.FC = () => {
  const [draft, setDraft] = useState<Draft>(empty);
  const [picking, setPicking] = useState<{ side: Side; index: number } | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/ranked/info`).then(r => r.json()).then(d => setSummary(d.summary ?? null)).catch(() => {});
  }, []);

  const taken = new Set([...draft.blue, ...draft.red].filter(Boolean));
  const complete = taken.size === 10;

  const pick = (champion: string) => {
    if (!picking) return;
    setDraft(d => ({ ...d, [picking.side]: d[picking.side].map((c, i) => (i === picking.index ? champion : c)) }));
    setResult(null);
  };

  const analyze = async () => {
    setLoading(true); setError('');
    try {
      const response = await fetch(`${API_URL}/api/ranked/predict`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ blue: draft.blue.map(championId), red: draft.red.map(championId) }),
      });
      if (!response.ok) throw new Error('Prediction is unavailable right now. Please try again in a minute.');
      setResult(await response.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Prediction is unavailable right now.');
    } finally {
      setLoading(false);
    }
  };

  const column = (side: Side) => (
    <section className={`rounded-2xl border p-4 ${side === 'blue' ? 'border-blue-900/70 bg-blue-950/10' : 'border-red-900/70 bg-red-950/10'}`}>
      <h3 className={`mb-3 font-display text-xl font-bold tracking-widest ${side === 'blue' ? 'text-blue-300' : 'text-red-300'}`}>
        {side === 'blue' ? 'BLUE SIDE' : 'RED SIDE'}
      </h3>
      <div className="space-y-2">
        {ROLES.map((role, i) => (
          <button key={role} onClick={() => setPicking({ side, index: i })}
            className="flex w-full items-center gap-3 rounded-xl border border-gray-800 bg-gray-900/60 p-2 text-left transition hover:border-esport-gold/60">
            <span className="w-16 text-[11px] font-bold uppercase tracking-wider text-gray-500">{role}</span>
            <Icon name={draft[side][i]} />
            <span className={draft[side][i] ? 'font-semibold text-gray-100' : 'text-gray-500'}>{draft[side][i] || 'Pick champion'}</span>
          </button>
        ))}
      </div>
    </section>
  );

  const blue = result ? Math.round(result.blueWinChance * 100) : 50;
  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
      <div className="mb-6">
        <h2 className="font-display text-3xl font-bold tracking-wide text-white sm:text-4xl">Ranked Draft Analysis</h2>
        <p className="mt-1 text-sm text-gray-400">
          Ten champions, no teams. Based on {summary ? summary.matches.toLocaleString() : 'recent'} Master+ ranked games
          {summary ? ` (${summary.server}, patches ${summary.patches.join(', ')} and earlier)` : ''}.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">{column('blue')}{column('red')}</div>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <button onClick={analyze} disabled={!complete || loading}
          className="rounded-full bg-esport-gold px-8 py-3 font-display font-bold tracking-widest text-black transition hover:bg-white disabled:cursor-not-allowed disabled:bg-gray-800 disabled:text-gray-500">
          {loading ? 'ANALYZING…' : 'ANALYZE DRAFT'}
        </button>
        <button onClick={() => { setDraft(empty()); setResult(null); setError(''); }}
          className="rounded-full border border-gray-700 px-6 py-3 text-sm text-gray-300 hover:border-gray-500">Clear</button>
        {!complete && <span className="text-sm text-gray-500">{10 - taken.size} picks left</span>}
      </div>

      {error && <p role="alert" className="mt-4 rounded-lg border border-red-800 bg-red-950/30 p-4 text-red-300">{error}</p>}

      {result && (
        <section className="mt-6 rounded-2xl border border-gray-800 bg-gray-900/60 p-5" aria-live="polite">
          <div className="mb-2 flex justify-between font-display text-2xl font-bold">
            <span className="text-blue-300">Blue {blue}%</span><span className="text-red-300">{100 - blue}% Red</span>
          </div>
          <div className="flex h-3 overflow-hidden rounded-full bg-gray-800">
            <div className="bg-blue-500" style={{ width: `${blue}%` }} /><div className="flex-1 bg-red-500" />
          </div>
          <ul className="mt-4 space-y-2 text-sm text-gray-300">
            {result.factors.map((f, i) => <li key={i}>• {f}</li>)}
          </ul>
          <details className="mt-4 text-sm text-gray-400">
            <summary className="cursor-pointer text-gray-300">Effect of each pick</summary>
            <div className="mt-2 grid gap-1 sm:grid-cols-2">
              {result.picks.map(p => (
                <div key={`${p.side}-${p.role}`} className="flex justify-between rounded bg-gray-950/50 px-3 py-1">
                  <span className={p.side === 'blue' ? 'text-blue-300' : 'text-red-300'}>{p.champion} · {p.role}</span>
                  <span>{p.effect > 0 ? '+' : ''}{p.effect} pts</span>
                </div>
              ))}
            </div>
            <p className="mt-2 text-xs text-gray-500">Points = change in that team's win chance compared with an average pick in the same role.</p>
          </details>
        </section>
      )}

      {summary && (
        <p className="mt-6 text-xs text-gray-500">
          Tested on the newest {summary.test_games.toLocaleString()} games: right {(summary.accuracy * 100).toFixed(1)}% of the time
          (always picking blue side: {(summary.blue_side_accuracy * 100).toFixed(1)}%). In ranked, the draft is a small part of who wins.
        </p>
      )}

      <ChampionSelectModal isOpen={picking !== null} onClose={() => setPicking(null)} onSelect={pick}
        unavailableChampions={taken} />
    </main>
  );
};
