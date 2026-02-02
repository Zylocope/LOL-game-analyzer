import { useState, useEffect } from 'react';
import { Team } from '../../types';
import { fetchMatchupStats } from '../../services/geminiService';

export const useMatchups = (team: Team, enemyTeam?: Team) => {
  const [matchups, setMatchups] = useState<Record<string, any>>({});

  useEffect(() => {
    if (!enemyTeam) return;

    const loadMatchups = async () => {
      const newMatchups: Record<string, any> = {};
      
      for (const player of team.players) {
        if (!player.champion) continue;
        
        const enemy = enemyTeam.players.find(p => p.role === player.role);
        if (!enemy?.champion) continue;

        // Fetch Stats
        const stats = await fetchMatchupStats(player.champion, enemy.champion, player.role);
        if (stats) {
          newMatchups[player.role] = stats;
        }
      }
      setMatchups(newMatchups);
    };

    loadMatchups();
  }, [team.players, enemyTeam?.players]); // Re-run when players/champs change

  return matchups;
};