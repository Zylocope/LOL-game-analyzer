export const SYNERGIES: Record<string, string[]> = {
  // Duo Bot Synergies
  "Xayah": ["Rakan"],
  "Rakan": ["Xayah"],
  "Lucian": ["Nami", "Braum", "Milio"],
  "Nami": ["Lucian", "Draven"],
  "Kog'Maw": ["Lulu", "Milio", "Janna"],
  "Lulu": ["Kog'Maw", "Jinx", "Twitch", "Zeri"],
  "Zeri": ["Yuumi", "Lulu"],
  "Yuumi": ["Zeri", "Ezreal", "Twitch"],
  "Samira": ["Nautilus", "Rell", "Alistar", "Leona"],
  "Yasuo": ["Malphite", "Diana", "Gragas", "Yone", "Alister", "Rakan", "Lee Sin"],
  "Yone": ["Yasuo", "Diana", "Rell"],
  
  // Jungle/Mid Synergies
  "Lee Sin": ["Leblanc", "Ahri", "Yasuo", "Orianna"],
  "Sejuani": ["Renekton", "Jax", "Yone", "Sylas", "Irelia"], // Melee synergy
  "Viego": ["Lissandra", "Ahri", "Annie"], // CC setup for resets
  
  // Wombo Combos
  "Malphite": ["Yasuo", "Orianna", "Miss Fortune"],
  "Orianna": ["Malphite", "Rengar", "Jarvan IV", "Zac", "Nocturne"],
  "Jarvan IV": ["Orianna", "Galio", "Rumble"],
  "Galio": ["Jarvan IV", "Camille", "Pantheon"],
  "Camille": ["Galio", "Sejuani", "Twisted Fate"],
  
  // Global/Pick
  "Twisted Fate": ["Nocturne", "Shen", "Galio", "Camille"],
  "Nocturne": ["Twisted Fate", "Shen", "Orianna"],
  "Shen": ["Nocturne", "Twitch", "Evelynn"]
};