import { ModelStatus } from "./components/ModelStatus";
import React, { useState, useEffect, useRef } from 'react';
import { Team, Role, Player, MatchContext, AnalysisResult } from './types';
import { DraftBoard } from './components/DraftBoard';
import { AnalysisPanel } from './components/AnalysisPanel';
import { Lobby } from './components/Lobby';
import { Landing } from './components/Landing';
import { RankedDraft } from './components/RankedDraft';
import { PRESET_TEAMS, PresetTeam } from './data/teams';
import { fetchTeamData, analyzeMatchup, fetchChampionStats, fetchRealPlayerStats } from './services/analysisService';
import { RefreshCw, Play, Search, Zap, LogOut } from 'lucide-react';

// Initial state helpers
const createEmptyTeam = (id: 'blue' | 'red'): Team => ({
  id,
  name: id === 'blue' ? 'T1' : 'Gen.G', // Default to real team names
  bans: ['', '', '', '', ''],
  players: id === 'blue' ? [
    { name: 'Zeus', role: 'Top' },   // Real Player
    { name: 'Oner', role: 'Jungle' },
    { name: 'Faker', role: 'Mid' },
    { name: 'Gumayusi', role: 'Bot' },
    { name: 'Keria', role: 'Support' }
  ] : [
    { name: 'Kiin', role: 'Top' },   // Real Player
    { name: 'Canyon', role: 'Jungle' },
    { name: 'Chovy', role: 'Mid' },
    { name: 'Peyz', role: 'Bot' },
    { name: 'Lehends', role: 'Support' }
  ]
});

export default function App() {
  const matchVersion = useRef(0);
  const predictionVersion = useRef(0);
  type View = 'home' | 'lobby' | 'analyzer' | 'ranked';
  const viewFromHash = (): View => (location.hash === '#/pro' ? 'lobby' : location.hash === '#/ranked' ? 'ranked' : 'home');
  const [view, setViewState] = useState<View>(viewFromHash);
  const setView = (next: View) => {
    setViewState(next);
    const hash = next === 'home' ? '' : next === 'ranked' ? '#/ranked' : '#/pro';
    if (location.hash !== hash) history.pushState(null, '', hash || location.pathname);
    window.scrollTo(0, 0);
  };
  useEffect(() => {
    const onPop = () => setViewState(v => {
      const next = viewFromHash();
      return v === 'analyzer' && next === 'lobby' ? v : next;
    });
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);
  const [blueTeam, setBlueTeam] = useState<Team>(createEmptyTeam('blue'));
  const [redTeam, setRedTeam] = useState<Team>(createEmptyTeam('red'));
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  const [patch, setPatch] = useState('');
  const [analysisError, setAnalysisError] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isFetchingBlue, setIsFetchingBlue] = useState(false);
  const [isFetchingRed, setIsFetchingRed] = useState(false);

  // Calculate unavailable champions (picks + bans from both teams)
  const unavailableChampions = new Set([
    ...blueTeam.players.map(p => p.champion).filter((c): c is string => !!c),
    ...redTeam.players.map(p => p.champion).filter((c): c is string => !!c),
    ...blueTeam.bans.filter((c): c is string => !!c),
    ...redTeam.bans.filter((c): c is string => !!c)
  ]);

const handleStartMatch = async (blue: PresetTeam, red: PresetTeam) => {
    const version = ++matchVersion.current;
    setAnalysis(null);
    console.log("BLUE TEAM DATA:", blue);
    console.log("Players List:", blue.players);
    // 1. Smart Roster Helper: Keeps real names if they exist!
    const getRoster = (teamData: PresetTeam) => {
      // If the preset has specific players (like T1), USE THEM.
      if (teamData.players && teamData.players.length > 0) {
        return teamData.players.map(p => ({ ...p })); // Copy them
      }
      // Only use generics if the team is blank
      return [
        { role: 'Top', name: 'Top Laner' },
        { role: 'Jungle', name: 'Jungler' },
        { role: 'Mid', name: 'Mid Laner' },
        { role: 'Bot', name: 'Bot Laner' },
        { role: 'Support', name: 'Support' }
      ] as Player[];
    };

    // 2. Initialize Blue Team (T1) -> Now keeps "Zeus", "Faker"...
    setBlueTeam({
      id: 'blue',
      name: blue.name,
      bans: ['', '', '', '', ''],
      players: getRoster(blue),
      advancedStats: undefined
    });

    // 3. Initialize Red Team (Gen.G) -> Now keeps "Kiin", "Chovy"...
    setRedTeam({
      id: 'red',
      name: red.name,
      bans: ['', '', '', '', ''],
      players: getRoster(red),
      advancedStats: undefined
    });

    // Fetch team stats in background
    fetchTeamData(blue.name).then(stats => {
      if (version !== matchVersion.current) return;
      setBlueTeam(prev => ({
        ...prev,
        stats,
        // Auto-fill roster from DB if available
        players: (stats as any).roster && (stats as any).roster.length === 5
          ? prev.players.map(p => ({ ...p, name: (stats as any).roster.find((r: any) => r.role === p.role)?.name || p.name, championStats: undefined }))
          : prev.players
      }));
    });

    fetchTeamData(red.name).then(stats => {
      if (version !== matchVersion.current) return;
      setRedTeam(prev => ({
        ...prev,
        stats,
        // Auto-fill roster from DB if available
        players: (stats as any).roster && (stats as any).roster.length === 5
          ? prev.players.map(p => ({ ...p, name: (stats as any).roster.find((r: any) => r.role === p.role)?.name || p.name, championStats: undefined }))
          : prev.players
      }));
    });

    setView('analyzer');
  };

  const handleUpdatePlayer = (side: 'blue' | 'red', role: Role, champion: string) => {
    setAnalysis(null);
    const setter = side === 'blue' ? setBlueTeam : setRedTeam;
    setter(prev => ({
      ...prev,
      // Clear championStats when champion name changes to avoid stale data
      players: prev.players.map(p => p.role === role ? { ...p, champion, championStats: undefined } : p)
    }));
  };

  // Smart Manual Mode: Handle player name updates (Substitutions)
  const handleUpdatePlayerName = (side: 'blue' | 'red', role: Role, name: string) => {
    setAnalysis(null);
    const setter = side === 'blue' ? setBlueTeam : setRedTeam;
    setter(prev => ({
      ...prev,
      players: prev.players.map(p => p.role === role ? {
        ...p,
        name: name,
        championStats: undefined,
        gamesOnChamp: undefined,
        isComfortPick: false,
        // Refresh advanced stats for the new player (mock)
        advancedStats: undefined
      } : p)
    }));
  };

const handleFetchChampionStats = async (side: 'blue' | 'red', role: Role, champion: string) => {
    if (!champion) return;
    const version = matchVersion.current;
    const requestedName = (side === 'blue' ? blueTeam : redTeam).players.find(p => p.role === role)?.name;
    try {
        // 1. Get Generic Info (Meta Tier) from AI
        // We use this as a "Baseline" object to fill in gaps (like metaTier)
        const aiStats = await fetchChampionStats(champion, role);

        const team = side === 'blue' ? blueTeam : redTeam;
        const player = team.players.find(p => p.role === role);
        const playerName = player?.name || "Unknown";

        // 2. Try to get REAL Stats from Python DB
        // Returns null if player has never played this champ in our DB
        const realStats = await fetchRealPlayerStats(playerName, champion, role);

        // 3. Fallback to simulation/AI


        // --- LOGIC FIX START ---

        // A. Construct the final "Badge" stats
        // If we have real stats, we OVERWRITE the AI's generic winrate with the player's real winrate
        const finalChampionStats = realStats ? {
            ...aiStats, // Keep generic/meta info
            winRate: realStats.winRate,
            gamesPlayed: realStats.gamesPlayed,
            roleEffectiveness: realStats.roleEffectiveness,
            source: realStats.source ?? 'pro',
        } : {
            ...aiStats,
            source: aiStats.source,
        };

        // B. Determine Game Count for the UI logic
        const finalGames = realStats ? realStats.gamesPlayed : undefined;

        // C. Determine if it's a "Comfort Pick"
        const isComfort = realStats?.source === 'player' && realStats.gamesPlayed >= 5;

        // --- LOGIC FIX END ---

        const setter = side === 'blue' ? setBlueTeam : setRedTeam;
        setter(prev => ({
          ...prev,
          players: prev.players.map(p => p.role === role && p.champion === champion && p.name === requestedName && version === matchVersion.current ? {
            ...p,
            championStats: finalChampionStats, // <--- Use the merged stats here
            recentForm: undefined,
            gamesOnChamp: finalGames,
            isComfortPick: isComfort,
            // If we have real stats, we likely don't have "advancedStats" (aggro/gold) for that specific player/champ pair yet,
            // so we keep the simulated advanced stats for the graphs, OR you can extend the backend to provide this too.
            advancedStats: undefined
          } : p)
        }));
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  };

  const handleUpdateBan = (side: 'blue' | 'red', index: number, champion: string) => {
    setAnalysis(null);
    const setter = side === 'blue' ? setBlueTeam : setRedTeam;
    setter(prev => {
      const newBans = [...prev.bans];
      newBans[index] = champion;
      return { ...prev, bans: newBans };
    });
  };

  const handleUpdateName = (side: 'blue' | 'red', name: string) => {
    setAnalysis(null);
    const setter = side === 'blue' ? setBlueTeam : setRedTeam;
    setter(prev => ({ ...prev, name }));
  };

  const fetchStats = async (side: 'blue' | 'red') => {
    const team = side === 'blue' ? blueTeam : redTeam;
    const setFetching = side === 'blue' ? setIsFetchingBlue : setIsFetchingRed;
    const setTeam = side === 'blue' ? setBlueTeam : setRedTeam;
    const version = matchVersion.current;

    if (!team.name) return;

    setFetching(true);
    try {
      // 1. Fetch generic team data (AI)
      const stats = await fetchTeamData(team.name);

      // 2. Collect Advanced Metrics (DataCollector)
      const advancedStats = undefined;

      if (version === matchVersion.current) setTeam(prev => prev.name === team.name ? ({ ...prev, stats, advancedStats }) : prev);
    } catch (e) {
      console.error(e);
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => { predictionVersion.current++; setAnalysis(null); setAnalysisError(''); }, [blueTeam, redTeam, patch]);

  const handleAnalyze = async () => {
    if ([...blueTeam.players, ...redTeam.players].some(p => !p.champion)) return;
    const version = matchVersion.current;
    setIsAnalyzing(true);
    setAnalysisError('');
    const predictionId = ++predictionVersion.current;
    const context: MatchContext = { blueTeam, redTeam, patch };
    try {
      const result = await analyzeMatchup(context);
      if (version === matchVersion.current && predictionId === predictionVersion.current) setAnalysis(result);
    } catch (e) {
      if (version === matchVersion.current && predictionId === predictionVersion.current) setAnalysisError(e instanceof Error ? e.message : "Prediction unavailable");
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (view === 'home') {
    return <Landing onPro={() => setView('lobby')} onRanked={() => setView('ranked')} />;
  }

  return (
    <div className="min-h-screen bg-esport-dark text-gray-200 font-sans selection:bg-esport-gold/30 flex flex-col">

      {/* Navbar */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setView('home')}>
            <Zap className="text-esport-gold animate-pulse" />
            <h1 className="text-2xl font-display font-bold text-white tracking-widest">
              NEXUS<span className="text-esport-gold">SIGHT</span>
            </h1>
          </div>
          {view === 'ranked' && (
            <button onClick={() => setView('lobby')} className="text-xs font-bold uppercase tracking-widest text-gray-500 hover:text-white">
              Pro mode
            </button>
          )}
          {view === 'lobby' && (
            <button onClick={() => setView('ranked')} className="text-xs font-bold uppercase tracking-widest text-gray-500 hover:text-white">
              Ranked mode
            </button>
          )}
          {view === 'analyzer' && (
            <button
              onClick={() => setView('lobby')}
              className="flex items-center gap-2 text-xs text-gray-500 hover:text-white transition-colors"
            >
              <LogOut size={12} /> EXIT MATCH
            </button>
          )}
        </div>
      </header>

      {view === 'ranked' ? (
        <RankedDraft />
      ) : view === 'lobby' ? (
        <Lobby onStartMatch={handleStartMatch} />
      ) : (
        <main className="max-w-7xl mx-auto px-4 py-8 flex-1">

          <ModelStatus />
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

            <div className="lg:col-span-7 space-y-6">
              <DraftBoard
                team={blueTeam}
                enemyTeam={redTeam} // <--- ADD THIS LINE
                side="blue"
                onUpdatePlayer={handleUpdatePlayer}
                onUpdateBan={handleUpdateBan}
                onUpdateName={handleUpdateName}
                onUpdatePlayerName={handleUpdatePlayerName}
                onFetchChampionStats={handleFetchChampionStats}
                loading={isFetchingBlue}
                unavailableChampions={unavailableChampions}
              />

              <div className="flex items-center justify-center py-2">
                 <span className="text-gray-600 font-display font-bold text-2xl tracking-widest">VS</span>
              </div>

              <DraftBoard
                team={redTeam}
                enemyTeam={blueTeam} // <--- ADD THIS LINE
                side="red"
                onUpdatePlayer={handleUpdatePlayer}
                onUpdateBan={handleUpdateBan}
                onUpdateName={handleUpdateName}
                onUpdatePlayerName={handleUpdatePlayerName}
                onFetchChampionStats={handleFetchChampionStats}
                loading={isFetchingRed}
                unavailableChampions={unavailableChampions}
              />

              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing || [...blueTeam.players, ...redTeam.players].some(p => !p.champion)}
                className="w-full mt-4 bg-esport-gold hover:bg-yellow-500 text-black font-bold py-4 rounded-xl shadow-lg shadow-yellow-900/20 transition-all flex items-center justify-center gap-3 text-lg uppercase tracking-wider disabled:cursor-not-allowed disabled:bg-gray-800 disabled:text-gray-500 disabled:shadow-none"
              >
                {isAnalyzing ? <RefreshCw className="animate-spin" /> : <Play fill="currentColor" />}
                {isAnalyzing ? 'Predicting...' : 'Run Prediction'}
              </button>
              {!isAnalyzing && [...blueTeam.players, ...redTeam.players].some(p => !p.champion) && (
                <p className="mt-2 text-center text-sm text-gray-500">
                  Pick all 10 champions to run the prediction ({10 - [...blueTeam.players, ...redTeam.players].filter(p => p.champion).length} left).
                </p>
              )}
            </div>

            {/* Analysis Column */}
            <div className="lg:col-span-5">
              <div className="sticky top-24">
                {analysisError && <p role="alert" className="mb-4 rounded-lg border border-red-800 bg-red-950/30 p-4 text-red-300">{analysisError}</p>}
                <AnalysisPanel
                  analysis={analysis}
                  loading={isAnalyzing}
                  blueName={blueTeam.name}
                  redName={redTeam.name}
                />
              </div>
            </div>
          </div>
        </main>
      )}

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-900 py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center text-xs text-gray-600">
          <div className="flex items-center gap-2 mb-4 md:mb-0">
            <Zap size={14} className="text-gray-700" />
            <span>NEXUS SIGHT</span>
          </div>
          <div className="flex gap-6">
            <a href="https://github.com/Zylocope/LOL-game-analyzer/blob/main/docs/MODEL_CARD.md" target="_blank" rel="noopener" className="hover:text-esport-gold transition-colors">How it works</a>
            <a href="https://github.com/Zylocope/LOL-game-analyzer" target="_blank" rel="noopener" className="hover:text-esport-gold transition-colors">GitHub</a>
            <a href="https://zylocope.github.io" target="_blank" rel="noopener" className="hover:text-esport-gold transition-colors">About the author</a>
          </div>
          <div className="mt-4 md:mt-0 opacity-50">
            Not endorsed by Riot Games. Pro data: Oracle's Elixir.
          </div>
        </div>
      </footer>
    </div>
  );
}
