export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
export const ROLE_ORDER = ['Top', 'Jungle', 'Mid', 'Bot', 'Support'] as const;
