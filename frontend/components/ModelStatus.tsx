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
  const draft = current ? report?.test?.selected : report?.test?.draft_and_elo;
  const elo = current ? report?.test?.elo_formula : report?.test?.elo_model;
  return <aside className="mb-6 rounded-xl border border-gray-700 bg-gray-900 p-4 text-sm" aria-live="polite">
    <p className="font-bold text-gray-200">{status === null ? 'Checking prediction engine…' : status.ready ? 'Prediction engine ready' : 'Prediction engine unavailable'}</p>
    {draft && elo ? <>
      <p className="mt-1 text-gray-400">{current ? '2025 retrospective benchmark' : 'Historical test'} · {draft.games.toLocaleString()} games</p>
      <p className="mt-1 text-gray-400">Model accuracy {(draft.accuracy * 100).toFixed(2)}% · Elo {(elo.accuracy * 100).toFixed(2)}%</p>
      <p className="mt-1 text-gray-400">Log loss {draft.log_loss.toFixed(4)} · Elo {elo.log_loss.toFixed(4)} · Lower is better</p>
      <p className="mt-1 text-xs text-gray-500">Model chosen on earlier seasons. Historical performance does not guarantee future results. Data through {report.data?.last_date?.slice(0, 10)}{status.latest_patch ? ` · Latest recorded patch ${status.latest_patch}` : ''}.</p>
    </> : status && <p className="mt-1 text-gray-400">Predictions need a trained model and a reachable backend.</p>}
  </aside>;
}
