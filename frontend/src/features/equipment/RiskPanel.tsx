import { useEffect, useState } from 'react';

import { getEquipmentRisk, type EquipmentRisk } from '../../api/risk';
import { toUserMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';

const POLL_MS = 10_000;

// PUBLIC_INTERFACE
export function RiskPanel({ equipmentId }: { equipmentId: string }) {
  /**
   * Failure-risk summary for one equipment (WP4).
   *
   * Polls every 10 s; Supabase Realtime is the upgrade path (ADR-0004).
   * The score is a model estimate on benchmark-trained data, so the panel
   * says so and links the decision back to the alert workflow.
   */
  const [risk, setRisk] = useState<EquipmentRisk | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const load = () => {
      getEquipmentRisk(equipmentId, controller.signal)
        .then((data) => {
          setRisk(data);
          setError(null);
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === 'AbortError') return;
          setError(toUserMessage(err));
        });
    };
    load();
    const timer = window.setInterval(load, POLL_MS);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [equipmentId]);

  if (error) {
    return (
      <section className="card p-4 text-sm text-slate-600" aria-label="Failure risk">
        Failure risk unavailable: {error}
      </section>
    );
  }
  if (!risk) return null;

  if (risk.status === 'not_configured') {
    return (
      <section className="card p-4 text-sm text-slate-600" aria-label="Failure risk">
        <h2 className="text-sm font-semibold text-slate-800">Failure risk</h2>
        <p className="mt-1">
          Not scored. This equipment has no model asset class, or its parameters are not
          mapped to model inputs.
        </p>
      </section>
    );
  }

  const latest = risk.latest;
  const level = !latest
    ? null
    : latest.flagged
      ? { label: 'At risk', tone: 'bg-red-100 text-red-800 border-red-200' }
      : { label: 'Normal', tone: 'bg-emerald-100 text-emerald-800 border-emerald-200' };

  return (
    <section className="card space-y-3 p-4" aria-label="Failure risk">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-800">Failure risk</h2>
        {level && (
          <span
            className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${level.tone}`}
            data-testid="risk-badge"
          >
            {level.label}
          </span>
        )}
      </div>

      {!latest ? (
        <p className="text-sm text-slate-600">
          No scores yet. Scores appear once every mapped parameter has a reading.
        </p>
      ) : (
        <>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-semibold text-slate-900">
              {Math.round(latest.score * 100)}%
            </span>
            <span className="text-xs text-slate-500">
              estimated failure risk · {formatDateTime(latest.scored_at)}
            </span>
          </div>
          {latest.stage === 'shadow' && (
            <p className="rounded-md bg-amber-50 p-2 text-xs text-amber-800">
              Shadow model ({latest.model_version}): visible to Admins only and raises no
              alerts until promoted.
            </p>
          )}
          <ol className="flex h-10 items-end gap-0.5" aria-label="Recent scores, oldest first">
            {[...risk.history].reverse().map((s) => (
              <li
                key={s.id}
                title={`${Math.round(s.score * 100)}% · ${formatDateTime(s.scored_at)}`}
                className={`w-2 rounded-sm ${s.flagged ? 'bg-red-400' : 'bg-brand-300'}`}
                style={{ height: `${Math.max(4, s.score * 100)}%` }}
              />
            ))}
          </ol>
          <p className="text-xs text-slate-500">
            Model {latest.model_version}. A model estimate, not a diagnosis: record whether a
            failure was confirmed when closing the work order.
          </p>
        </>
      )}
    </section>
  );
}
