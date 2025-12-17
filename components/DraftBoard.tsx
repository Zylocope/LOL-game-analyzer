import React, { useState } from 'react';
import { Team, Role } from '../types';
import { Swords, Ban, Activity, Info, Link as LinkIcon, Flame, Snowflake, Star, Award, Eye, Target, Coins } from 'lucide-react';
import { CHAMPIONS } from '../data/champions';
import { SYNERGIES } from '../data/synergies';

interface DraftBoardProps {
  team: Team;
  side: 'blue' | 'red';
  onUpdatePlayer: (side: 'blue' | 'red', role: Role, champion: string) => void;
  onUpdateBan: (side: 'blue' | 'red', index: number, champion: string) => void;
  onUpdateName: (side: 'blue' | 'red', name: string) => void;
  onUpdatePlayerName: (side: 'blue' | 'red', role: Role, name: string) => void; // New prop
  onFetchChampionStats: (side: 'blue' | 'red', role: Role, champion: string) => void;
  loading: boolean;
  unavailableChampions: Set<string>;
}

const ROLES: Role[] = ['Top', 'Jungle', 'Mid', 'Bot', 'Support'];

export const DraftBoard: React.FC<DraftBoardProps> = ({ team, side, onUpdatePlayer, onUpdateBan, onUpdateName, onUpdatePlayerName, onFetchChampionStats, loading, unavailableChampions }) => {
  const isBlue = side === 'blue';
  const borderColor = isBlue ? 'border-esport-blue' : 'border-esport-red';
  const textColor = isBlue ? 'text-esport-blue' : 'text-esport-red';
  const bgColor = isBlue ? 'bg-blue-900/20' : 'bg-red-900/20';

  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [hoveredChampion, setHoveredChampion] = useState<string | null>(null);

  const getSuggestions = (query: string) => {
    if (!query) return [];
    return CHAMPIONS.filter(c => 
      c.toLowerCase().startsWith(query.toLowerCase()) && 
      !unavailableChampions.has(c)
    );
  };

  const getBanSuggestions = (query: string) => {
    if (!query) return [];
    return CHAMPIONS.filter(c => 
      c.toLowerCase().startsWith(query.toLowerCase()) && 
      !unavailableChampions.has(c)
    );
  };

  const getMetaColor = (tier?: string) => {
    switch(tier) {
      case 'S+': return 'text-purple-400 bg-purple-400/10 border-purple-400/30';
      case 'S': return 'text-esport-gold bg-esport-gold/10 border-esport-gold/30';
      case 'A': return 'text-green-400 bg-green-400/10 border-green-400/30';
      case 'B': return 'text-blue-400 bg-blue-400/10 border-blue-400/30';
      default: return 'text-gray-400 bg-gray-400/10 border-gray-400/30';
    }
  };

  return (
    <div className={`flex flex-col gap-4 p-4 rounded-xl border ${borderColor} ${bgColor} backdrop-blur-sm relative overflow-visible transition-all duration-300`}>
      {/* Header */}
      <div className="flex justify-between items-center border-b border-gray-700/50 pb-2 mb-2">
        <div className="flex flex-col w-full">
           <label className={`text-xs uppercase tracking-widest font-bold ${textColor} mb-1 opacity-80`}>
            {side} Team
          </label>
          <input 
            type="text" 
            value={team.name}
            onChange={(e) => onUpdateName(side, e.target.value)}
            className={`bg-transparent text-2xl font-display font-bold text-white focus:outline-none placeholder-gray-600 w-full`}
            placeholder={`${side === 'blue' ? 'Team 1' : 'Team 2'}`}
          />
        </div>
      </div>

      {/* Bans */}
      <div className="flex gap-2 mb-2">
        <span className="text-gray-500 text-xs font-mono self-center mr-1">BANS</span>
        {team.bans.map((ban, idx) => {
          const inputId = `${side}-ban-${idx}`;
          const isDropdownOpen = activeDropdown === inputId;
          const suggestions = isDropdownOpen && ban ? getBanSuggestions(ban) : [];
          
          return (
            <div key={`ban-${idx}`} className="relative group w-10">
              <div className="w-10 h-10 bg-gray-900/80 border border-gray-700 rounded flex items-center justify-center overflow-hidden">
                {ban ? (
                  <span className="text-[10px] text-gray-300 font-bold truncate px-1">{ban}</span>
                ) : (
                  <Ban size={14} className="text-gray-600" />
                )}
              </div>
              <input
                  type="text"
                  value={ban}
                  onChange={(e) => {
                    onUpdateBan(side, idx, e.target.value);
                    setActiveDropdown(inputId);
                  }}
                  onFocus={() => setActiveDropdown(inputId)}
                  onBlur={() => setTimeout(() => setActiveDropdown(null), 200)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer text-xs"
                  placeholder="Ban"
                  title={`Ban ${idx + 1}`}
                  autoComplete="off"
                />
                
                {/* Ban Dropdown */}
                {isDropdownOpen && suggestions.length > 0 && (
                  <ul className="absolute top-full left-0 w-32 bg-gray-900 border border-gray-700 rounded-b shadow-xl z-[70] max-h-48 overflow-y-auto mt-1">
                    {suggestions.map((s) => (
                      <li 
                        key={s}
                        className="px-3 py-2 text-xs text-gray-300 hover:bg-gray-800 hover:text-white cursor-pointer border-b border-gray-800 last:border-0"
                        onMouseDown={(e) => {
                          e.preventDefault();
                          onUpdateBan(side, idx, s);
                          setActiveDropdown(null);
                        }}
                      >
                        {s}
                      </li>
                    ))}
                  </ul>
                )}
            </div>
          )
        })}
      </div>

      {/* Picks */}
      <div className="flex flex-col gap-2">
        {team.players.map((player, idx) => {
          const inputId = `${side}-${player.role}`;
          const isDropdownOpen = activeDropdown === inputId;
          const suggestions = isDropdownOpen && player.champion ? getSuggestions(player.champion) : [];
          const isBanned = player.champion && unavailableChampions.has(player.champion) && team.bans.includes(player.champion); 
          
          // Synergy Check
          const isSynergistic = hoveredChampion && player.champion && SYNERGIES[hoveredChampion]?.includes(player.champion);
          const isHovered = hoveredChampion === player.champion;
          
          // Meta & Form Logic
          const metaClass = player.championStats?.metaTier ? getMetaColor(player.championStats.metaTier) : '';
          const isHot = player.recentForm === 'Hot';
          const isCold = player.recentForm === 'Cold';
          
          // Dynamic Styles
          let rowBorderClass = 'border-gray-800 hover:border-gray-600';
          let shadowClass = '';
          
          if (isSynergistic) {
            rowBorderClass = 'border-esport-gold bg-yellow-900/20';
            shadowClass = 'shadow-[0_0_15px_rgba(200,170,110,0.2)]';
          }

          return (
          <div 
            key={player.role} 
            className={`flex items-center gap-3 bg-gray-900/40 p-2 rounded border transition-all duration-300 relative group/row z-10 ${rowBorderClass} ${shadowClass}`}
            onMouseEnter={() => player.champion && setHoveredChampion(player.champion)}
            onMouseLeave={() => setHoveredChampion(null)}
          >
            <div className="w-8 h-8 flex items-center justify-center bg-black/50 rounded-full border border-gray-700 shadow-inner">
               <span className="text-[10px] font-bold text-gray-400 font-mono">{player.role[0]}</span>
            </div>
            
            <div className="flex-1 flex flex-col relative group/input">
               <div className="flex justify-between items-center mb-1">
                 <div className="flex items-center gap-2">
                   <span className="text-xs text-gray-500 font-semibold uppercase">{player.role}</span>
                   {isSynergistic && (
                     <span className="flex items-center gap-1 text-[10px] text-esport-gold font-bold animate-pulse">
                       <LinkIcon size={10} /> SYNERGY
                     </span>
                   )}
                 </div>
                 <div className="flex items-center gap-2">
                   {/* Player Name Input - Editable for smart manual mode */}
                   <input
                     type="text"
                     value={player.name}
                     onChange={(e) => onUpdatePlayerName(side, player.role, e.target.value)}
                     className="text-xs text-gray-400 bg-transparent border-b border-transparent hover:border-gray-600 focus:border-esport-gold focus:text-white focus:outline-none w-20 transition-all placeholder-gray-700"
                     placeholder="Player Name"
                   />
                   
                   {/* Player Form Badge */}
                   {player.recentForm && !isDropdownOpen && !isBanned && (
                     <div className={`flex items-center gap-0.5 px-1 py-0.5 rounded text-[9px] border ${isHot ? 'text-orange-400 border-orange-400/30 bg-orange-900/20' : isCold ? 'text-blue-300 border-blue-400/30 bg-blue-900/20' : 'text-gray-400 border-gray-700'}`}>
                        {isHot ? <Flame size={10} /> : isCold ? <Snowflake size={10} /> : null}
                        {isHot ? 'HOT' : isCold ? 'COLD' : null}
                     </div>
                   )}
                 </div>
               </div>
               <div className="relative">
                  <input
                    type="text"
                    value={player.champion || ''}
                    onChange={(e) => {
                      onUpdatePlayer(side, player.role, e.target.value);
                      setActiveDropdown(inputId);
                    }}
                    onFocus={() => setActiveDropdown(inputId)}
                    onBlur={() => {
                        setTimeout(() => setActiveDropdown(null), 200);
                        if (player.champion && !isBanned) {
                            onFetchChampionStats(side, player.role, player.champion);
                        }
                    }}
                    placeholder="Select Champion..."
                    className={`w-full bg-transparent text-sm font-bold focus:outline-none uppercase tracking-wide
                      ${isBanned ? 'text-red-500 line-through decoration-2' : player.champion ? 'text-white' : 'text-gray-600'}
                      ${isSynergistic ? 'text-esport-gold' : ''}
                    `}
                    autoComplete="off"
                  />
                  
                  {/* Meta Tier Badge (Right side of input) */}
                  {player.championStats?.metaTier && !isBanned && !isDropdownOpen && (
                    <div className={`absolute right-0 top-1/2 -translate-y-1/2 flex items-center justify-center px-1.5 py-0.5 rounded border text-[10px] font-bold ${metaClass}`}>
                      {player.championStats.metaTier}
                    </div>
                  )}

                  {isBanned && (
                    <div className="absolute right-0 top-1/2 -translate-y-1/2 flex items-center gap-1 bg-red-900/90 text-red-200 text-[10px] font-bold px-1.5 py-0.5 rounded border border-red-700 pointer-events-none">
                      <Ban size={10} /> BANNED
                    </div>
                  )}

                  {!player.champion && !isBanned && (
                    <div className="absolute right-0 top-0 pointer-events-none">
                      <Swords size={14} className="text-gray-700" />
                    </div>
                  )}
                  
                  {/* Autocomplete Dropdown */}
                  {isDropdownOpen && suggestions.length > 0 && (
                    <ul className="absolute top-full left-0 w-full bg-gray-900 border border-gray-700 rounded-b shadow-xl z-[60] max-h-48 overflow-y-auto mt-1">
                      {suggestions.map((s) => (
                        <li 
                          key={s}
                          className="px-3 py-2 text-xs text-gray-300 hover:bg-gray-800 hover:text-white cursor-pointer border-b border-gray-800 last:border-0"
                          onMouseDown={(e) => {
                            e.preventDefault(); 
                            onUpdatePlayer(side, player.role, s);
                            onFetchChampionStats(side, player.role, s);
                            setActiveDropdown(null);
                          }}
                        >
                          {s}
                        </li>
                      ))}
                    </ul>
                  )}
               </div>

               {/* Stats Tooltip */}
               {player.championStats && !isDropdownOpen && !isBanned && (
                 <div className="absolute left-0 bottom-full mb-2 w-80 bg-gray-900/95 border border-esport-gold/30 rounded-lg shadow-2xl p-3 z-50 opacity-0 group-hover/row:opacity-100 transition-all duration-300 pointer-events-none translate-y-2 group-hover/row:translate-y-0 backdrop-blur-md">
                   <div className="flex items-center justify-between mb-2 border-b border-gray-700/50 pb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-esport-gold font-bold text-xs uppercase tracking-wider">{player.champion} Stats</span>
                        {player.isComfortPick && (
                           <span className="flex items-center gap-0.5 text-[9px] text-yellow-400 border border-yellow-400/30 px-1 rounded bg-yellow-400/10">
                             <Star size={8} fill="currentColor" /> MAIN
                           </span>
                        )}
                      </div>
                      <Activity size={12} className="text-esport-accent" />
                   </div>
                   
                   {/* Advanced Player Data Grid */}
                   <div className="grid grid-cols-4 gap-2 mb-2">
                      <div className="bg-gray-800/50 p-1.5 rounded flex flex-col">
                         <span className="text-[9px] text-gray-500 uppercase">Games</span>
                         <span className="text-xs font-bold text-white">{player.gamesOnChamp || '-'}</span>
                      </div>
                      <div className="bg-gray-800/50 p-1.5 rounded flex flex-col">
                         <span className="text-[9px] text-gray-500 uppercase">KDA</span>
                         <span className="text-xs font-bold text-white">{player.advancedStats?.kda || '-'}</span>
                      </div>
                      <div className="bg-gray-800/50 p-1.5 rounded flex flex-col">
                         <span className="text-[9px] text-gray-500 uppercase">DPM</span>
                         <span className="text-xs font-bold text-white">{player.advancedStats?.dpm || '-'}</span>
                      </div>
                      <div className="bg-gray-800/50 p-1.5 rounded flex flex-col">
                         <span className="text-[9px] text-gray-500 uppercase">VS/m</span>
                         <span className="text-xs font-bold text-white">{player.advancedStats?.visionScore || '-'}</span>
                      </div>
                   </div>
                   
                   {/* Advanced Row 2 */}
                   {player.advancedStats && (
                    <div className="flex gap-2 mb-2">
                       <div className="flex-1 bg-gray-800/50 p-1.5 rounded flex items-center gap-2">
                          <Target size={12} className="text-gray-500" />
                          <div className="flex flex-col">
                             <span className="text-[9px] text-gray-500 uppercase leading-none">Lane Phase</span>
                             <span className={`text-[10px] font-bold leading-tight ${player.advancedStats.lanePhase === 'Dominant' ? 'text-green-400' : 'text-gray-300'}`}>
                               {player.advancedStats.lanePhase}
                             </span>
                          </div>
                       </div>
                       <div className="flex-1 bg-gray-800/50 p-1.5 rounded flex items-center gap-2">
                          <Coins size={12} className="text-yellow-600" />
                          <div className="flex flex-col">
                             <span className="text-[9px] text-gray-500 uppercase leading-none">CS Diff @15</span>
                             <span className={`text-[10px] font-bold leading-tight ${parseInt(player.advancedStats.csDiff15) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                               {player.advancedStats.csDiff15}
                             </span>
                          </div>
                       </div>
                    </div>
                   )}

                   <div className="grid grid-cols-2 gap-2 mb-2">
                      <div className="bg-gray-800/50 p-1.5 rounded">
                        <span className="text-[10px] text-gray-500 uppercase block">Win Rate</span>
                        <span className="text-sm font-bold text-white">{player.championStats.winRate}</span>
                      </div>
                      <div className="bg-gray-800/50 p-1.5 rounded">
                        <span className="text-[10px] text-gray-500 uppercase block">Meta Tier</span>
                        <span className={`text-sm font-bold ${metaClass.split(' ')[0]}`}>{player.championStats.metaTier}</span>
                      </div>
                   </div>
                   <div className="bg-gray-800/30 p-2 rounded border border-gray-700/50">
                      <span className="text-[10px] text-gray-500 uppercase block mb-1">Notes</span>
                      <p className="text-[10px] text-gray-300 leading-tight">{player.championStats.counterNotes}</p>
                   </div>
                   {/* Arrow */}
                   <div className="absolute top-full left-4 -mt-px border-[6px] border-transparent border-t-gray-900/95"></div>
                 </div>
               )}
            </div>
          </div>
        )})}
      </div>

      {/* Stats Summary (if loaded) */}
      {team.stats && (
        <div className="mt-4 pt-4 border-t border-gray-700/50">
          <div className="flex justify-between items-end mb-2">
             <span className="text-xs text-gray-400 uppercase">Season Winrate</span>
             <span className={`text-xl font-display font-bold ${textColor}`}>{team.stats.winRateSeason}</span>
          </div>
          
          {/* Advanced Team Stats Display */}
          {team.advancedStats && (
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="bg-gray-800/40 p-1 rounded text-center">
                 <span className="text-[9px] text-gray-500 uppercase block">GD@15</span>
                 <span className={`text-xs font-bold ${team.advancedStats.goldDiff15.includes('+') ? 'text-green-400' : 'text-red-400'}`}>
                   {team.advancedStats.goldDiff15}
                 </span>
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

          <div className="space-y-1">
            <p className="text-[10px] text-gray-500 uppercase font-bold">Recent Achievements</p>
            <div className="flex flex-wrap gap-1">
              {team.stats.recentAchievements.slice(0, 2).map((ach, i) => (
                <span key={i} className="text-[10px] bg-gray-800 px-1.5 py-0.5 rounded text-gray-300 border border-gray-700">
                  {ach}
                </span>
              ))}
            </div>
          </div>
          <div className="mt-2">
             <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Playstyle</p>
             <p className="text-xs text-gray-300 italic leading-relaxed opacity-80">"{team.stats.playstyle}"</p>
          </div>
        </div>
      )}
    </div>
  );
};