import { GoogleGenAI, Type } from "@google/genai";
import { MatchContext, AnalysisResult, TeamStats, ChampionStats, AdvancedPlayerStats } from '../types';
import { formatMatchDataForAI } from './dataCollector';

// 1. Setup API Keys and Endpoints
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
const LOCAL_API_URL = "http://localhost:8000"; // Address of your Python Backend

const SYSTEM_INSTRUCTION = `You are a world-class League of Legends Esports Analyst and Coach (like LS, Caedrel, or YamatoCannon). 
Your job is to analyze live match states, draft compositions, and historical team data to predict the winner.
You understand the current meta, champion synergies, and counters deeply. 
Provide concise, data-driven insights.`;

/**
 * Fetches Team Data: Prioritizes Local Python SQL DB -> Falls back to Gemini
 */
export const fetchTeamData = async (teamName: string): Promise<TeamStats> => {

  try {
    const response = await fetch(`${LOCAL_API_URL}/api/team/${encodeURIComponent(teamName)}`);
    if (response.ok) {
      const data = await response.json();
      // Only return if valid data came back (not an error object)
      if (!data.error && !data.use_mock) {
        console.log(`✅ Loaded real data for ${teamName} from Python Backend`);
        return data as TeamStats;
      }
    }
  } catch (error) {
    console.warn(`Local API unreachable for ${teamName}. Is 'uvicorn main:app' running?`);
  }

  // B. Fallback to Gemini (The "Hallucinated/Generic" Data)
  console.log(`Falling back to Gemini for ${teamName}...`);
  try {
    const prompt = `Find the most recent competitive stats for the League of Legends team "${teamName}".
    Include their approximate win rate for the current/most recent season, 3 recent achievements, key players, and a brief playstyle description.
    RETURN JSON ONLY.`;

    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
      config: {
        tools: [{ googleSearch: {} }],
      }
    });

    let text = response.text || "";
    text = text.replace(/```json\n?|\n?```/g, "").trim();
    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');
    if (start !== -1 && end !== -1) {
      text = text.substring(start, end + 1);
    }

    return JSON.parse(text) as TeamStats;

  } catch (error) {
    console.error("Gemini fallback failed:", error);
    return {
      winRateSeason: "N/A",
      recentAchievements: ["Data unavailable"],
      keyPlayers: ["Unknown"],
      playstyle: "Standard balanced playstyle"
    };
  }
};

/**
 * Fetches Real Player Stats from Python DB
 * usage: Call this in App.tsx to replace 'getSimulatedPlayerData'
 */
export const fetchRealPlayerStats = async (playerName: string, champion: string) => {
  try {
    const url = `${LOCAL_API_URL}/api/player/${encodeURIComponent(playerName)}/champion/${encodeURIComponent(champion)}`;
    const response = await fetch(url);
    const json = await response.json();

    if (json.found && json.data) {
      return {
        winRate: `${json.data.winRate}%`,
        gamesPlayed: json.data.games, // We store games count to detect "Signature Picks"
        roleEffectiveness: json.data.mastery_tag, // "Signature Pick", "Comfort Pick"
        counterNotes: "",
        metaTier: "S" // Placeholder
      };
    }
  } catch (e) { 
    console.error("Player stat fetch failed", e); 
  }
  return null;
};
/**
 * Fetches Generic Champion Meta Info (Still uses Gemini because "Meta Tier" is subjective)
 */
export const fetchChampionStats = async (championName: string, role: string): Promise<ChampionStats> => {
  try {
    // 1. Ask Gemini
    const prompt = `Stats for LoL champ "${championName}" in ${role}. JSON: winRate (e.g. "52%"), roleEffectiveness (Short phrase e.g. "High Burst"), counterNotes, metaTier (S+/S/A/B/C/D). Keep winRate strictly numeric.`;
    
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
      config: { responseMimeType: "application/json" }
    });
    
    const stats = JSON.parse(response.text!) as ChampionStats;

    // --- STRICT FIX: Aggressive Winrate Cleaner ---
    if (stats.winRate) {
       // regex: finds the FIRST number (integer or decimal) in the string
       // e.g. "45.75% probuilds..." -> matches "45.75"
       const match = stats.winRate.match(/(\d+(\.\d+)?)/);
       
       if (match) {
           // Force it to be just the number + %
           stats.winRate = match[0] + "%";
       } else {
           // If no number found, default to N/A
           stats.winRate = "N/A";
       }
    }
    // ---------------------------------------------

    return stats;
  } catch (error) {
    return { winRate: "50%", roleEffectiveness: "Unknown", counterNotes: "-", metaTier: 'B' };
  }
};

/**
 * Analyzes the Matchup: Uses the Structured Data (from DB) to generate prediction
 */
export const analyzeMatchup = async (match: MatchContext): Promise<AnalysisResult> => {
  // 1. Try our ML Model first
  try {
    const response = await fetch(`${LOCAL_API_URL}/api/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            blueTeam: match.blueTeam.name,
            redTeam: match.redTeam.name,
            // SEND THE DRAFT DATA
            blueDraft: match.blueTeam.players.map(p => p.champion || ""), 
            redDraft: match.redTeam.players.map(p => p.champion || "")
        })
    });
    
    if (response.ok) {
        const mlData = await response.json();
        console.log("ML Prediction:", mlData);
        
        // 2. We still use Gemini to generate the "Reasoning" text (Model gives numbers, AI gives words)
        // We'll create a lighter prompt just for text generation
        const prompt = `
        Match: ${match.blueTeam.name} vs ${match.redTeam.name}.
        My Statistical Model predicts:
        - ${match.blueTeam.name} Win Chance: ${mlData.blueWin}%
        - Key Factor: ${mlData.factors.join(', ')}
        
        Write a short, exciting "Caster Analysis" explaining why this result makes sense based on their Gold Difference stats.
        RETURN JSON: { "reasoning": "string", "keyFactors": ["string"], "winConditions": {"blue": ["string"], "red": ["string"]} }
        `;
        
        // Ask Gemini to explain our Math
        const aiResponse = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: { responseMimeType: "application/json" }
        });
        
        const textData = JSON.parse(aiResponse.text!);
        
        return {
            winProbability: { blue: mlData.blueWin, red: mlData.redWin }, // Use REAL Math
            reasoning: textData.reasoning, // Use AI Words
            keyFactors: [...mlData.factors, ...textData.keyFactors],
            winConditions: textData.winConditions,
            sources: []
        };
    }
  }catch (error) {
    console.error("Analysis Error:", error);
    return {
      winProbability: { blue: 50, red: 50 },
      reasoning: "Prediction Engine Offline.",
      keyFactors: ["Error"],
      winConditions: { blue: [], red: [] },
      sources: []
    };
  }
};
export const fetchMatchupStats = async (myChamp: string, enemyChamp: string, role: string) => {
  try {
    // Clean role names (e.g. "Top Laner" -> "Top") for DB matching
    const cleanRole = role.replace(" Laner", ""); 
    
    const url = `${LOCAL_API_URL}/api/matchup/${encodeURIComponent(myChamp)}/vs/${encodeURIComponent(enemyChamp)}/role/${encodeURIComponent(cleanRole)}`;
    const response = await fetch(url);
    const json = await response.json();
    
    if (json.found && json.data) {
      return json.data; // { type: "advantage", winRate: 60, games: 12 }
    }
  } catch (e) {
    console.error("Matchup fetch failed", e);
  }
  return null;
};