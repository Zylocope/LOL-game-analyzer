import { GoogleGenAI, Type } from "@google/genai";
import { MatchContext, AnalysisResult, TeamStats, ChampionStats } from '../types';
import { formatMatchDataForAI } from './dataCollector';

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

// Constants for prompts to ensure consistency
const SYSTEM_INSTRUCTION = `You are a world-class League of Legends Esports Analyst and Coach (like LS, Caedrel, or YamatoCannon). 
Your job is to analyze live match states, draft compositions, and historical team data to predict the winner.
You understand the current meta, champion synergies, and counters deeply. 
Provide concise, data-driven insights.`;

export const fetchTeamData = async (teamName: string): Promise<TeamStats> => {
  try {
    const prompt = `Find the most recent competitive stats for the League of Legends team "${teamName}".
    Include their approximate win rate for the current/most recent season, 3 recent achievements (e.g. tournament placements), key players to watch, and a brief 1-sentence description of their playstyle (e.g. "Early game aggression", "Late game scaling").
    
    If the team is not a professional team or unknown, provide generic placeholder stats for a "Challenger Tier Team".
    
    RETURN JSON ONLY. The response must be a valid JSON object with the following structure:
    {
      "winRateSeason": "string",
      "recentAchievements": ["string"],
      "keyPlayers": ["string"],
      "playstyle": "string"
    }`;

    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
      config: {
        tools: [{ googleSearch: {} }],
        // responseMimeType and responseSchema are NOT allowed with googleSearch
      }
    });

    let text = response.text;
    if (!text) throw new Error("No data returned");

    // Clean up markdown code blocks if present
    text = text.replace(/```json\n?|\n?```/g, "").trim();
    // Extract JSON object
    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');
    if (start !== -1 && end !== -1) {
      text = text.substring(start, end + 1);
    }

    return JSON.parse(text) as TeamStats;

  } catch (error) {
    console.error("Error fetching team data:", error);
    return {
      winRateSeason: "N/A",
      recentAchievements: ["Data unavailable"],
      keyPlayers: ["Unknown"],
      playstyle: "Standard balanced playstyle"
    };
  }
};

export const fetchChampionStats = async (championName: string, role: string): Promise<ChampionStats> => {
  try {
    const prompt = `Provide brief competitive stats for League of Legends champion "${championName}" in the ${role} role.
    Include:
    - winRate: Approximate win rate in recent pro play (e.g., "51%").
    - roleEffectiveness: Tier/Effectiveness (e.g., "S-Tier", "Situational").
    - counterNotes: 3-5 words on what they counter or struggle against.
    - metaTier: The current meta tier strictly as one of: 'S+', 'S', 'A', 'B', 'C', 'D'.
    `;

    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            winRate: { type: Type.STRING },
            roleEffectiveness: { type: Type.STRING },
            counterNotes: { type: Type.STRING },
            metaTier: { type: Type.STRING, enum: ['S+', 'S', 'A', 'B', 'C', 'D'] }
          }
        }
      }
    });

    const text = response.text;
    if (!text) throw new Error("No stats");
    return JSON.parse(text) as ChampionStats;
  } catch (error) {
    return {
      winRate: "N/A",
      roleEffectiveness: "Unknown",
      counterNotes: "No data available",
      metaTier: 'B'
    };
  }
};

export const analyzeMatchup = async (match: MatchContext): Promise<AnalysisResult> => {
  try {
    // Use the data collector to format the strict JSON payload
    const structuredData = formatMatchDataForAI(match.blueTeam, match.redTeam);

    const prompt = `Analyze this League of Legends matchup using the provided structured data.
    
    DATA PAYLOAD:
    ${JSON.stringify(structuredData, null, 2)}
    
    CRITICAL ANALYSIS POINTS:
    1. **Early Game vs Scaling**: Compare 'avg_game_time' and 'gold_diff_15'. If a team has high 'aggression_rating' and 'gold_diff_15' but the other has better scaling champs, how does the early game play out?
    2. **Lane Matchups**: Check 'lane_phase' metrics (Dominant/Weak) for each lane. Identify volatile lanes.
    3. **Win Conditions**: correlate 'dragon_control' / 'baron_control' stats with the draft.
    4. **Player Form**: Factor in 'recent_form' and 'advanced_metrics' (DPM, KDA). A 'Hot' player with high DPM should be a primary win condition.
    
    Provide a prediction percentage (must sum to 100), detailed reasoning, key factors, and win conditions.`;

    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            winProbability: {
              type: Type.OBJECT,
              properties: {
                blue: { type: Type.NUMBER, description: "Integer percentage 0-100" },
                red: { type: Type.NUMBER, description: "Integer percentage 0-100" }
              }
            },
            reasoning: { type: Type.STRING },
            keyFactors: { type: Type.ARRAY, items: { type: Type.STRING } },
            winConditions: {
              type: Type.OBJECT,
              properties: {
                blue: { type: Type.ARRAY, items: { type: Type.STRING } },
                red: { type: Type.ARRAY, items: { type: Type.STRING } }
              }
            }
          }
        }
      }
    });

    const text = response.text;
    if (!text) throw new Error("No analysis generated");
    
    const result = JSON.parse(text);

    return {
      ...result,
      sources: []
    };

  } catch (error) {
    console.error("Error analyzing matchup:", error);
    return {
      winProbability: { blue: 50, red: 50 },
      reasoning: "Analysis failed. Please try again.",
      keyFactors: ["Unknown error"],
      winConditions: { blue: [], red: [] },
      sources: []
    };
  }
};