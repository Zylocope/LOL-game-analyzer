import { useState, useEffect } from 'react';
import { Team } from '../../types';
import { fetchMatchupStats } from '../../services/analysisService';

export interface MatchupInfo {
  lane: { isCounter: boolean; isGood: boolean; winRate: number; games: number } | null;
  globalThreats: string[];
}

export const useMatchups = (team: Team, enemyTeam?: Team) => {
  const [matchups, setMatchups] = useState<Record<string, MatchupInfo>>({});
  const picks = JSON.stringify(team.players.map(p => [p.role, p.champion]));
  const enemies = JSON.stringify(enemyTeam?.players.map(p => [p.role, p.champion]) || []);
  useEffect(() => {
    let cancelled = false;
    setMatchups({});
    const own: [string, string | null][] = JSON.parse(picks);
    const opponents = new Map<string, string>(JSON.parse(enemies));
    Promise.all(own.map(async ([role, champion]) => {
      const enemy = opponents.get(role);
      const stats = champion && enemy ? await fetchMatchupStats(champion, enemy, role) : null;
      return [role, { lane: stats ? { isCounter: stats.winRate < 48, isGood: stats.winRate > 52,
        winRate: stats.winRate, games: stats.games } : null, globalThreats: [] }] as const;
    })).then(entries => { if (!cancelled) setMatchups(Object.fromEntries(entries)); });
    return () => { cancelled = true; };
  }, [picks, enemies]);
  return matchups;
};
