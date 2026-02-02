import { Player } from '../types';
import { CHAMPION_DATA } from '../data/championTags';

// Define strict return types
interface CompositionResult {
  warnings: string[];
  strengths: string[];
}

export const analyzeComposition = (players: Player[]): CompositionResult => {
  const warnings: string[] = [];
  const strengths: string[] = [];

  // Filter empty slots and get valid champion names
  const champNames = players
    .map(p => p.champion)
    .filter((c): c is string => !!c && !!CHAMPION_DATA[c]);

  if (champNames.length < 3) return { warnings, strengths };

  // --- 1. STATISTICAL COUNTS ---
  let adCount = 0;
  let apCount = 0;
  let tankCount = 0;
  let utilityCount = 0;

  champNames.forEach(name => {
    const data = CHAMPION_DATA[name];
    if (data.tags.includes('ad')) adCount++;
    if (data.tags.includes('ap')) apCount++;
    if (data.tags.includes('tank')) tankCount++;
    if (data.tags.includes('utility')) utilityCount++;
  });

  // --- 2. WARNING RULES (Clean Text) ---
  if (adCount >= 4) warnings.push("HEAVY PHYSICAL DMG");
  if (apCount >= 4) warnings.push("HEAVY MAGIC DMG");
  if (tankCount === 0 && champNames.length === 5) warnings.push("NO FRONTLINE");
  if (utilityCount === 0 && champNames.length === 5) warnings.push("LOW UTILITY");

  // --- 3. COMBO RULES (Specific Synergies) ---
  const namesSet = new Set(champNames);

  // Yasuo Synergies (Knockups)
  if (namesSet.has("Yasuo") || namesSet.has("Yone")) {
    const knockups = ["Malphite", "Diana", "Ornn", "Gragas", "Janna", "Alistar", "Rakan", "Nautilus", "Vi", "Wukong"];
    const hasKnockup = champNames.some(c => knockups.includes(c));
    if (hasKnockup) strengths.push("KNOCKUP COMBO");
    else if (champNames.length >= 4) warnings.push("YASUO NEEDS KNOCKUPS");
  }

  // Xayah + Rakan
  if (namesSet.has("Xayah") && namesSet.has("Rakan")) {
    strengths.push("LOVERS DUO");
  }

  // Global Ultimates
  const globals = ["Karthus", "Soraka", "Shen", "Galio", "Ezreal", "Jinx", "Senna", "Gangplank"];
  const globalCount = champNames.filter(c => globals.includes(c)).length;
  if (globalCount >= 2) strengths.push("GLOBAL PRESENCE");

  // Protect the Carry
  const hypers = ["Kog'Maw", "Jinx", "Twitch", "Zeri"];
  const enchanters = ["Lulu", "Janna", "Yuumi", "Milio", "Soraka"];
  if (champNames.some(c => hypers.includes(c)) && champNames.some(c => enchanters.includes(c))) {
    strengths.push("HYPERCARRY SETUP");
  }

  return { warnings, strengths };
};