import React, { useState, useEffect } from 'react';
import { Team, Role, Player, MatchContext, AnalysisResult } from './types';
import { DraftBoard } from './components/DraftBoard';
import { AnalysisPanel } from './components/AnalysisPanel';
import { Lobby } from './components/Lobby';
import { PRESET_TEAMS, PresetTeam } from './data/teams';
import { fetchTeamData, analyzeMatchup, fetchChampionStats } from './services/geminiService';
import { collectTeamAdvancedStats, collectPlayerAdvancedStats } from './services/dataCollector';
import { RefreshCw, Play, Search, Zap, LogOut } from 'lucide-react';

// Initial state helpers
const createEmptyTeam = (id: 'blue' | 'red'): Team => ({
  id,
  name: id === 'blue' ? 'Blue Team' : 'Red Team',
  bans: ['', '', '', '', ''],
  players: [
    { name: 'Top Laner', role: 'Top' },
    { name: 'Jungler', role: 'Jungle' },
    { name: 'Mid Laner', role: 'Mid' },
    { name: 'Bot Laner', role: 'Bot' },
    { name: 'Support', role: 'Support' }
  ]
});

// Helper to simulate fetching player specific data (Tilt, Mastery) since we don't have a backend
const getSimulatedPlayerData = (champion: string, role: string, playerName: string) => {
  const forms: Array<'Hot' | 'Stable' | 'Cold'> = ['Hot', 'Hot', 'Stable', 'Stable', 'Stable', 'Cold'];
  const form = forms[Math.floor(Math.random() * forms.length)];
  const games = Math.floor(Math.random() * 50) + 1; // 1 to 50 games this season
  const isComfort = games > 30 || Math.random() > 0.8;
  
  // Use the new Data Collector for advanced metrics
  const advanced = collectPlayerAdvancedStats(playerName, role);

  return {
    recentForm: form,
    gamesOnChamp: games,
    isComfortPick: isComfort,
    advancedStats: advanced
  };
};

export default function App() {
  const [view, setView] = useState<'lobby' | 'analyzer'>('lobby');
  const [blueTeam, setBlueTeam] = useState<Team>(createEmptyTeam('blue'));
  const [redTeam, setRedTeam] = useState<Team>(createEmptyTeam('red'));
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  
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

  // Handler to start match from Lobby
  const handleStartMatch = async (blue: PresetTeam, red: PresetTeam) => {
    // Initialize Blue Team
    setBlueTeam({
      id: 'blue',
      name: blue.name,
      bans: ['', '', '', '', ''],
      players: blue.players.map(p => ({
        role: p.role,
        name: p.name,
        // We can optionally pre-load advanced player stats here if needed, but usually we wait for champ select
        advancedStats: collectPlayerAdvancedStats(p.name, p.role)
      })),
      advancedStats: collectTeamAdvancedStats(blue.name)
    });

    // Initialize Red Team
    setRedTeam({
      id: 'red',
      name: red.name,
      bans: ['', '', '', '', ''],
      players: red.players.map(p => ({
        role: p.role,
        name: p.name,
        advancedStats: collectPlayerAdvancedStats(p.name, p.role)
      })),
      advancedStats: collectTeamAdvancedStats(red.name)
    });

    // Fetch team stats in background
    fetchTeamData(blue.name).then(stats => setBlueTeam(prev => ({...prev, stats})));
    fetchTeamData(red.name).then(stats => setRedTeam(prev => ({...prev, stats})));

    setView('analyzer');
  };

  const handleUpdatePlayer = (side: 'blue' | 'red', role: Role, champion: string) => {
    const setter = side === 'blue' ? setBlueTeam : setRedTeam;
    setter(prev => ({
      ...prev,
      // Clear championStats when champion name changes to avoid stale data
      players: prev.players.map(p => p.role === role ? { ...p, champion, championStats: undefined } : p)
    }));
  };

  // Smart Manual Mode: Handle player name updates (Substitutions)
  const handleUpdatePlayerName = (side: 'blue' | 'red', role: Role, name: string) => {
    const setter = side === 'blue' ? setBlueTeam : setRedTeam;
    setter(prev => ({
      ...prev,
      players: prev.players.map(p => p.role === role ? { 
        ...p, 
        name: name,
        // Refresh advanced stats for the new player (mock)
        advancedStats: collectPlayerAdvancedStats(name, role)
      } : p)
    }));
  };

  const handleFetchChampionStats = async (side: 'blue' | 'red', role: Role, champion: string) => {
    if (!champion) return;
    try {
       // 1. Fetch generic champion meta stats
       const stats = await fetchChampionStats(champion, role);
       
       const team = side === 'blue' ? blueTeam : redTeam;
       const player = team.players.find(p => p.role === role);
       
       // 2. Simulate "Live" Player data (e.g. from a DB)
       const playerData = getSimulatedPlayerData(champion, role, player?.name || "Player");

       const setter = side === 'blue' ? setBlueTeam : setRedTeam;
       setter(prev => ({
         ...prev,
         players: prev.players.map(p => p.role === role ? { 
           ...p, 
           championStats: stats,
           ...playerData // Merge the simulated player-specific data
         } : p)
       }));
    } catch (e) {
      console.error("Failed to fetch champion stats", e);
    }
  };

  const handleUpdateBan = (side: 'blue' | 'red', index: number, champion: string) => {
    const setter = side === 'blue' ? setBlueTeam : setRedTeam;
    setter(prev => {
      const newBans = [...prev.bans];
      newBans[index] = champion;
      return { ...prev, bans: newBans };
    });
  };

  const handleUpdateName = (side: 'blue' | 'red', name: string) => {
    const setter = side === 'blue' ? setBlueTeam : setRedTeam;
    setter(prev => ({ ...prev, name }));
  };

  const fetchStats = async (side: 'blue' | 'red') => {
    const team = side === 'blue' ? blueTeam : redTeam;
    const setFetching = side === 'blue' ? setIsFetchingBlue : setIsFetchingRed;
    const setTeam = side === 'blue' ? setBlueTeam : setRedTeam;

    if (!team.name) return;

    setFetching(true);
    try {
      // 1. Fetch generic team data (AI)
      const stats = await fetchTeamData(team.name);
      
      // 2. Collect Advanced Metrics (DataCollector)
      const advancedStats = collectTeamAdvancedStats(team.name);
      
      setTeam(prev => ({ ...prev, stats, advancedStats }));
    } catch (e) {
      console.error(e);
    } finally {
      setFetching(false);
    }
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    const context: MatchContext = { blueTeam, redTeam };
    try {
      const result = await analyzeMatchup(context);
      setAnalysis(result);
    } catch (e) {
      console.error(e);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-esport-dark text-gray-200 font-sans selection:bg-esport-gold/30 flex flex-col">
      
      {/* Navbar */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setView('lobby')}>
            <Zap className="text-esport-gold animate-pulse" />
            <h1 className="text-2xl font-display font-bold text-white tracking-widest">
              NEXUS<span className="text-esport-gold">SIGHT</span>
            </h1>
          </div>
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

      {view === 'lobby' ? (
        <Lobby onStartMatch={handleStartMatch} />
      ) : (
        <main className="max-w-7xl mx-auto px-4 py-8 flex-1">
          
          {/* Action Bar */}
          <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
             <div className="flex gap-2">
                <span className="bg-gray-800 border border-gray-700 text-gray-400 px-3 py-1 rounded text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                   Manual Draft Mode
                </span>
             </div>
             
             <div className="flex gap-3">
               <button 
                  onClick={() => fetchStats('blue')}
                  disabled={isFetchingBlue || !blueTeam.name}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-semibold transition-all border border-gray-700 disabled:opacity-50"
               >
                  <Search size={16} />
                  {isFetchingBlue ? 'Scanning Blue...' : 'Fetch Blue Stats'}
               </button>
               <button 
                  onClick={() => fetchStats('red')}
                  disabled={isFetchingRed || !redTeam.name}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-semibold transition-all border border-gray-700 disabled:opacity-50"
               >
                  <Search size={16} />
                  {isFetchingRed ? 'Scanning Red...' : 'Fetch Red Stats'}
               </button>
             </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Draft Column */}
            <div className="lg:col-span-7 space-y-6">
              <DraftBoard 
                team={blueTeam} 
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
                disabled={isAnalyzing}
                className="w-full mt-4 bg-esport-gold hover:bg-yellow-500 text-black font-bold py-4 rounded-xl shadow-lg shadow-yellow-900/20 transition-all flex items-center justify-center gap-3 text-lg uppercase tracking-wider"
              >
                {isAnalyzing ? <RefreshCw className="animate-spin" /> : <Play fill="currentColor" />}
                {isAnalyzing ? 'Processing Match Data...' : 'Run Prediction'}
              </button>
            </div>

            {/* Analysis Column */}
            <div className="lg:col-span-5">
              <div className="sticky top-24">
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
      <footer className="border-t border-gray-800 mt-auto py-8 text-center text-gray-600 text-sm">
        <p>Nexus Sight AI • Powered by Gemini • Not affiliated with Riot Games</p>
      </footer>
    </div>
  );
}