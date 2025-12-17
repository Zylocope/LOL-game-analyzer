import React, { useState } from 'react';
import { PRESET_TEAMS, PresetTeam } from '../data/teams';
import { Search, Swords, Shield } from 'lucide-react';

interface LobbyProps {
  onStartMatch: (blue: PresetTeam, red: PresetTeam) => void;
}

interface TeamCardProps {
  team: PresetTeam;
  side: 'blue' | 'red';
  isSelected: boolean;
  onClick: () => void;
}

const TeamCard: React.FC<TeamCardProps> = ({ team, side, isSelected, onClick }) => (
  <div 
    onClick={onClick}
    className={`
      relative p-4 rounded-xl border cursor-pointer transition-all duration-300 group overflow-hidden
      ${isSelected 
        ? side === 'blue' 
          ? 'border-esport-blue bg-blue-900/40 shadow-[0_0_20px_rgba(0,168,255,0.2)]' 
          : 'border-esport-red bg-red-900/40 shadow-[0_0_20px_rgba(255,51,51,0.2)]'
        : 'border-gray-800 bg-gray-900/40 hover:border-gray-600 hover:bg-gray-800/60'
      }
    `}
  >
    <div className="flex justify-between items-start mb-3 relative z-10">
      <h3 className={`font-display font-bold text-lg tracking-wide ${isSelected ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'}`}>
        {team.name}
      </h3>
      {isSelected && (
        <Shield size={18} className={side === 'blue' ? 'text-esport-blue' : 'text-esport-red'} fill="currentColor" />
      )}
    </div>
    
    <div className="space-y-1.5 relative z-10">
      {team.players.map(p => (
          <div key={p.role} className="flex items-center text-xs">
            <span className={`font-bold uppercase w-8 ${isSelected ? 'text-gray-300' : 'text-gray-600'}`}>{p.role.substring(0, 3)}</span>
            <span className={`${isSelected ? 'text-gray-200' : 'text-gray-500'}`}>{p.name}</span>
          </div>
      ))}
    </div>

    {/* Background Gradient Effect */}
    <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 bg-gradient-to-br ${side === 'blue' ? 'from-blue-600 to-transparent' : 'from-red-600 to-transparent'}`}></div>
  </div>
);

export const Lobby: React.FC<LobbyProps> = ({ onStartMatch }) => {
  const [selectedBlue, setSelectedBlue] = useState<PresetTeam | null>(null);
  const [selectedRed, setSelectedRed] = useState<PresetTeam | null>(null);
  const [blueSearch, setBlueSearch] = useState('');
  const [redSearch, setRedSearch] = useState('');

  const filteredBlue = PRESET_TEAMS.filter(t => 
    t.name.toLowerCase().includes(blueSearch.toLowerCase())
  );
  
  const filteredRed = PRESET_TEAMS.filter(t => 
    t.name.toLowerCase().includes(redSearch.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 flex flex-col h-[calc(100vh-64px)]">
      
      {/* Header Section */}
      <div className="text-center mb-8 shrink-0">
        <h2 className="text-5xl font-display font-bold text-white tracking-widest mb-2">
          MATCH <span className="text-esport-gold">LOBBY</span>
        </h2>
        <p className="text-gray-400 text-sm tracking-wide uppercase">Select two teams to begin simulation</p>
      </div>

      {/* Main Selection Area */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[1fr_80px_1fr] gap-4 mb-8">
        
        {/* Blue Side Panel */}
        <div className="flex flex-col bg-gray-900/20 rounded-2xl border border-blue-900/30 overflow-hidden relative">
           <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-esport-blue to-transparent opacity-50"></div>
           
           <div className="p-6 pb-4 shrink-0">
              <div className="flex items-center justify-between mb-4">
                 <h3 className="text-esport-blue font-display text-3xl font-bold uppercase tracking-wider">Blue Side</h3>
                 <Shield className="text-esport-blue" size={24} />
              </div>
              
              <div className="relative group">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-blue-500/50 group-focus-within:text-blue-400 transition-colors" size={18} />
                <input 
                  type="text" 
                  placeholder="Find Blue Team..."
                  className="w-full bg-gray-900/50 border border-blue-900/50 rounded-lg py-3 pl-10 pr-4 text-gray-200 placeholder-blue-500/30 focus:outline-none focus:border-esport-blue focus:bg-gray-900 focus:ring-1 focus:ring-esport-blue/50 transition-all"
                  value={blueSearch}
                  onChange={(e) => setBlueSearch(e.target.value)}
                />
              </div>
           </div>

           <div className="flex-1 overflow-y-auto custom-scrollbar p-6 pt-0">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                {filteredBlue.map(team => (
                  <TeamCard 
                    key={team.id} 
                    team={team} 
                    side="blue" 
                    isSelected={selectedBlue?.id === team.id}
                    onClick={() => setSelectedBlue(team)}
                  />
                ))}
              </div>
           </div>
        </div>

        {/* VS Divider (Desktop) */}
        <div className="hidden lg:flex flex-col items-center justify-center relative">
           <div className="h-full w-px bg-gradient-to-b from-transparent via-gray-700 to-transparent absolute"></div>
           <div className="relative z-10 bg-esport-dark border-2 border-gray-700 w-16 h-16 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(0,0,0,0.8)]">
             <span className="font-display font-bold text-2xl text-gray-500 italic pr-1">VS</span>
           </div>
        </div>

        {/* Red Side Panel */}
        <div className="flex flex-col bg-gray-900/20 rounded-2xl border border-red-900/30 overflow-hidden relative">
           <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-esport-red to-transparent opacity-50"></div>
           
           <div className="p-6 pb-4 shrink-0">
              <div className="flex items-center justify-between mb-4">
                 <Shield className="text-esport-red" size={24} />
                 <h3 className="text-esport-red font-display text-3xl font-bold uppercase tracking-wider">Red Side</h3>
              </div>
              
              <div className="relative group">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-red-500/50 group-focus-within:text-red-400 transition-colors" size={18} />
                <input 
                  type="text" 
                  placeholder="Find Red Team..."
                  className="w-full bg-gray-900/50 border border-red-900/50 rounded-lg py-3 pl-10 pr-4 text-gray-200 placeholder-red-500/30 focus:outline-none focus:border-esport-red focus:bg-gray-900 focus:ring-1 focus:ring-esport-red/50 transition-all text-right"
                  value={redSearch}
                  onChange={(e) => setRedSearch(e.target.value)}
                />
              </div>
           </div>

           <div className="flex-1 overflow-y-auto custom-scrollbar p-6 pt-0">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                {filteredRed.map(team => (
                  <TeamCard 
                    key={team.id} 
                    team={team} 
                    side="red" 
                    isSelected={selectedRed?.id === team.id}
                    onClick={() => setSelectedRed(team)}
                  />
                ))}
              </div>
           </div>
        </div>
      </div>

      {/* Start Button */}
      <div className="shrink-0 flex justify-center pb-8">
        <button 
          disabled={!selectedBlue || !selectedRed}
          onClick={() => selectedBlue && selectedRed && onStartMatch(selectedBlue, selectedRed)}
          className={`
            group relative px-16 py-5 rounded-xl font-display font-bold text-2xl tracking-[0.2em] transition-all duration-300 overflow-hidden
            ${selectedBlue && selectedRed 
              ? 'bg-esport-gold text-black hover:scale-105 hover:shadow-[0_0_40px_rgba(200,170,110,0.4)]' 
              : 'bg-gray-800 text-gray-600 cursor-not-allowed border border-gray-700'}
          `}
        >
          <div className="relative z-10 flex items-center gap-4">
             {selectedBlue && selectedRed ? <Swords size={28} className="animate-pulse" /> : <Swords size={28} />}
             <span>ENTER DRAFT</span>
          </div>
          {selectedBlue && selectedRed && (
             <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 skew-y-12"></div>
          )}
        </button>
      </div>

    </div>
  );
};