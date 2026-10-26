import { CHAMPION_DATA } from '../data/championTags';

// Riot champion id (e.g. "MonkeyKing") for a display name (e.g. "Wukong").
const ID_BY_NAME: Record<string, string> = Object.fromEntries(
  Object.values(CHAMPION_DATA).map(c => [c.name, c.id])
);
const ICON_FILE: Record<string, string> = { Khazix: "Kha'Zix", Nunu: 'Nunu & Willump', Velkoz: "Vel'Koz" };

export const championId = (name: string): string => ID_BY_NAME[name] ?? name.replace(/[^A-Za-z0-9]/g, '');
export const championIcon = (name: string): string => `/champions/${ICON_FILE[championId(name)] ?? championId(name)}.png`;
