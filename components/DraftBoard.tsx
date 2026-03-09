import React, { useState } from 'react';
import { Team, Role } from '../types';
import { Swords, Ban } from 'lucide-react';
import { ChampionSelectModal } from './ChampionSelectModal';
import { analyzeComposition } from '../src/compositionAnalysis'; // Verify this path matches your folder structure
import { useMatchups } from '../src/hooks/useMatchups';
import { TeamLogo } from './TeamLogo';
import { CHAMPION_DATA } from '../data/championTags';

interface DraftBoardProps {
  team: Team;
  enemyTeam?: Team; // <--- This allows the board to see the enemy
  side: 'blue' | 'red';
  onUpdatePlayer: (side: 'blue' | 'red', role: Role, champion: string) => void;
  onUpdateBan: (side: 'blue' | 'red', index: number, champion: string) => void;
  onUpdateName: (side: 'blue' | 'red', name: string) => void;
  onUpdatePlayerName: (side: 'blue' | 'red', role: Role, name: string) => void;
  onFetchChampionStats: (side: 'blue' | 'red', role: Role, champion: string) => void;
  loading: boolean;
  unavailableChampions: Set<string>;
}

export const DraftBoard: React.FC<DraftBoardProps> = ({ 
  team, 
  enemyTeam, 
  side, 
  onUpdatePlayer, 
  onUpdateBan, 
  onUpdateName, 
  onUpdatePlayerName, 
  onFetchChampionStats, 
  loading, 
  unavailableChampions 
}) => {
  const isBlue = side === 'blue';
  const borderColor = isBlue ? 'border-esport-blue' : 'border-esport-red';
  const textColor = isBlue ? 'text-esport-blue' : 'text-esport-red';
  const bgColor = isBlue ? 'bg-blue-950/20' : 'bg-red-950/20';

  // 1. USE THE HOOK (Replaces the manual code)
  const matchups = useMatchups(team, enemyTeam);

  // MODAL STATE
  const [modalOpen, setModalOpen] = useState(false);
  const [activeSlot, setActiveSlot] = useState<{role: Role, isBan: boolean, banIndex?: number} | null>(null);

  // Helper for Local Icons
  const getIconUrl = (name: string) => {
    if (!name) return '';
    let cleanName = name.replace(/[^a-zA-Z0-9]/g, '');
    const exceptions: Record<string, string> = {
        "Wukong": "MonkeyKing", "Renata Glasc": "Renata", "Bel'Veth": "Belveth",
        "Kai'Sa": "Kaisa", "Kha'Zix": "Khazix", "Vel'Koz": "Velkoz", "Cho'Gath": "Chogath",
        "Kog'Maw": "KogMaw", "Rek'Sai": "RekSai", "LeBlanc": "Leblanc", "Dr. Mundo": "DrMundo",
        "Tahm Kench": "TahmKench", "Twisted Fate": "TwistedFate", "Lee Sin": "LeeSin",
        "Xin Zhao": "XinZhao", "Master Yi": "MasterYi", "Jarvan IV": "JarvanIV",
        "Aurelion Sol": "AurelionSol", "Miss Fortune": "MissFortune"
    };
    if (exceptions[name]) return `/champions/${exceptions[name]}.png`;
    cleanName = cleanName.charAt(0).toUpperCase() + cleanName.slice(1);
    return `/champions/${cleanName}.png`;
  };

  const openSelect = (role: Role, isBan: boolean = false, banIndex?: number) => {
    setActiveSlot({ role, isBan, banIndex });
    setModalOpen(true);
  };

  const handleSelect = (champ: string) => {
    if (!activeSlot) return;
    if (activeSlot.isBan && typeof activeSlot.banIndex === 'number') {
      onUpdateBan(side, activeSlot.banIndex, champ);
    } else {
      onUpdatePlayer(side, activeSlot.role, champ);
      onFetchChampionStats(side, activeSlot.role, champ);
    }
  };

  return (
    <div className={`h-fit flex flex-col ${bgColor} border-t-4 ${borderColor} rounded-b-xl relative overflow-hidden shadow-2xl`}>
      <ChampionSelectModal 
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSelect={handleSelect}
        unavailableChampions={unavailableChampions}
      />

      {/* Header - Improved Layout */}
      <div className="p-4 border-b border-gray-800/50 flex flex-col gap-3 bg-gray-900/40">
        <div className="flex justify-between items-start">
            {/* Team Identity */}
            <div className="flex items-center gap-4 flex-1">
                <div className="w-16 h-16 bg-gray-950/40 p-2 rounded-xl border border-gray-800/50 shrink-0 shadow-lg relative overflow-hidden group">
                    <div className={`absolute inset-0 opacity-20 ${isBlue ? 'bg-blue-500' : 'bg-red-500'}`} />
                    <TeamLogo team={{ id: team.id || 'unknown', name: team.name }} className="w-full h-full object-contain relative z-10" />
                </div>
                <div className="flex flex-col flex-1 min-w-0">
                    <span className={`text-[10px] font-bold tracking-[0.2em] uppercase ${textColor} mb-0.5`}>
                        {side} Side
                    </span>
                    <input 
                        value={team.name}
                        onChange={(e) => onUpdateName(side, e.target.value)}
                        className={`bg-transparent text-3xl font-display font-black uppercase tracking-tight text-white w-full focus:outline-none focus:bg-gray-800/50 rounded -ml-1 px-1 transition-colors truncate placeholder-gray-700`}
                        placeholder="TEAM NAME"
                    />
                </div>
            </div>

            {/* Bans - Top Right */}
            <div className="flex gap-1.5 pt-1">
                {team.bans.map((ban, idx) => (
                    <button
                    key={idx}
                    onClick={() => openSelect('Top', true, idx)}
                    className="w-9 h-9 bg-black/60 border border-gray-700/80 rounded-lg flex items-center justify-center hover:border-gray-500 hover:bg-gray-800 transition-all overflow-hidden group relative"
                    title={`Ban ${idx + 1}`}
                    >
                    {ban ? (
                        <>
                            <img src={getIconUrl(ban)} className="w-full h-full object-cover opacity-70 grayscale group-hover:grayscale-0 transition-all" />
                            <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-transparent">
                                <Ban className="text-red-500/80 w-5 h-5 drop-shadow-md" />
                            </div>
                        </>
                    ) : (
                        <Ban size={14} className="text-gray-700 group-hover:text-gray-500" />
                    )}
                    </button>
                ))}
            </div>
        </div>
      </div>

      {/* Players List */}
      <div className="p-2 space-y-2 overflow-y-auto custom-scrollbar min-h-0">
        {team.players.map((player, idx) => (
          <div key={idx} className="relative group bg-gray-900/40 border border-gray-800 rounded-lg p-2 flex items-center gap-3 hover:bg-gray-800/60 transition-all">
             
            <div className="w-6 flex justify-center">
               <span className="text-[10px] font-bold text-gray-500 uppercase -rotate-90 w-12 text-center">{player.role}</span>
            </div>

            <button 
              onClick={() => openSelect(player.role)}
              className={`relative w-14 h-14 bg-gray-950 rounded-lg overflow-hidden border border-gray-700 
                hover:border-esport-gold hover:shadow-[0_0_15px_rgba(200,170,110,0.3)] transition-all shrink-0
                ${player.champion ? 'ring-2 ring-black' : ''}`}
            >
              {player.champion ? (
                <img src={getIconUrl(player.champion)} alt={player.champion} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-700">
                  <Swords size={18} />
                </div>
              )}
            </button>

            {/* Inputs & Stats */}
            <div className="flex-1 min-w-0 flex flex-col justify-center relative">
               
               {/* --- 1. LANE MATCHUP STRIP (Direct Opponent Only) --- */}
               {matchups[player.role]?.lane && (
                  <div 
                    className={`absolute -left-3 top-0 bottom-0 my-auto h-8 w-1 rounded-r shadow-[0_0_8px_rgba(0,0,0,0.5)]
                      ${matchups[player.role].lane.isGood 
                        ? 'bg-green-500 shadow-[0_0_10px_lime]' 
                        : matchups[player.role].lane.isCounter 
                            ? 'bg-red-500 shadow-[0_0_10px_red]'
                            : 'bg-gray-500 opacity-20'}`
                    }
                    title={matchups[player.role].lane.isGood 
                        ? `Counters Lane Opponent (${matchups[player.role].lane.winRate}% WR)` 
                        : `Countered by Lane Opponent (${matchups[player.role].lane.winRate}% WR)`
                    }
                  />
               )}

               {/* --- 2. GLOBAL THREAT ALERT (3+ Counters) --- */}
               {matchups[player.role]?.globalThreats && matchups[player.role].globalThreats.length >= 3 && (
                   <div className="absolute -right-1 -top-3 z-20 flex flex-col items-end">
                       <div 
                         className="bg-red-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow-lg border border-red-400 animate-pulse mb-0.5"
                       >
                         !
                       </div>
                       <div className="bg-black/90 text-red-400 text-[9px] px-1.5 py-0.5 rounded border border-red-900/50 whitespace-nowrap shadow-xl">
                          ⚠️ Countered by: {matchups[player.role].globalThreats.join(', ')}
                       </div>
                   </div>
               )}

               <input 
                 value={player.name}
                 onChange={(e) => onUpdatePlayerName(side, player.role, e.target.value)}
                 className="bg-transparent text-sm font-bold text-gray-200 w-full focus:outline-none focus:text-esport-gold placeholder-gray-600 mb-0.5"
                 placeholder="Player Name"
               />
               <div className="text-xs text-esport-gold/80 font-medium truncate">
                 {player.champion || "Select Champion"}
               </div>
               
               {player.champion && player.championStats && (() => {
                  const meta = CHAMPION_DATA[player.champion as keyof typeof CHAMPION_DATA];
                  const laneKey = player.role.toLowerCase() as 'top' | 'jungle' | 'mid' | 'bot' | 'support';
                  const validRoles = meta?.roles ?? [];
                  const isValidRole = validRoles.includes(laneKey);

                  // OFF-ROLE: do not show winrate badge at all, just a warning
                  if (!isValidRole && meta) {
                    return (
                      <div className="flex items-center gap-2 mt-1 w-full overflow-hidden">
                        <span className="text-[10px] px-1.5 py-0.5 rounded border font-bold whitespace-nowrap shrink-0 bg-red-900/60 text-red-200 border-red-700">
                          OFF-ROLE
                        </span>
                        <span className="text-[10px] text-gray-500 flex items-center gap-1 flex-1 min-w-0">
                          <span className="shrink-0 opacity-50">◎</span>
                          <span className="truncate w-full text-red-300">
                            Not a standard {laneKey} pick in pro play
                          </span>
                        </span>
                      </div>
                    );
                  }

                  // Default: keep global 50% prior behaviour, but annotate "never played" when applicable
                  const hasRealGames = player.championStats.gamesPlayed && player.championStats.gamesPlayed > 0;
                  const winRateValue = parseInt(player.championStats.winRate);
                  const source = player.championStats.source || 'ai';

                  let secondaryText: string;
                  const proPickRate = meta?.stats?.proPickRate ?? null;

                  // If truly no pro data anywhere, surface that explicitly (only when not using player/pro sources)
                  if (
                    proPickRate === 0 &&
                    (!player.championStats.gamesPlayed ||
                      (source !== 'player' && source !== 'pro'))
                  ) {
                    secondaryText = 'Never played in pro matches (last 7 years)';
                  } else {
                    if (source === 'player') {
                      // Only favourites can be called "Main"
                      if (player.championStats.gamesPlayed && player.championStats.gamesPlayed > 5) {
                        secondaryText = 'Main';
                      } else {
                        secondaryText = player.championStats.roleEffectiveness || 'Favourite pick';
                      }
                    } else if (source === 'pro') {
                      secondaryText = 'Pro (7-year aggregate)';
                    } else if (source === 'global') {
                      secondaryText = 'Global win rate';
                    } else {
                      secondaryText = player.championStats.roleEffectiveness || 'Unknown';
                    }
                  }

                  // Color + label based on source type
                  let badgeClass = '';
                  let badgeLabelSuffix = '';
                  if (source === 'player') {
                    badgeClass = winRateValue >= 50
                      ? 'bg-yellow-900/60 text-yellow-200 border-yellow-500/60'
                      : 'bg-yellow-950/40 text-yellow-300 border-yellow-800';
                    badgeLabelSuffix = ' Fav';
                  } else if (source === 'pro') {
                    badgeClass = winRateValue >= 50
                      ? 'bg-blue-900/60 text-blue-200 border-blue-500/60'
                      : 'bg-blue-950/40 text-blue-300 border-blue-800';
                    badgeLabelSuffix = ' Pro';
                  } else if (source === 'global') {
                    badgeClass = winRateValue >= 50
                      ? 'bg-green-900/50 text-green-200 border-green-500/60'
                      : 'bg-green-950/40 text-green-300 border-green-800';
                    badgeLabelSuffix = ' Global';
                  } else {
                    badgeClass = winRateValue >= 50
                      ? 'bg-gray-800 text-gray-200 border-gray-600'
                      : 'bg-gray-900 text-gray-300 border-gray-700';
                    badgeLabelSuffix = '';
                  }

                  return (
                    <div className="flex items-center gap-2 mt-1 w-full overflow-hidden">
                      {hasRealGames ? (
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded border font-bold whitespace-nowrap shrink-0 ${badgeClass}`}
                        >
                          {player.championStats.winRate} ({player.championStats.gamesPlayed}G){badgeLabelSuffix}
                        </span>
                      ) : (
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded whitespace-nowrap shrink-0 font-bold ${
                            winRateValue > 50 ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                          }`}
                        >
                          {player.championStats.winRate} Global
                        </span>
                      )}
                      <span className="text-[10px] text-gray-500 flex items-center gap-1 flex-1 min-w-0">
                        <span className="shrink-0 opacity-50">◎</span>
                        <span className="truncate w-full text-gray-400">
                          {secondaryText === 'Main' ? (
                            <span className="text-esport-gold font-bold">Main</span>
                          ) : (
                            secondaryText
                          )}
                        </span>
                      </span>
                    </div>
                  );
               })()}
            </div>
          </div>
        ))}
      </div>

      {/* Composition Analysis (Safe Mode) */}
      {(() => {
        try {
            if (!team.players || team.players.length === 0) return null;
            const { warnings, strengths } = analyzeComposition(team.players);
            if (warnings.length === 0 && strengths.length === 0) return null;
            return (
              <div className="flex flex-wrap gap-2 mb-3 justify-center px-2 py-2 border-t border-gray-800/50">
                {warnings.map((w, i) => (
                  <span key={i} className="px-2 py-0.5 text-[10px] font-display font-bold tracking-widest text-red-400 bg-red-950/30 border border-red-900/50 rounded uppercase">{w}</span>
                ))}
                {strengths.map((s, i) => (
                  <span key={i} className="px-2 py-0.5 text-[10px] font-display font-bold tracking-widest text-esport-gold bg-yellow-950/20 border border-yellow-900/50 rounded uppercase shadow-[0_0_5px_rgba(200,170,110,0.1)]">{s}</span>
                ))}
              </div>
            );
        } catch (e) {
            console.warn("Composition analysis failed:", e);
            return null;
        }
      })()}

      {/* Stats Summary */}
      {team.stats && (
        <div className="mt-4 pt-4 border-t border-gray-700/50">
          <div className="flex justify-between items-end mb-2">
             <span className="text-xs text-gray-400 uppercase">Season Winrate</span>
             <span className={`text-xl font-display font-bold ${textColor}`}>{team.stats.winRateSeason || 'N/A'}</span>
          </div>
          {team.advancedStats && (
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="bg-gray-800/40 p-1 rounded text-center">
                 <span className="text-[9px] text-gray-500 uppercase block">GD@15</span>
                 <span className={`text-xs font-bold ${team.advancedStats.goldDiff15.includes('+') ? 'text-green-400' : 'text-red-400'}`}>{team.advancedStats.goldDiff15}</span>
              </div>
              <div className="bg-gray-800/40 p-1 rounded text-center">
                 <span className="text-[9px] text-gray-500 uppercase block">Dragons</span>
                 <span className="text-xs font-bold text-gray-300">{team.advancedStats.dragonControl}</span>
              </div>
              <div className="bg-gray-800/40 p-1 rounded text-center">
                 <span className="text-[9px] text-gray-500 uppercase block">Aggro</span>
                 <div className="w-full bg-gray-700 h-1.5 rounded-full mt-1">
                    <div className={`h-full rounded-full ${team.advancedStats.aggressionRating > 60 ? 'bg-red-500' : 'bg-blue-400'}`} style={{width: `${team.advancedStats.aggressionRating}%`}}></div>
                 </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};