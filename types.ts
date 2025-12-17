export type Role = 'Top' | 'Jungle' | 'Mid' | 'Bot' | 'Support';

export interface ChampionStats {
  winRate: string;
  roleEffectiveness: string;
  counterNotes: string;
  metaTier?: 'S+' | 'S' | 'A' | 'B' | 'C' | 'D';
}

export interface AdvancedPlayerStats {
  kda: string;           // Kill/Death/Assist Ratio
  dpm: string;           // Damage Per Minute (e.g., "550")
  goldShare: string;     // % of team gold (e.g., "24%")
  visionScore: string;   // Vision Score per minute (e.g., "1.5")
  csDiff15: string;      // CS Difference at 15 min (e.g., "+12")
  kp: string;            // Kill Participation %
  lanePhase: 'Dominant' | 'Stable' | 'Weak'; // Early game laning prowess
}

export interface Player {
  name: string;
  role: Role;
  champion?: string;
  championStats?: ChampionStats;
  
  // High-Level Metrics
  recentForm?: 'Hot' | 'Stable' | 'Cold'; 
  gamesOnChamp?: number; 
  isComfortPick?: boolean; 
  
  // Granular Data (New)
  advancedStats?: AdvancedPlayerStats;
}

export interface AdvancedTeamStats {
  goldDiff15: string;      // Average Gold Diff at 15 min (e.g., "+1.2k")
  firstBloodRate: string;  // % (e.g., "60%")
  dragonControl: string;   // % (e.g., "55%")
  heraldControl: string;   // % (e.g., "40%")
  baronControl: string;    // % (e.g., "65%")
  aggressionRating: number; // 0-100 (Early game skirmish frequency)
  averageGameTime: string; // e.g., "32:00"
}

export interface Team {
  id: 'blue' | 'red';
  name: string;
  players: Player[];
  bans: string[];
  stats?: TeamStats;
  // Deep Data (New)
  advancedStats?: AdvancedTeamStats;
}

export interface TeamStats {
  winRateSeason: string;
  recentAchievements: string[];
  keyPlayers: string[];
  playstyle: string;
}

export interface AnalysisResult {
  winProbability: {
    blue: number;
    red: number;
  };
  reasoning: string;
  keyFactors: string[];
  winConditions: {
    blue: string[];
    red: string[];
  };
  sources: Array<{ title: string; uri: string }>;
}

export interface MatchContext {
  blueTeam: Team;
  redTeam: Team;
  gameTime?: string; 
  goldDiff?: number;
}