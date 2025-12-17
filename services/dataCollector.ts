import { Team, Player, AdvancedTeamStats, AdvancedPlayerStats } from '../types';

/**
 * DATA COLLECTOR SERVICE
 * 
 * This file is responsible for structuring the data sent to the Gemini AI.
 * In a real application, replace the 'generateMock...' functions with real API calls.
 */

// Generate mock advanced stats for a team
export const collectTeamAdvancedStats = (teamName: string): AdvancedTeamStats => {
  // TODO: Replace with real API call
  const isStrong = teamName.toLowerCase().includes('t1') || teamName.toLowerCase().includes('gen') || teamName.toLowerCase().includes('blg');
  
  return {
    goldDiff15: isStrong ? "+850" : "-120",
    firstBloodRate: isStrong ? "62%" : "45%",
    dragonControl: isStrong ? "58%" : "42%",
    heraldControl: isStrong ? "60%" : "35%",
    baronControl: isStrong ? "65%" : "40%",
    aggressionRating: Math.floor(Math.random() * 40) + 40, // 40-80
    averageGameTime: "31:45"
  };
};

// Generate mock advanced stats for a player
export const collectPlayerAdvancedStats = (playerName: string, role: string): AdvancedPlayerStats => {
  // TODO: Replace with real API call
  return {
    kda: (Math.random() * 4 + 2).toFixed(1),
    dpm: Math.floor(Math.random() * 400 + 300).toString(),
    goldShare: role === 'Support' || role === 'Jungle' ? '14%' : '24%',
    visionScore: role === 'Support' ? '2.4' : role === 'Jungle' ? '1.8' : '0.8',
    csDiff15: (Math.floor(Math.random() * 20) - 5).toString(),
    kp: (Math.floor(Math.random() * 30) + 50).toString() + '%',
    lanePhase: Math.random() > 0.6 ? 'Dominant' : Math.random() > 0.3 ? 'Stable' : 'Weak'
  };
};

// Formats the full match payload for the AI
export const formatMatchDataForAI = (blueTeam: Team, redTeam: Team) => {
  return {
    match_context: {
      patch: "14.5 (Live)",
      format: "BO3",
      stage: "Regular Season"
    },
    blue_side: {
      name: blueTeam.name,
      macro_stats: blueTeam.advancedStats,
      roster: blueTeam.players.map(p => ({
        role: p.role,
        champion: p.champion,
        player_name: p.name,
        meta_tier: p.championStats?.metaTier,
        proficiency: {
          games_played: p.gamesOnChamp,
          win_rate: p.championStats?.winRate,
          is_comfort: p.isComfortPick
        },
        recent_form: p.recentForm,
        advanced_metrics: p.advancedStats
      })),
      bans: blueTeam.bans
    },
    red_side: {
      name: redTeam.name,
      macro_stats: redTeam.advancedStats,
      roster: redTeam.players.map(p => ({
        role: p.role,
        champion: p.champion,
        player_name: p.name,
        meta_tier: p.championStats?.metaTier,
        proficiency: {
          games_played: p.gamesOnChamp,
          win_rate: p.championStats?.winRate,
          is_comfort: p.isComfortPick
        },
        recent_form: p.recentForm,
        advanced_metrics: p.advancedStats
      })),
      bans: redTeam.bans
    }
  };
};