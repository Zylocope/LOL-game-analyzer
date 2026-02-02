import React, { useState } from 'react';
import { Team, Role } from '../types';
import { Swords, Ban } from 'lucide-react';
import { ChampionSelectModal } from './ChampionSelectModal';
import { analyzeComposition } from '../src/compositionAnalysis'; // Verify this path matches your folder structure
import { useMatchups } from '../src/hooks/useMatchups';
import { TeamLogo } from './TeamLogo';

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

      {/* Header */}
      <div className="p-4 border-b border-gray-800/50 flex justify-between items-center bg-gray-900/40">
        <div className="flex items-center gap-3 w-2/3">
           <div className="w-12 h-12 bg-gray-950/40 p-1.5 rounded-lg border border-gray-800/50 shrink-0 shadow-inner">
              <TeamLogo team={{ id: team.id || 'unknown', name: team.name }} className="w-full h-full object-contain filter drop-shadow-[0_0_2px_rgba(255,255,255,0.4)]" />
           </div>
           <input 
             value={team.name}
             onChange={(e) => onUpdateName(side, e.target.value)}
             className={`bg-transparent text-2xl font-display font-bold uppercase tracking-wider ${textColor} w-full focus:outline-none focus:bg-gray-800/50 rounded px-1`}
           />
        </div>
        <div className="flex gap-1">
          {team.bans.map((ban, idx) => (
            <button
              key={idx}
              onClick={() => openSelect('Top', true, idx)}
              className="w-8 h-8 bg-black/40 border border-gray-700 rounded flex items-center justify-center hover:border-gray-500 overflow-hidden group"
            >
              {ban ? (
                <div className="relative w-full h-full">
                   <img src={getIconUrl(ban)} className="w-full h-full object-cover opacity-60 grayscale group-hover:grayscale-0" />
                   <Ban className="absolute inset-0 m-auto text-gray-400 w-4 h-4" />
                </div>
              ) : (
                <Ban size={12} className="text-gray-600" />
              )}
            </button>
          ))}
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
               
               {/* --- COUNTER PICK STRIP (ACTIVE) --- */}
               {matchups[player.role] && (
                  <div 
                    className={`absolute -left-3 top-0 bottom-0 my-auto h-8 w-1 rounded-r shadow-[0_0_8px_rgba(0,0,0,0.5)]
                      ${matchups[player.role].type === 'advantage' 
                        ? 'bg-green-500 shadow-[0_0_10px_lime]' 
                        : 'bg-red-500 shadow-[0_0_10px_red]'}`
                    }
                    title={`${matchups[player.role].type === 'advantage' ? 'Counters' : 'Countered by'} enemy (Historical WR: ${matchups[player.role].winRate.toFixed(1)}%)`}
                  />
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
               
               {player.champion && player.championStats && (
                  <div className="flex items-center gap-2 mt-1 w-full overflow-hidden">
                     {player.championStats.gamesPlayed && player.championStats.gamesPlayed > 0 ? (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-bold whitespace-nowrap shrink-0
                            ${parseInt(player.championStats.winRate) >= 60 
                              ? 'bg-yellow-900/40 text-yellow-200 border-yellow-700/50' 
                              : 'bg-blue-900/40 text-blue-200 border-blue-700'
                            }`}>
                            {player.championStats.winRate} ({player.championStats.gamesPlayed}G)
                        </span>
                     ) : (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded whitespace-nowrap shrink-0 font-bold ${parseInt(player.championStats.winRate) > 50 ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                          {player.championStats.winRate} Global
                        </span>
                     )}
                     <span className="text-[10px] text-gray-500 flex items-center gap-1 flex-1 min-w-0">
                       <span className="shrink-0 opacity-50">◎</span>
                       <span className="truncate w-full text-gray-400">
                         {player.championStats.gamesPlayed && player.championStats.gamesPlayed > 5 
                            ? <span className="text-esport-gold font-bold">Main</span> 
                            : player.championStats.roleEffectiveness || "Unknown"
                         }
                       </span>
                     </span>
                  </div>
               )}
            </div>
          </div>
        ))}
      </div>

      {/* Composition Analysis */}
      {(() => {
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