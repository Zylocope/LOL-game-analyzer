import { MatchContext, AnalysisResult, TeamStats, ChampionStats } from '../types';
import CHAMPION_STATS from '../data/championStats.json';

const LOCAL_API_URL = "http://localhost:8000"; // Address of your Python Backend
const HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2";
// Note: In a real app, use import.meta.env.VITE_HF_API_KEY
// If no key is provided, the API might be rate limited or require a key. 
// For this demo, we assume the user might provide one or we use a public limited access.
const HF_TOKEN = import.meta.env.VITE_HF_API_KEY || ""; 

/**
 * Helper to call Hugging Face Inference API
 */
async function callHuggingFace(prompt: string, maxNewTokens = 500) {
  if (!HF_TOKEN) {
      console.warn("No Hugging Face Token found (VITE_HF_API_KEY). Requests might fail.");
  }
  
  const response = await fetch(HF_API_URL, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${HF_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      inputs: `[INST] ${prompt} [/INST]`, // Mistral Instruction Format
      parameters: {
        max_new_tokens: maxNewTokens,
        temperature: 0.7,
        return_full_text: false,
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`HF API Error: ${response.statusText}`);
  }

  const result = await response.json();
  // HF returns [{ generated_text: "..." }]
  return result[0]?.generated_text || "";
}

/**
 * Helper to extract JSON from LLM text output
 */
function extractJSON(text: string) {
    try {
        const start = text.indexOf('{');
        const end = text.lastIndexOf('}');
        if (start !== -1 && end !== -1) {
            const jsonStr = text.substring(start, end + 1);
            return JSON.parse(jsonStr);
        }
    } catch (e) {
        console.warn("Failed to extract JSON from HF output", e);
    }
    return null;
}


/**
 * Fetches Team Data: Prioritizes Local Python SQL DB -> Falls back to Hugging Face
 */
export const fetchTeamData = async (teamName: string): Promise<TeamStats> => {
  try {
    const response = await fetch(`${LOCAL_API_URL}/api/team/${encodeURIComponent(teamName)}`);
    if (response.ok) {
      const data = await response.json();
      if (!data.error && !data.use_mock) {
        console.log(`✅ Loaded real data for ${teamName} from Python Backend`);
        return data as TeamStats;
      }
    }
  } catch (error) {
    console.warn(`Local API unreachable for ${teamName}.`);
  }

  console.log(`Falling back to AI for ${teamName}...`);
  try {
    const prompt = `You are a LoL Esports expert. Provide competitive stats for team "${teamName}".
    Return a strict JSON object with this format:
    {
      "winRateSeason": "approx winrate string",
      "recentAchievements": ["achievement1", "achievement2"],
      "keyPlayers": ["player1", "player2"],
      "playstyle": "brief description"
    }
    Do not add any markdown formatting or extra text.`;

    const text = await callHuggingFace(prompt, 300);
    const data = extractJSON(text);

    if (data) return data as TeamStats;
    throw new Error("Invalid JSON from AI");

  } catch (error) {
    console.error("AI fallback failed:", error);
    return {
      winRateSeason: "N/A",
      recentAchievements: ["Data unavailable"],
      keyPlayers: ["Unknown"],
      playstyle: "Standard balanced playstyle"
    };
  }
};

/**
 * Fetches layered stats for a champ:
 * 1) Player-specific (favourite)
 * 2) Global pro (7-year DB)
 * 3) Fallback handled by AI champion stats
 */
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

/**
 * Fetches Generic Champion Meta Info using AI
 */
export const fetchChampionStats = async (championName: string, role: string): Promise<ChampionStats> => {
  // 1) Prefer mined GLOBAL win rate from championStats.json
  try {
    const allEntries = Object.values(CHAMPION_STATS) as Array<{ name: string; winRate: number }>;
    const entry = allEntries.find(e => e.name === championName);
    if (entry && typeof entry.winRate === 'number') {
      const wr = entry.winRate;
      let roleEffectiveness = "Balanced globally";
      if (wr >= 52) roleEffectiveness = "Strong globally";
      else if (wr <= 48) roleEffectiveness = "Weak globally";

      let metaTier: ChampionStats['metaTier'] = 'B';
      if (wr >= 54) metaTier = 'S';
      else if (wr >= 51) metaTier = 'A';
      else if (wr <= 47) metaTier = 'C';

      return {
        winRate: `${wr.toFixed(1)}%`,
        roleEffectiveness,
        counterNotes: "-",
        metaTier,
        source: 'global',
      };
    }
  } catch (e) {
    console.warn("Global champ stats lookup failed, falling back to AI:", e);
  }

  // 2) Fallback: AI-based generic stats (labelled as AI)
  try {
    const prompt = `Provide LoL stats for champion "${championName}" in role ${role}.
    Return a strict JSON object with fields: "winRate" (e.g. "52%"), "roleEffectiveness" (short phrase), "counterNotes", "metaTier" (S/A/B/C).
    Example: {"winRate": "51%", "roleEffectiveness": "Strong Early", "counterNotes": "Weak vs CC", "metaTier": "S"}
    Do not use markdown blocks.`;

    const text = await callHuggingFace(prompt, 200);
    const stats = extractJSON(text);

    if (stats) {
       if (stats.winRate) {
           const match = stats.winRate.match(/(\d+(\.\d+)?)/);
           stats.winRate = match ? match[0] + "%" : "N/A";
       }
       return { ...(stats as ChampionStats), source: 'ai' };
    }
    throw new Error("Invalid JSON");

  } catch (error) {
    return { winRate: "50%", roleEffectiveness: "Unknown", counterNotes: "-", metaTier: 'B', source: 'ai' };
  }
};

/**
 * Analyzes the Matchup: Uses the Structured Data (from DB) to generate prediction + AI Commentary
 */
export const analyzeMatchup = async (match: MatchContext): Promise<AnalysisResult> => {
  // 1. Try our ML Model first (Priority)
  let mlData = null;
  try {
    const response = await fetch(`${LOCAL_API_URL}/api/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            blueTeam: match.blueTeam.name,
            redTeam: match.redTeam.name,
            blueDraft: match.blueTeam.players.map(p => p.champion || ""), 
            redDraft: match.redTeam.players.map(p => p.champion || "")
        })
    });
    
    if (response.ok) {
        mlData = await response.json();
    }
  } catch (error) {
      console.warn("ML Model unreachable:", error);
  }

  // If ML failed completely, return offline
  if (!mlData) {
      return {
        winProbability: { blue: 50, red: 50 },
        reasoning: "Prediction Engine Offline. Check Backend.",
        keyFactors: ["Connection Error"],
        winConditions: { blue: [], red: [] },
        sources: []
      };
  }

  // 2. Try AI for Text (Flavor)
  try {
    const prompt = `
    Match: ${match.blueTeam.name} vs ${match.redTeam.name}.
    Statistical Model predicts:
    - ${match.blueTeam.name} Win Chance: ${mlData.blueWin}%
    - Key Factor: ${mlData.factors.join(', ')}
    
    Write a short, exciting "Caster Analysis" explaining why this result makes sense.
    Return STRICT JSON: { "reasoning": "string", "keyFactors": ["string"], "winConditions": {"blue": ["string"], "red": ["string"]} }
    Do not write code blocks. Just the raw JSON string.
    `;
    
    const text = await callHuggingFace(prompt, 400);
    const textData = extractJSON(text);
    
    if (textData) {
        // Merge ML Warnings into Win Conditions for display
        const blueConds = textData.winConditions?.blue || [];
        const redConds = textData.winConditions?.red || [];
        
        if (mlData.blueWarnings) blueConds.unshift(...mlData.blueWarnings);
        if (mlData.redWarnings) redConds.unshift(...mlData.redWarnings);

        return {
            winProbability: { blue: mlData.blueWin, red: mlData.redWin },
            reasoning: textData.reasoning,
            keyFactors: [...mlData.factors, ...textData.keyFactors],
            winConditions: { blue: blueConds, red: redConds },
            sources: []
        };
    }
    throw new Error("No JSON parsed");

  } catch (error) {
    console.warn("AI Text Generation failed, using raw ML stats:", error);
    return {
        winProbability: { blue: mlData.blueWin, red: mlData.redWin },
        reasoning: `Statistical Model predicts ${mlData.blueWin > 50 ? 'Blue' : 'Red'} advantage based on historic Elo and Role integrity.`,
        keyFactors: mlData.factors,
        winConditions: { 
            blue: mlData.blueWarnings || ["Standard Play"], 
            red: mlData.redWarnings || ["Standard Play"] 
        },
        sources: []
    };
  }
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