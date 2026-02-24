import { useState, useEffect } from 'react';
import { Team } from '../../types';
import { fetchMatchupStats } from '../../services/analysisService';

export interface MatchupInfo {
  lane: {
    isCounter: boolean; // Is enemy countering me? (Red)
    isGood: boolean;    // Am I countering enemy? (Green)
    winRate: number;
    games: number;
  } | null;
  globalThreats: string[]; // List of other roles countering me (e.g. ['Jungle', 'Mid'])
}

export const useMatchups = (team: Team, enemyTeam?: Team) => {
  const [matchups, setMatchups] = useState<Record<string, MatchupInfo>>({});

  useEffect(() => {
    if (!enemyTeam) return;

    const loadMatchups = async () => {
      const newMatchups: Record<string, MatchupInfo> = {};
      
      // Iterate through MY players
      for (const player of team.players) {
        if (!player.champion) continue;
        
        let laneStats = null;
        const threats: string[] = [];

        // 1. Check vs EVERY Enemy (for Global Threat Count)
        for (const enemy of enemyTeam.players) {
           if (!enemy.champion) continue;
           
           // Is this my direct lane opponent?
           const isLaneOpponent = (player.role === enemy.role);
           
           // Fetch stats (We might need a batch API later for performance)
           const stats = await fetchMatchupStats(player.champion, enemy.champion, player.role);
           
           if (stats) {
               // Heuristic: If winrate < 48%, it's a counter.
               const isBad = stats.winRate < 48;
               const isGood = stats.winRate > 52;
               
               if (isLaneOpponent) {
                   laneStats = {
                       isCounter: isBad,
                       isGood: isGood,
                       winRate: stats.winRate,
                       games: stats.games
                   };
               }
               
               if (isBad && !isLaneOpponent) {
                   threats.push(enemy.role);
               }
           }
        }
        
        newMatchups[player.role] = {
            lane: laneStats,
            globalThreats: threats
        };
      }
      setMatchups(newMatchups);
    };

    loadMatchups();
  }, [team.players, enemyTeam?.players]);

  return matchups;
};