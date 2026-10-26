import { CHAMPION_DATA } from '../data/championTags';

// Riot champion id (e.g. "MonkeyKing") for a display name (e.g. "Wukong").
const ID_BY_NAME: Record<string, string> = Object.fromEntries(
  Object.values(CHAMPION_DATA).map(c => [c.name, c.id])
);
const ICON_FILE: Record<string, string> = { Khazix: "Kha'Zix", Nunu: 'Nunu & Willump', Velkoz: "Vel'Koz" };

export const championId = (name: string): string => ID_BY_NAME[name] ?? name.replace(/[^A-Za-z0-9]/g, '');
export const championIcon = (name: string): string => `/champions/${ICON_FILE[championId(name)] ?? championId(name)}.png`;

// Shown when a champion has no icon file yet (e.g. a newly released champion).
export const championFallbackIcon = (name: string): string =>
  'data:image/svg+xml;utf8,' + encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#1f2937"/>` +
    `<text x="32" y="40" font-family="Arial" font-size="22" font-weight="700" fill="#c8aa6e" text-anchor="middle">${name.slice(0, 2).toUpperCase()}</text></svg>`);

export const iconFallback = (name: string) => (e: { currentTarget: HTMLImageElement }) => {
  const img = e.currentTarget;
  if (!img.dataset.fallback) { img.dataset.fallback = '1'; img.src = championFallbackIcon(name); }
};
