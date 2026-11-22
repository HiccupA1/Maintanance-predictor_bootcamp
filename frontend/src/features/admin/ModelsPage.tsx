import { useCallback, useEffect, useState } from 'react';

import { toUserMessage } from '../../api/client';
import {
  getModelDrift,
  getModelEvaluation,
  listModels,
  setModelStage,
  type ModelDrift,
  type ModelEvaluation,
  type ModelStage,
  type ModelVersion,
  type WarningStats,
} from '../../api/models';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { SkeletonRows } from '../../components/ui/Spinner';
import { formatDateTime } from '../../utils/format';

const pct = (value: number | null | undefined) =>
  value == null ? '—' : `${Math.round(value * 100)}%`;

function StatsRow({ label, stats }: { label: string; stats: WarningStats }) {
  return (
    <tr>
      <th scope="row" className="py-1 pr-3 text-left font-medium">
        {label}
      </th>
      <td className="px-2">{pct(stats.precision)}</td>
      <td className="px-2">
        {pct(stats.recall)} ({stats.failures_detected}/{stats.failures})
      </td>
      <td className="px-2">
        {stats.true_positive} / {stats.false_positive} / {stats.pending}
      </td>
      <td className="px-2">
        {stats.median_lead_hours == null ? '—' : `${stats.median_lead_hours} h`}
      </td>
    </tr>
  );
}

function ModelReview({ model }: { model: ModelVersion }) {
  const [evaluation, setEvaluation] = useState<ModelEvaluation | null>(null);
  const [drift, setDrift] = useState<ModelDrift | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      getModelEvaluation(model.id, controller.signal),
      getModelDrift(model.id, controller.signal),
    ])
      .then(([e, d]) => {
        setEvaluation(e);
        setDrift(d);
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        setError(toUserMessage(err));
      });
    return () => controller.abort();
  }, [model.id]);

  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!evaluation || !drift) return <SkeletonRows rows={2} columns={3} />;

  const driftedFeatures = Object.entries(drift.features).filter(([, v]) => v.level !== 'stable');

  return (
    <div className="space-y-3 text-sm" data-testid={`review-${model.version}`}>
      <div>
        <h3 className="font-semibold">
          Shadow evaluation · last {evaluation.window_days} days, {evaluation.horizon_days}-day
          horizon
        </h3>
        <p className="text-xs text-slate-500">
          {evaluation.scores} scores on {evaluation.equipment} machines. Ground truth: work orders
          closed with a confirmed failure.
        </p>
        <table className="mt-2 text-xs">
          <thead>
            <tr className="text-left text-slate-500">
              <th />
              <th className="px-2">Precision</th>
              <th className="px-2">Recall</th>
              <th className="px-2">TP / FP / pending</th>
              <th className="px-2">Median lead</th>
            </tr>
          </thead>
          <tbody>
            <StatsRow label="This model" stats={evaluation.model} />
            <StatsRow label="Threshold alerts" stats={evaluation.threshold_alerts} />
          </tbody>
        </table>
      </div>
      <div>
        <h3 className="font-semibold">
          Drift · last {drift.window_days} days: <Badge>{drift.status.replace('_', ' ')}</Badge>
        </h3>
        {drift.score && (
          <p className="text-xs text-slate-500">
            Score PSI {drift.score.psi} ({drift.score.level}) over {drift.samples} scores.
          </p>
        )}
        {driftedFeatures.length > 0 && (
          <ul className="mt-1 list-disc pl-5 text-xs">
            {driftedFeatures.map(([name, v]) => (
              <li key={name}>
                {name}: PSI {v.psi} ({v.level})
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

// PUBLIC_INTERFACE
export function ModelsPage() {
  /**
   * Admin model registry (WP4/WP5): review shadow evaluation and drift, then
   * promote, demote or retire versions. Stage changes are audited server-side.
   */
  const [models, setModels] = useState<ModelVersion[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    listModels()
      .then(setModels)
      .catch((err: unknown) => setError(err));
  }, []);

  useEffect(load, [load]);

  const change = async (model: ModelVersion, stage: ModelStage) => {
    const verb = { active: 'Activate', shadow: 'Move to shadow', retired: 'Retire' }[stage];
    if (!window.confirm(`${verb} ${model.version}?`)) return;
    setBusy(model.id);
    setActionError(null);
    try {
      await setModelStage(model.id, stage);
      load();
    } catch (err) {
      setActionError(toUserMessage(err));
    } finally {
      setBusy(null);
    }
  };

  if (error) return <ErrorPanel title="Unable to load models" error={error} onRetry={load} />;
  if (!models) return <SkeletonRows rows={4} columns={4} />;

  return (
    <section aria-labelledby="models-heading" className="space-y-4">
      <div>
        <h1 id="models-heading" className="text-xl font-semibold text-slate-900">
          Models
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          New versions start in shadow: scored and evaluated, never alerting. Activate only after
          the shadow evaluation beats threshold alerts on confirmed failures.
        </p>
      </div>
      {actionError && <ErrorPanel title="Stage change failed" error={actionError} />}
      {models.length === 0 ? (
        <EmptyState
          title="No models registered"
          description="Register a trained artifact with ml/scripts/register_model.py."
        />
      ) : (
        models.map((model) => (
          <article key={model.id} className="card space-y-3 p-4">
            <header className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="font-semibold">
                  {model.version} <Badge>{model.stage}</Badge>
                </h2>
                <p className="text-xs text-slate-500">
                  {model.asset_class} · alert threshold {pct(model.threshold)} · registered{' '}
                  {formatDateTime(model.created_at)}
                  {model.stage_changed_by &&
                    ` · stage set by ${model.stage_changed_by} ${formatDateTime(model.stage_changed_at)}`}
                </p>
              </div>
              <div className="flex gap-2">
                {model.stage === 'shadow' && (
                  <Button loading={busy === model.id} onClick={() => void change(model, 'active')}>
                    Activate
                  </Button>
                )}
                {model.stage === 'active' && (
                  <Button loading={busy === model.id} onClick={() => void change(model, 'shadow')}>
                    Move to shadow
                  </Button>
                )}
                {model.stage !== 'retired' && (
                  <Button loading={busy === model.id} onClick={() => void change(model, 'retired')}>
                    Retire
                  </Button>
                )}
              </div>
            </header>
            {model.stage !== 'retired' && <ModelReview model={model} />}
          </article>
        ))
      )}
    </section>
  );
}
