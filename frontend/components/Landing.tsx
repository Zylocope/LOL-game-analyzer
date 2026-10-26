import React, { useEffect, useRef, useState } from 'react';
import { API_URL } from '../services/api';

interface Props { onPro: () => void; onRanked: () => void }

const STAGES = ['Pro drafts', 'Ranked drafts', 'Honest numbers'];

/** Particle object that morphs sphere -> ring -> eye as the hero scrolls. Canvas 2D, no libraries. */
const Orb: React.FC<{ progress: number }> = ({ progress }) => {
  const canvas = useRef<HTMLCanvasElement>(null);
  const progressRef = useRef(progress);
  progressRef.current = progress;

  useEffect(() => {
    const el = canvas.current; if (!el) return;
    const ctx = el.getContext('2d'); if (!ctx) return;
    const N = 900, reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const golden = Math.PI * (3 - Math.sqrt(5));
    const shapes = [[], [], []] as number[][][];
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2, r = Math.sqrt(1 - y * y), t = golden * i;
      shapes[0].push([Math.cos(t) * r, y, Math.sin(t) * r]);                       // sphere
      const a = (i / N) * Math.PI * 2, tube = 0.22 * Math.cos(i * 7.3), tw = 0.22 * Math.sin(i * 7.3);
      shapes[1].push([(0.78 + tube) * Math.cos(a), tw, (0.78 + tube) * Math.sin(a)]); // ring
      const u = (i / N) * Math.PI * 2;
      if (i % 3 === 0) { const k = (i % 9) / 9; shapes[2].push([0.32 * k * Math.cos(u * 3), 0.32 * k * Math.sin(u * 3), 0]); } // iris
      else { const s = i % 2 ? 1 : -1; shapes[2].push([Math.cos(u), s * 0.42 * Math.sin(u) * Math.abs(Math.sin(u)) ** 0.2, 0]); } // lids
    }
    let frame = 0, raf = 0;
    const draw = () => {
      const dpr = Math.min(devicePixelRatio || 1, 2), w = el.clientWidth, h = el.clientHeight;
      if (el.width !== w * dpr) { el.width = w * dpr; el.height = h * dpr; }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, w, h);
      const p = Math.min(1.999, Math.max(0, progressRef.current * 2)), i0 = Math.floor(p), f = p - i0;
      const ease = f * f * (3 - 2 * f), A = shapes[i0], B = shapes[Math.min(2, i0 + 1)];
      const rot = reduce ? 0.6 : frame * 0.006, tilt = 0.35 + 0.25 * (i0 + ease) / 2, R = Math.min(w, h) * 0.42;
      for (let i = 0; i < N; i++) {
        let x = A[i][0] + (B[i][0] - A[i][0]) * ease, y = A[i][1] + (B[i][1] - A[i][1]) * ease, z = A[i][2] + (B[i][2] - A[i][2]) * ease;
        const spin = rot * (1 - 0.8 * ((i0 + ease) / 2));
        const cx = x * Math.cos(spin) - z * Math.sin(spin); z = x * Math.sin(spin) + z * Math.cos(spin); x = cx;
        const cy = y * Math.cos(tilt) - z * Math.sin(tilt); z = y * Math.sin(tilt) + z * Math.cos(tilt); y = cy;
        const depth = (z + 1.6) / 2.6, size = 0.6 + depth * 1.4;
        const warm = i % 5 === 0;
        ctx.fillStyle = warm ? `rgba(200,170,110,${0.35 + depth * 0.6})` : `rgba(226,232,240,${0.2 + depth * 0.7})`;
        ctx.beginPath(); ctx.arc(w / 2 + x * R, h / 2 + y * R, size, 0, Math.PI * 2); ctx.fill();
      }
      frame++; if (!reduce) raf = requestAnimationFrame(draw);
    };
    draw();
    const onScroll = () => { if (reduce) draw(); };
    addEventListener('scroll', onScroll, { passive: true });
    return () => { cancelAnimationFrame(raf); removeEventListener('scroll', onScroll); };
  }, []);

  return <canvas ref={canvas} aria-hidden="true" className="h-full w-full" />;
};

export const Landing: React.FC<Props> = ({ onPro, onRanked }) => {
  const hero = useRef<HTMLDivElement>(null);
  const [progress, setProgress] = useState(0);
  const [pro, setPro] = useState<{ model: number; elo: number; games: number } | null>(null);
  const [ranked, setRanked] = useState<{ accuracy: number; blue: number; games: number; matches: number } | null>(null);

  useEffect(() => {
    const onScroll = () => {
      const el = hero.current; if (!el) return;
      const total = el.offsetHeight - innerHeight;
      setProgress(total > 0 ? Math.min(1, Math.max(0, -el.getBoundingClientRect().top / total)) : 0);
    };
    onScroll(); addEventListener('scroll', onScroll, { passive: true }); addEventListener('resize', onScroll);
    return () => { removeEventListener('scroll', onScroll); removeEventListener('resize', onScroll); };
  }, []);

  useEffect(() => {
    fetch(`${API_URL}/api/model`).then(r => r.json()).then(d => {
      const h = d.holdout; if (h) setPro({ model: h.model.accuracy, elo: h.elo.accuracy, games: h.model.games });
    }).catch(() => {});
    fetch(`${API_URL}/api/ranked/info`).then(r => r.json()).then(d => {
      const s = d.summary; if (s) setRanked({ accuracy: s.accuracy, blue: s.blue_side_accuracy, games: s.test_games, matches: s.matches });
    }).catch(() => {});
  }, []);

  const stage = Math.min(STAGES.length - 1, Math.floor(progress * STAGES.length));
  const counter = String(Math.round(100 - progress * 100)).padStart(3, '0');
  const pct = (x: number) => `${(x * 100).toFixed(1)}%`;

  return (
    <div className="bg-[#05060a] text-white">
      {/* Top bar */}
      <nav className="fixed inset-x-0 top-0 z-40 flex items-center justify-between px-5 py-4 text-xs font-bold uppercase tracking-[0.2em] mix-blend-difference sm:px-8">
        <span>Nexus Sight</span>
        <span className="flex gap-5">
          <button onClick={onPro} className="hover:text-esport-gold">Pro</button>
          <button onClick={onRanked} className="hover:text-esport-gold">Ranked</button>
          <a href="https://github.com/Zylocope/LOL-game-analyzer" target="_blank" rel="noopener" className="hover:text-esport-gold">GitHub</a>
        </span>
      </nav>

      {/* Hero: sticky wordmark with the morphing object as the gap between the words */}
      <div ref={hero} className="relative h-[260vh]">
        <div className="sticky top-0 flex h-screen flex-col items-center justify-center overflow-hidden px-4">
          <h1 className="flex items-center gap-2 font-display font-bold leading-none tracking-tight sm:gap-4"
              style={{ fontSize: 'clamp(44px, 12vw, 190px)' }}>
            <span>NEXUS</span>
            <span className="inline-block" style={{ width: '1.05em', height: '1.05em' }}><Orb progress={progress} /></span>
            <span>SIGHT</span>
          </h1>
          <p className="mt-6 max-w-xl text-center text-sm text-gray-400 sm:text-base">
            League of Legends draft analysis that tells you how much a draft really matters.
          </p>
          <p className="mt-10 h-5 text-xs font-bold uppercase tracking-[0.3em] text-esport-gold">{STAGES[stage]}</p>
          <span className="absolute bottom-6 font-mono text-xs text-gray-500">{counter}</span>
        </div>
      </div>

      {/* Two modes */}
      <section className="mx-auto max-w-6xl px-4 py-24 sm:px-8">
        <p className="mb-3 text-xs font-bold uppercase tracking-[0.3em] text-gray-500">( Two ways to analyze )</p>
        <div className="grid gap-5 md:grid-cols-2">
          <button onClick={onPro} className="group rounded-3xl border border-gray-800 bg-gray-950 p-7 text-left transition hover:border-esport-gold">
            <span className="text-xs font-bold uppercase tracking-[0.25em] text-esport-gold">Pro</span>
            <h2 className="mt-3 font-display text-3xl font-bold sm:text-4xl">Pro Team Draft Analysis</h2>
            <p className="mt-3 text-gray-400">Pick two pro teams and their draft. Win probability from team strength, players, recent form and the draft, with a warning when a pick is rare or off-role.</p>
            <span className="mt-6 inline-block font-display font-bold tracking-widest text-white group-hover:text-esport-gold">START PRO DRAFT →</span>
          </button>
          <button onClick={onRanked} className="group rounded-3xl border border-gray-800 bg-gray-950 p-7 text-left transition hover:border-esport-gold">
            <span className="text-xs font-bold uppercase tracking-[0.25em] text-esport-gold">Ranked · Experimental</span>
            <h2 className="mt-3 font-display text-3xl font-bold sm:text-4xl">Ranked Draft Analysis</h2>
            <p className="mt-3 text-gray-400">Ten champions, no teams. See how much a draft shifts the odds in Master+ solo queue, and which picks are doing well right now.</p>
            <span className="mt-6 inline-block font-display font-bold tracking-widest text-white group-hover:text-esport-gold">START RANKED DRAFT →</span>
          </button>
        </div>
      </section>

      {/* Numbers */}
      <section className="border-y border-gray-900 bg-black">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-20 sm:px-8 md:grid-cols-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.3em] text-gray-500">( Honest numbers )</p>
            <h2 className="mt-3 font-display text-4xl font-bold">Tested on games it had never seen.</h2>
          </div>
          <div>
            <p className="font-display text-6xl font-bold text-esport-gold">{pro ? pct(pro.model) : '64.7%'}</p>
            <p className="mt-2 text-gray-300">Pro games called right, on {pro ? pro.games.toLocaleString() : '1,970'} games from 2026 sealed before testing.</p>
            <p className="mt-1 text-sm text-gray-500">Team ratings alone: {pro ? pct(pro.elo) : '63.4%'}. In pro play, team strength decides most games.</p>
          </div>
          <div>
            <p className="font-display text-6xl font-bold text-esport-gold">{ranked ? pct(ranked.accuracy) : '53.3%'}</p>
            <p className="mt-2 text-gray-300">Ranked games called right from the draft alone, on the newest {ranked ? ranked.games.toLocaleString() : '4,502'} Master+ games.</p>
            <p className="mt-1 text-sm text-gray-500">Always picking blue side: {ranked ? pct(ranked.blue) : '51.2%'}. Matchmaking evens the teams, so the draft matters only a little.</p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-6xl px-4 py-24 sm:px-8">
        <p className="mb-8 text-xs font-bold uppercase tracking-[0.3em] text-gray-500">( How it works )</p>
        <div className="grid gap-8 md:grid-cols-3">
          {[
            ['01', 'Real results', 'Pro games from 2018 to today (LCK, LPL, LEC, LCS, MSI, Worlds) and recent Master+ ranked games.'],
            ['02', 'Only the past', 'Every rating and statistic is built from games that finished before the one being predicted.'],
            ['03', 'Plain answers', 'A win chance, the reasons behind it, and a warning when the data is too thin to be sure.'],
          ].map(([n, t, d]) => (
            <div key={n}>
              <span className="font-mono text-sm text-esport-gold">{n}</span>
              <h3 className="mt-2 font-display text-2xl font-bold">{t}</h3>
              <p className="mt-2 text-gray-400">{d}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-gray-900 px-4 py-10 text-center text-xs text-gray-500 sm:px-8">
        <p>Built by <a className="text-gray-300 hover:text-esport-gold" href="https://zylocope.github.io" target="_blank" rel="noopener">La Min Oo</a> · <a className="text-gray-300 hover:text-esport-gold" href="https://github.com/Zylocope/LOL-game-analyzer" target="_blank" rel="noopener">Source on GitHub</a></p>
        <p className="mt-2">Pro data: Oracle's Elixir. Ranked data: Riot Games API.</p>
        <p className="mx-auto mt-2 max-w-2xl">Nexus Sight isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.</p>
      </footer>
    </div>
  );
};
