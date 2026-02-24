import React, { useState, useMemo } from 'react';
import { Search, X, Filter, BarChart2, Shield, Sword, Sparkles, Crosshair } from 'lucide-react';
import { CHAMPION_DATA } from '../data/championTags';
import CHAMPION_STATS from '../data/championStats.json';

interface ChampionSelectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (champion: string) => void;
  unavailableChampions: Set<string>;
}

// Stats Type Helper
interface ChampStats {
  name: string;
  winRate: number;
  pickRate: number;
  roles: string[];
}

const ROLES = [
  { id: 'all', label: 'All Roles', icon: null },
  { id: 'top', label: 'Top', icon: <Sword size={14} className="rotate-90" /> },
  { id: 'jungle', label: 'Jungle', icon: <Filter size={14} /> },
  { id: 'mid', label: 'Mid', icon: <Sparkles size={14} /> },
  { id: 'bot', label: 'Bot', icon: <Crosshair size={14} /> },
  { id: 'support', label: 'Support', icon: <Shield size={14} /> }
];

const TYPES = [
  { id: 'all', label: 'All Types' },
  { id: 'Fighter', label: 'Fighters' },
  { id: 'Mage', label: 'Mages' },
  { id: 'Assassin', label: 'Assassins' },
  { id: 'Marksman', label: 'Marksmen' },
  { id: 'Tank', label: 'Tanks' },
  { id: 'Support', label: 'Supports' },
  { id: 'Juggernaut', label: 'Juggernauts' },
  { id: 'Diver', label: 'Divers' },
  { id: 'Battlemage', label: 'Battlemages' },
  { id: 'Burst', label: 'Burst Mages' },
  { id: 'Artillery', label: 'Artillery' },
  { id: 'Enchanter', label: 'Enchanters' },
  { id: 'Catcher', label: 'Catchers' },
  { id: 'Vanguard', label: 'Vanguards' },
  { id: 'Warden', label: 'Wardens' },
  { id: 'Skirmisher', label: 'Skirmishers' }
];

const RANGES = [
  { id: 'all', label: 'All Ranges' },
  { id: 'Melee', label: 'Melee' },
  { id: 'Ranged', label: 'Ranged' }
];

// Helper to get stats safely (DEPRECATED - stats are now embedded)
// const getStats = (key: string): ChampStats | null => ...

// Helper for inferring lane roles if not explicit (using BOTH static tags and mined stats)
const inferRoles = (champ: any, stats: ChampStats | null) => {
  const r = new Set<string>();
  const c = champ.classes;
  const name = champ.name;
  
  // 1. Primary Mapping based on Class
  if (c.includes('Fighter') || c.includes('Tank')) r.add('top');
  if (c.includes('Mage') || c.includes('Assassin')) r.add('mid');
  if (c.includes('Marksman')) r.add('bot');
  if (c.includes('Support')) r.add('support');

  // 2. Specific Jungle Logic (Only true junglers)
  const commonJunglers = [
    'Amumu', 'Bel\'Veth', 'Briar', 'Diana', 'Ekko', 'Elise', 'Evelynn', 'Fiddlesticks',
    'Gragas', 'Graves', 'Hecarim', 'Ivern', 'Jarvan IV', 'Jax', 'Karthus', 'Kayn', 'Kha\'Zix',
    'Kindred', 'Lee Sin', 'Lillia', 'Master Yi', 'Nidalee', 'Nocturne', 'Nunu & Willump', 'Olaf',
    'Poppy', 'Rammus', 'Rek\'Sai', 'Rengar', 'Sejuani', 'Shaco', 'Shyvana', 'Skarner', 'Taliyah',
    'Trundle', 'Udyr', 'Vi', 'Viego', 'Volibear', 'Warwick', 'Wukong', 'Zac'
  ];
  if (commonJunglers.includes(name)) r.add('jungle');

  // 3. Support Refinement (Don't show every tank as support)
  const supportTanks = ['Alistar', 'Blitzcrank', 'Braum', 'Leona', 'Nautilus', 'Pyke', 'Rakan', 'Rell', 'Taric', 'Thresh', 'Galio', 'Maokai'];
  if (supportTanks.includes(name)) r.add('support');
  if (c.includes('Tank') && !supportTanks.includes(name)) r.delete('support');

  // 4. Flex Overrides
  if (name === 'Karma' || name === 'Lux' || name === 'Morgana' || name === 'Seraphine') { r.add('support'); r.add('mid'); }
  if (name === 'Yasuo' || name === 'Yone') { r.add('mid'); r.add('top'); }
  if (name === 'Swain') { r.add('mid'); r.add('support'); r.add('bot'); }
  if (name === 'Tristana' || name === 'Lucian' || name === 'Corki') { r.add('bot'); r.add('mid'); }
  if (name === 'Tahm Kench') { r.add('support'); r.add('top'); }
  if (name === 'Vayne' || name === 'Quinn') { r.add('bot'); r.add('top'); }
  if (name === 'Senna') { r.add('support'); r.add('bot'); }
  
  return r;
};

export const ChampionSelectModal: React.FC<ChampionSelectModalProps> = ({ isOpen, onClose, onSelect, unavailableChampions }) => {
  const [search, setSearch] = useState('');
  const [selectedRole, setSelectedRole] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [selectedRange, setSelectedRange] = useState('all');
  const [sortBy, setSortBy] = useState<'name' | 'winrate' | 'pickrate'>('name');

  // Memoized Filter & Sort Logic
  const filteredChamps = useMemo(() => {
    // 1. Convert Dictionary to Array and Attach Stats
    let list = Object.entries(CHAMPION_DATA).map(([key, data]) => {
      // The stats are already embedded in data.stats now (from backend update)
      // We explicitly prefer PRO stats for sorting as requested.
      const stats = {
        name: data.name,
        winRate: data.stats?.proWinRate || 0,
        pickRate: data.stats?.proPickRate || 0, 
        roles: data.roles
      };
      return { ...data, stats };
    });

    // 2. Search Filter
    if (search) {
      const cleanSearch = search.toLowerCase().replace(/[^a-z]/g, '');
      list = list.filter(c => 
        c.name.toLowerCase().replace(/[^a-z]/g, '').includes(cleanSearch)
      );
    }

    // 3. Role Filter (Data-Driven, NOT Heuristic)
    if (selectedRole !== 'all') {
      list = list.filter(c => {
        // "roles" array from championTags.ts (Mined from DB or inferred from tags)
        return c.roles && c.roles.includes(selectedRole);
      });
    }

    // 4. Type Filter (Supports Wiki-Level Subclasses)
    if (selectedType !== 'all') {
      list = list.filter(c => c.classes && c.classes.includes(selectedType));
    }

    // 5. Range Filter
    if (selectedRange !== 'all') {
      list = list.filter(c => c.attackType === selectedRange);
    }

    // 5. Sorting
    list.sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      
      const wrA = a.stats ? a.stats.winRate : 50;
      const wrB = b.stats ? b.stats.winRate : 50;
      const prA = a.stats ? a.stats.pickRate : 0;
      const prB = b.stats ? b.stats.pickRate : 0;

      if (sortBy === 'winrate') return wrB - wrA; // Descending
      if (sortBy === 'pickrate') return prB - prA; // Descending
      
      return 0;
    });

    return list;
  }, [search, selectedRole, selectedType, selectedRange, sortBy]);

  if (!isOpen) return null;

  // Helper to get local icon path
  const getLocalIcon = (name: string) => {
    // 1. Files that KEEP their special characters/spaces (Based on public/champions dir)
    const exactMatches = [
      "Vel'Koz", 
      "Kha'Zix", 
      "Nunu & Willump",
      "Renata Glasc", 
      "Miss Fortune",
      "Tahm Kench",
      "Xin Zhao",
      "Twisted Fate",
      "Lee Sin",
      "Master Yi",
      "Jarvan IV",
      "Dr. Mundo", // Wait, log said DrMundo.png. Checking...
      "Aurelion Sol" // Log said AurelionSol.png
    ];

    // Check specific overrides based on file listing
    const overrides: Record<string, string> = {
      "Kai'Sa": "Kaisa",
      "Kog'Maw": "KogMaw",
      "Rek'Sai": "RekSai",
      "Cho'Gath": "Chogath",
      "LeBlanc": "Leblanc",
      "Bel'Veth": "Belveth",
      "Wukong": "MonkeyKing",
      "Dr. Mundo": "DrMundo",
      "Aurelion Sol": "AurelionSol",
      "Renata Glasc": "Renata", 
      "Nunu & Willump": "Nunu & Willump", // Explicitly keep
      "Vel'Koz": "Vel'Koz", // Explicitly keep
      "Kha'Zix": "Kha'Zix", // Explicitly keep
    };

    if (overrides[name]) return `/champions/${overrides[name]}.png`;

    // Default: Remove spaces/apostrophes for the rest (e.g. "Lee Sin" -> "LeeSin"?) 
    // Log check: LeeSin.png, MasterYi.png, MissFortune.png.
    // So the default cleaner IS good for spaces, just not for the specific apostrophe ones we kept.
    return `/champions/${name.replace(/[^a-zA-Z0-9]/g, '')}.png`;
  };

  // Color helper for winrates
  const getWrColor = (wr: number) => {
    if (wr >= 52) return "text-green-300 bg-green-900/80";
    if (wr <= 48) return "text-red-300 bg-red-900/80";
    return "text-gray-300 bg-gray-800/80";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-esport-dark border border-gray-700 rounded-xl w-full max-w-6xl h-[90vh] flex flex-col shadow-2xl shadow-blue-900/20 overflow-hidden">
        
        {/* Header Section */}
        <div className="p-4 border-b border-gray-800 bg-gray-900/90 flex flex-col gap-4">
          
          {/* Top Row: Search & Close */}
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                autoFocus
                type="text" 
                placeholder="Search Champion..." 
                className="w-full bg-gray-800 text-white rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-esport-gold border border-gray-700"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button onClick={onClose} className="p-3 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors">
              <X size={24} />
            </button>
          </div>

          {/* Filters Row */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            
            {/* Role Tabs */}
            <div className="flex bg-gray-800/50 p-1 rounded-lg">
              {ROLES.map(role => (
                <button
                  key={role.id}
                  onClick={() => setSelectedRole(role.id)}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all
                    ${selectedRole === role.id 
                      ? 'bg-gray-700 text-white shadow-sm' 
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'}
                  `}
                >
                  {role.icon}
                  {role.label}
                </button>
              ))}
            </div>

            <div className="flex gap-4">
                {/* Type Pills */}
                <select 
                    value={selectedType} 
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="bg-gray-800 text-sm text-gray-300 border border-gray-700 rounded-lg px-3 py-2 focus:ring-2 focus:ring-esport-gold outline-none"
                >
                    {TYPES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
                </select>

                {/* Range Filter */}
                <select 
                    value={selectedRange} 
                    onChange={(e) => setSelectedRange(e.target.value)}
                    className="bg-gray-800 text-sm text-gray-300 border border-gray-700 rounded-lg px-3 py-2 focus:ring-2 focus:ring-esport-gold outline-none"
                >
                    {RANGES.map(r => <option key={r.id} value={r.id}>{r.label}</option>)}
                </select>

                {/* Sort Dropdown */}
                <select 
                    value={sortBy} 
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="bg-gray-800 text-sm text-gray-300 border border-gray-700 rounded-lg px-3 py-2 focus:ring-2 focus:ring-esport-gold outline-none cursor-pointer"
                >
                    <option value="name" className="bg-gray-800">Sort: Name</option>
                    <option value="winrate" className="bg-gray-800">Sort: Pro Win Rate</option>
                    <option value="pickrate" className="bg-gray-800">Sort: Pro Pick Rate</option>
                </select>
            </div>
          </div>
        </div>

        {/* Grid Body */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-gray-900/30">
          <div className="grid grid-cols-5 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-3">
            {filteredChamps.map(champ => {
              const isTaken = unavailableChampions.has(champ.name);
              const wr = champ.stats ? champ.stats.winRate : 0;
              const hasStats = !!champ.stats;

              return (
                <button
                  key={champ.id}
                  disabled={isTaken}
                  onClick={() => {
                    onSelect(champ.name);
                    onClose();
                    setSearch('');
                  }}
                  className={`
                    group relative aspect-square rounded-lg overflow-hidden border-2 transition-all duration-100 flex flex-col
                    ${isTaken 
                      ? 'opacity-20 grayscale border-transparent cursor-not-allowed' 
                      : 'border-gray-800 hover:border-esport-gold hover:scale-105 hover:z-10 hover:shadow-lg hover:shadow-yellow-500/20'}
                  `}
                >
                  <img 
                    src={getLocalIcon(champ.name)} 
                    alt={champ.name}
                    className="w-full h-full object-cover"
                    loading="lazy"
                    onError={(e) => {
                      // Fallback: Hide image, show placeholder background
                      e.currentTarget.style.display = 'none';
                      e.currentTarget.parentElement?.classList.add('bg-gray-800');
                    }}
                  />
                  {/* Fallback Text for missing images */}
                  <div className="absolute inset-0 flex items-center justify-center -z-10">
                     <span className="text-[10px] text-gray-500 font-mono">NO IMG</span>
                  </div>
                  
                  {/* Real Winrate Badge (Pro WR) */}
                  {hasStats && wr > 0 && (
                     <div className={`absolute top-1 right-1 text-[9px] px-1.5 py-0.5 rounded backdrop-blur font-mono ${getWrColor(wr)}`}>
                        {wr.toFixed(1)}%
                     </div>
                  )}

                  {/* Name Overlay */}
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black via-black/80 to-transparent p-1 pt-4">
                    <p className="text-[10px] text-center text-gray-200 font-bold truncate px-1">
                      {champ.name}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};