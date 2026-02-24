import React, { useState, useEffect } from 'react';
import { Search, Swords, Shield, Loader2, ArrowRight } from 'lucide-react';
import { PRESET_TEAMS } from '../data/teams';
import { TeamLogo } from './TeamLogo';

interface LobbyTeam {
  id: string;
  name: string;
  region?: string;
  logo?: string;
  players?: any[]; 
}

interface LobbyProps {
  onStartMatch: (blue: any, red: any) => void;
}

// 🆕 Reusable Team Selection Modal (Clean UX)
const TeamSelectModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onSelect: (team: LobbyTeam) => void;
  teams: LobbyTeam[];
  side: 'blue' | 'red';
}> = ({ isOpen, onClose, onSelect, teams, side }) => {
  const [search, setSearch] = useState('');
  
  if (!isOpen) return null;

  // SORT BY RANK (If available) - Prefer higher rank (lower number)
  // Teams with rating are sorted descending.
  const sortedTeams = [...teams].sort((a, b) => {
      // Force ratings to numbers, default to 0 if missing
      const rateA = Number((a as any).rating) || 0;
      const rateB = Number((b as any).rating) || 0;
      
      // If both have ratings, higher rating first
      if (rateA > 0 || rateB > 0) {
          return rateB - rateA; 
      }
      
      // Fallback to alphabetical if no ratings
      return a.name.localeCompare(b.name);
  });

  const filtered = sortedTeams.filter(t => t.name.toLowerCase().includes(search.toLowerCase()));
  const colorClass = side === 'blue' ? 'border-blue-500 text-blue-400' : 'border-red-500 text-red-400';
  const bgClass = side === 'blue' ? 'hover:bg-blue-900/20 hover:border-blue-500' : 'hover:bg-red-900/20 hover:border-red-500';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in zoom-in-95 duration-200">
      <div className={`bg-esport-dark border ${colorClass} rounded-xl w-full max-w-2xl h-[70vh] flex flex-col shadow-2xl overflow-hidden`}>
        {/* Header */}
        <div className="p-4 border-b border-gray-800 bg-gray-900/80">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
            <input 
              autoFocus
              type="text" 
              placeholder={`Search ${side === 'blue' ? 'Blue' : 'Red'} Team...`}
              className="w-full bg-gray-800 text-white rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:ring-2 border border-gray-700 focus:border-transparent"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
        {/* List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
          {filtered.map(team => (
            <button
              key={team.id}
              onClick={() => { onSelect(team); onClose(); setSearch(''); }}
              className={`w-full text-left p-3 rounded-lg border border-transparent transition-all flex items-center gap-4 group ${bgClass}`}
            >
              {/* Smart Logo - Subtle Container */}
              <div className="w-16 h-16 flex-shrink-0 bg-gray-900/40 border border-gray-800/50 p-2 rounded-xl overflow-hidden shadow-lg">
                 <TeamLogo team={team} className="w-full h-full object-contain filter drop-shadow-[0_0_3px_rgba(255,255,255,0.3)]" />
              </div>

              <div className="flex-1">
                  <div className="flex items-center gap-2">
                      <span className="font-bold text-gray-300 group-hover:text-white block text-lg">{team.name}</span>
                      {(team as any).rating && (
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold tracking-tight
                              ${(team as any).rating >= 2000 ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30' : 
                                (team as any).rating >= 1700 ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 
                                'bg-gray-700 text-gray-400'}`}>
                              {(team as any).rating}
                          </span>
                      )}
                  </div>
                  <span className="text-xs text-gray-500 group-hover:text-gray-400 uppercase tracking-widest">{team.region}</span>
              </div>
            </button>
          ))}
        </div>
        {/* Close */}
        <button onClick={onClose} className="p-3 text-gray-500 hover:text-white text-sm border-t border-gray-800">
          Cancel Selection
        </button>
      </div>
    </div>
  );
};

export const Lobby: React.FC<LobbyProps> = ({ onStartMatch }) => {
  const [allTeams, setAllTeams] = useState<LobbyTeam[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [selectedBlue, setSelectedBlue] = useState<LobbyTeam | null>(null);
  const [selectedRed, setSelectedRed] = useState<LobbyTeam | null>(null);
  
  // Modal State
  const [modalOpen, setModalOpen] = useState<'blue' | 'red' | null>(null);

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/teams');
        const data = await response.json();
        
        // 1. Map API Ratings & Regions
        const apiMap = new Map();
        if (data.teams && Array.isArray(data.teams)) {
            data.teams.forEach((t: any) => {
                if (t.team) {
                    // Store strict lower case key
                    apiMap.set(t.team.toLowerCase(), t);
                    // Store normalized key (no spaces)
                    apiMap.set(t.team.toLowerCase().replace(/[^a-z0-9]/g, ''), t);
                }
            });
        }
        
        // ALIAS MAP (Preset Name -> DB Name)
        const ALIASES: Record<string, string> = {
            "psg talon": "talon",
            "karmine corp": "karmine corp blue" // Example if needed
        };

        // 2. Build the Final List from the API (Active/Veteran Teams)
        // This is the list of ~58 teams you want.
        const finalPool: LobbyTeam[] = [];
        
        if (data.teams && Array.isArray(data.teams)) {
            data.teams.forEach((t: any) => {
                 const name = typeof t === 'string' ? t : t.team;
                 const rating = typeof t === 'object' ? t.rating : 0;
                 const region = typeof t === 'object' ? t.region : "World";
                 
                 // Skip if blacklisted or known bad data (optional safety)
                 if (name.includes("Esports Academy") || name.includes("Challengers")) return;

                 // Check if we have a Preset for this team (Logo/Roster)
                 const preset = PRESET_TEAMS.find(p => p.name.toLowerCase() === name.toLowerCase());
                 
                 // ALIAS CHECK: If DB name is "TALON", check if we have "PSG Talon" preset
                 let foundPreset = preset;
                 if (!foundPreset) {
                     const reverseAlias = Object.keys(ALIASES).find(key => ALIASES[key] === name.toLowerCase());
                     if (reverseAlias) {
                         foundPreset = PRESET_TEAMS.find(p => p.name.toLowerCase() === reverseAlias);
                     }
                 }
                 
                 if (foundPreset) {
                     // MERGE: Use Preset Metadata + API Rating
                     finalPool.push({
                         ...foundPreset,
                         rating: rating,
                         region: region // Update region if needed
                     });
                 } else {
                     // NEW TEAM: Use API Data (No Logo, but valid team)
                     finalPool.push({
                         id: name.toLowerCase().replace(/[^a-z0-9]/g, ''),
                         name: name,
                         region: region,
                         rating: rating
                     });
                 }
            });
        }

        // 3. Fallback: Ensure all Presets are included even if API missed them
        PRESET_TEAMS.forEach(preset => {
            if (!finalPool.find(t => t.name.toLowerCase() === preset.name.toLowerCase())) {
                finalPool.push({
                    ...preset,
                    rating: 0,
                    region: "World"
                });
            }
        });

        // 4. SORT: Rating (High->Low) then Name (A->Z)
        finalPool.sort((a, b) => {
            const rA = (a as any).rating || 0;
            const rB = (b as any).rating || 0;
            if (rA !== rB) return rB - rA;
            return a.name.localeCompare(b.name);
        });

        setAllTeams(finalPool);

      } catch (error) {
        setAllTeams(PRESET_TEAMS as LobbyTeam[]);
      } finally {
        setLoading(false);
      }
    };
    fetchTeams();
  }, []);

  const handleStart = () => {
    if (selectedBlue && selectedRed) {
      onStartMatch(selectedBlue, selectedRed);
    }
  };

  return (
    <div className="h-full flex flex-col p-8 max-w-5xl mx-auto animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="text-center mb-12 mt-8">
        <h1 className="text-6xl font-display font-bold text-transparent bg-clip-text bg-gradient-to-r from-esport-gold via-white to-esport-gold mb-2 tracking-tighter drop-shadow-lg">
          NEXUS SIGHT
        </h1>
        <p className="text-gray-500 font-mono text-sm tracking-widest uppercase">Predictive Draft Analysis Engine</p>
      </div>

      {loading ? (
        <div className="flex-1 flex flex-col items-center justify-center text-esport-gold opacity-50">
          <Loader2 className="animate-spin mb-4" size={32} />
          <p className="text-xs tracking-widest">CONNECTING TO DATABASE...</p>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center gap-10">
          
          {/* Spotlight Selectors */}
          <div className="flex w-full items-center justify-center gap-12">
            
            {/* BLUE CARD */}
            <button 
                onClick={() => setModalOpen('blue')}
                className={`
                    w-80 h-96 rounded-2xl border-2 flex flex-col items-center justify-center gap-6 transition-all duration-300 group relative overflow-hidden
                    ${selectedBlue 
                        ? 'border-blue-500 bg-blue-900/10 shadow-[0_0_40px_rgba(59,130,246,0.2)]' 
                        : 'border-gray-800 bg-gray-900/40 hover:border-blue-500/50 hover:bg-gray-900/60'}
                `}
            >
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                
                {selectedBlue ? (
                    <>
                        <div className="w-40 h-40 relative flex items-center justify-center">
                            {/* Glow Effect */}
                            <div className="absolute inset-0 bg-blue-500/20 blur-3xl rounded-full animate-pulse" />
                            
                            {/* Logo with Fallback */}
                        <div className="w-40 h-40 z-10 drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]">
                           <TeamLogo team={selectedBlue} className="w-full h-full object-contain filter drop-shadow-[0_0_5px_rgba(255,255,255,0.4)]" />
                        </div>
                        </div>
                        
                        <div className="text-center z-10">
                            <h2 className="text-4xl font-display font-bold text-white mb-2 tracking-tight">{selectedBlue.name}</h2>
                            <p className="text-blue-400 text-xs font-bold uppercase tracking-[0.2em]">Blue Side</p>
                        </div>
                        <span className="text-xs text-gray-500 absolute bottom-6 group-hover:text-blue-300 transition-colors">Click to Change</span>
                    </>
                ) : (
                    <>
                        <div className="w-20 h-20 rounded-full bg-gray-800 flex items-center justify-center group-hover:scale-110 transition-transform">
                            <Search className="text-gray-600 group-hover:text-blue-400" size={32} />
                        </div>
                        <span className="text-xl font-bold text-gray-600 group-hover:text-blue-400">Select Blue Team</span>
                    </>
                )}
            </button>

            {/* VS */}
            <div className="text-4xl font-display font-bold text-gray-700 italic select-none">VS</div>

            {/* RED CARD */}
            <button 
                onClick={() => setModalOpen('red')}
                className={`
                    w-80 h-96 rounded-2xl border-2 flex flex-col items-center justify-center gap-6 transition-all duration-300 group relative overflow-hidden
                    ${selectedRed 
                        ? 'border-red-500 bg-red-900/10 shadow-[0_0_40px_rgba(239,68,68,0.2)]' 
                        : 'border-gray-800 bg-gray-900/40 hover:border-red-500/50 hover:bg-gray-900/60'}
                `}
            >
                <div className="absolute inset-0 bg-gradient-to-bl from-red-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                
                {selectedRed ? (
                    <>
                        <div className="w-40 h-40 relative flex items-center justify-center">
                            <div className="absolute inset-0 bg-red-500/20 blur-3xl rounded-full animate-pulse" />
                            {/* Removed bg-white to match Blue side style */}
                            <div className="w-40 h-40 z-10 drop-shadow-[0_0_15px_rgba(239,68,68,0.5)]">
                                <TeamLogo team={selectedRed} className="w-full h-full object-contain filter drop-shadow-[0_0_5px_rgba(255,255,255,0.4)]" />
                            </div>
                        </div>
                        <div className="text-center z-10">
                            <h2 className="text-3xl font-bold text-white mb-1">{selectedRed.name}</h2>
                            <p className="text-red-400 text-xs font-bold uppercase tracking-widest">Red Side</p>
                        </div>
                        <span className="text-xs text-gray-500 absolute bottom-6 group-hover:text-red-300 transition-colors">Click to Change</span>
                    </>
                ) : (
                    <>
                        <div className="w-20 h-20 rounded-full bg-gray-800 flex items-center justify-center group-hover:scale-110 transition-transform">
                            <Search className="text-gray-600 group-hover:text-red-400" size={32} />
                        </div>
                        <span className="text-xl font-bold text-gray-600 group-hover:text-red-400">Select Red Team</span>
                    </>
                )}
            </button>

          </div>

          {/* Action Button */}
          <button
            onClick={handleStart}
            disabled={!selectedBlue || !selectedRed}
            className={`
              flex items-center gap-3 px-12 py-5 rounded-full font-display font-bold text-lg tracking-widest transition-all duration-300
              ${selectedBlue && selectedRed 
                ? 'bg-esport-gold text-black hover:scale-105 hover:bg-white shadow-[0_0_30px_rgba(200,170,110,0.4)]' 
                : 'bg-gray-800 text-gray-600 cursor-not-allowed grayscale'}
            `}
          >
            ENTER DRAFT PHASE <ArrowRight size={20} />
          </button>

        </div>
      )}

      {/* Modals */}
      <TeamSelectModal 
        isOpen={modalOpen === 'blue'} 
        onClose={() => setModalOpen(null)} 
        onSelect={setSelectedBlue} 
        teams={allTeams} 
        side="blue" 
      />
      <TeamSelectModal 
        isOpen={modalOpen === 'red'} 
        onClose={() => setModalOpen(null)} 
        onSelect={setSelectedRed} 
        teams={allTeams} 
        side="red" 
      />

    </div>
  );
};