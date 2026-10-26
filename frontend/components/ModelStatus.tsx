import React, { useEffect, useState } from 'react';
import { API_URL } from '../services/api';

export function ModelStatus() {
  const [status, setStatus] = useState<any>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_URL}/api/model`, { signal: controller.signal })
      .then(response => { if (!response.ok) throw new Error(); return response.json(); })
      .then(setStatus).catch(() => { if (!controller.signal.aborted) setStatus({ ready: false }); });
    return () => controller.abort();
  }, []);
  const report = status?.evaluation;
  const current = report?.version === 'v6_elo_corrections';
  const holdout = status?.holdout;
  const draft = holdout ? holdout.model : current ? report?.test?.selected : report?.test?.draft_and_elo;
  const elo = holdout ? holdout.elo : current ? report?.test?.elo_formula : report?.test?.elo_model;
  const throughRaw = (status?.ratings_through || report?.data?.last_date || '').slice(0, 10);
  const through = throughRaw ? new Date(`${throughRaw}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }) : '';
  return <aside className="mb-6 rounded-xl border border-gray-700 bg-gray-900 p-4 text-sm" aria-live="polite">
    <p className="font-bold text-gray-200">{status === null ? 'Checking prediction engine…' : status.ready ? 'Prediction engine ready' : 'Prediction engine unavailable'}</p>
    {draft && elo ? <>
      <p className="mt-1 text-gray-400">
        {holdout ? `Tested on ${draft.games.toLocaleString()} pro games from 2026` : `Tested on ${draft.games.toLocaleString()} past pro games`}:
        {' '}right {(draft.accuracy * 100).toFixed(1)}% of the time (team ratings alone: {(elo.accuracy * 100).toFixed(1)}%).
      </p>
      {through && <p className="mt-1 text-xs text-gray-500">Based on pro games up to {through}{status.latest_patch ? ` · patch ${status.latest_patch}` : ''}.</p>}
    </> : status && <p className="mt-1 text-gray-400">Predictions are unavailable right now. Please try again in a minute.</p>}
  </aside>;
}
