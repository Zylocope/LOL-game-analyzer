import { MatchContext, AnalysisResult, TeamStats, ChampionStats } from '../types';
import CHAMPION_STATS from '../data/championStats.json';
import { API_URL as LOCAL_API_URL, ROLE_ORDER } from './api';

function normalizeWinPercent(value: unknown): number | null {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }

  const percent = value <= 1 ? value * 100 : value;
  return Math.round(Math.max(0, Math.min(100, percent)));
}

function normalizePredictionPayload(data: any) {
  const blue = normalizeWinPercent(data?.blueWinChance ?? data?.blueWin);
  const red = normalizeWinPercent(data?.redWinChance ?? data?.redWin);

  if (blue === null && red === null) {
    return null;
  }

  if (blue === null) {
    return { blueWin: 100 - red!, redWin: red!, factors: data?.factors || [] };
  }

  if (red === null) {
    return { blueWin: blue, redWin: 100 - blue, factors: data?.factors || [] };
  }

  return { blueWin: blue, redWin: red, factors: data?.factors || [] };
}

function buildLocalMatchAnalysis(match: MatchContext, mlData: { blueWin: number; redWin: number; factors: string[] }): AnalysisResult {
  const blueFavored = mlData.blueWin >= mlData.redWin;
  const favoredName = blueFavored ? match.blueTeam.name : match.redTeam.name;
  const favoredPercent = blueFavored ? mlData.blueWin : mlData.redWin;
  const edge = Math.abs(mlData.blueWin - mlData.redWin);
  const confidence = edge >= 20 ? "clear" : edge >= 10 ? "moderate" : "narrow";
  const factors = mlData.factors?.length ? mlData.factors : ["Model found a close draft with no dominant single factor."];

  return {
    winProbability: { blue: mlData.blueWin, red: mlData.redWin },
    reasoning: `${favoredName} has a ${confidence} statistical edge at ${favoredPercent}% based on the selected statistical model and historical results.`,
    keyFactors: factors,
    winConditions: {
      blue: [
        mlData.blueWin >= mlData.redWin ? "Play through the model-favored lanes and protect the draft advantage." : "Stabilize early lanes and avoid giving over matchup tempo.",
        "Force fights around completed item timings."
      ],
      red: [
        mlData.redWin >= mlData.blueWin ? "Play through the model-favored lanes and protect the draft advantage." : "Stabilize early lanes and avoid giving over matchup tempo.",
        "Trade objectives cleanly when direct fights are unfavorable."
      ],
    },
    sources: []
  };
}


export const fetchTeamData = async (teamName: string): Promise<TeamStats> => {
  try {
    const response = await fetch(`${LOCAL_API_URL}/api/team/${encodeURIComponent(teamName)}`);
    if (response.ok) {
      const data = await response.json();
      if (!data.error && !data.use_mock) return data;
    }
  } catch { /* Render an explicit unavailable state. */ }
  return { winRateSeason: 'N/A', recentAchievements: ['Data unavailable'], keyPlayers: [], playstyle: 'Unavailable' };
};

export const fetchRealPlayerStats = async (playerName: string, champion: string, role?: string) => {
  try {
    // 1) Player-specific stats
    const url = `${LOCAL_API_URL}/api/player/${encodeURIComponent(playerName)}/champion/${encodeURIComponent(champion)}`;
    const response = await fetch(url);
    const json = await response.json();

    if (json.found && json.data) {
      const games: number = json.data.games;
      const wr: number = json.data.winRate;

      // If favourite sample is too small in games played, do NOT treat as favourite.
      // Always fall back to champion-level pro/global stats when games < 5.
      const isWeakSample = games < 5;

      if (!isWeakSample) {
        return {
          winRate: `${wr}%`,
          gamesPlayed: games,
          roleEffectiveness: json.data.mastery_tag,
          counterNotes: "",
          metaTier: "S",
          source: 'player' as const,
        };
      }
      // else: deliberately skip to champion-level pro stats below
    }

    // 2) Global pro stats for this champion+role
    if (role) {
      const champUrl = `${LOCAL_API_URL}/api/champion/${encodeURIComponent(champion)}/role/${encodeURIComponent(role)}`;
      const champRes = await fetch(champUrl);
      const champJson = await champRes.json();

      if (champJson.found && champJson.data) {
        return {
          winRate: `${champJson.data.winRate}%`,
          gamesPlayed: champJson.data.games,
          roleEffectiveness: champJson.data.mastery_tag, // "Global Pro"
          counterNotes: "",
          metaTier: "S",
          source: 'pro' as const,
        };
      }
    }
  } catch (e) { 
    console.error("Player/champion stat fetch failed", e); 
  }
  return null;
};

export const fetchChampionStats = async (championName: string, role: string): Promise<ChampionStats> => {
  const entry = Object.values(CHAMPION_STATS).find(e => e.name === championName);
  if (!entry || !Number.isFinite(entry.winRate)) {
    return { winRate: 'N/A', roleEffectiveness: 'Data unavailable', counterNotes: '-', source: 'global' };
  }
  return { winRate: `${entry.winRate.toFixed(1)}%`, roleEffectiveness: 'Historical global average',
           counterNotes: '-', source: 'global' };
};

export const analyzeMatchup = async (match: MatchContext): Promise<AnalysisResult> => {
  const response = await fetch(`${LOCAL_API_URL}/api/predict`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ blueTeam: match.blueTeam.name, redTeam: match.redTeam.name,
      patch: match.patch || undefined,
      bluePlayers: ROLE_ORDER.map(role => match.blueTeam.players.find(p => p.role === role)?.name || ''),
      redPlayers: ROLE_ORDER.map(role => match.redTeam.players.find(p => p.role === role)?.name || ''),
      blueDraft: ROLE_ORDER.map(role => match.blueTeam.players.find(p => p.role === role)?.champion || ''),
      redDraft: ROLE_ORDER.map(role => match.redTeam.players.find(p => p.role === role)?.champion || '') })
  });
  if (!response.ok) {
    if (response.status === 422) {
      const error = await response.json().catch(() => ({}));
      const invalidPatch = Array.isArray(error.detail) && error.detail.some((item: any) => item.loc?.includes('patch'));
      throw new Error(invalidPatch ? 'Use a patch such as 15.01, or leave it blank for the latest recorded patch.' : 'Complete a valid draft with ten different champions.');
    }
    throw new Error('Prediction engine unavailable. Check the backend and trained model.');
  }
  const data = normalizePredictionPayload(await response.json());
  if (!data) throw new Error('Prediction engine returned an invalid result.');
  return buildLocalMatchAnalysis(match, data);
};

export const fetchMatchupStats = async (myChamp: string, enemyChamp: string, role: string) => {
  try {
    const cleanRole = role.replace(" Laner", ""); 
    const url = `${LOCAL_API_URL}/api/matchup/${encodeURIComponent(myChamp)}/vs/${encodeURIComponent(enemyChamp)}/role/${encodeURIComponent(cleanRole)}`;
    const response = await fetch(url);
    const json = await response.json();
    if (json.found && json.data) {
      return json.data; 
    }
  } catch (e) {
    console.error("Matchup fetch failed", e);
  }
  return null;
};
