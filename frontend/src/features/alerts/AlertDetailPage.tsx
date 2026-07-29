import type { ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';

import { hasRole } from '../../utils/rbac';
import { useCurrentUser } from '../../hooks/useCurrentUser';
import { useAlert } from '../../hooks/useAlerts';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { SkeletonRows } from '../../components/ui/Spinner';
import { Badge } from '../../components/ui/Badge';
import { ApiError, toUserMessage } from '../../api/client';
import { formatDateTime } from '../../utils/format';

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm text-slate-800">{children}</dd>
    </div>
  );
}

function JsonField({ value }: { value?: Record<string, unknown> | null }) {
  return value ? (
    <pre className="overflow-x-auto rounded bg-slate-50 p-2 text-xs text-slate-700">
      {JSON.stringify(value, null, 2)}
    </pre>
  ) : (
    <>—</>
  );
}

// PUBLIC_INTERFACE
export function AlertDetailPage() {
  /**
   * Render all available alert detail fields and the PlantManager conversion
   * action. Missing alerts use an empty state; other failures are retryable.
   */
  const { alertId } = useParams<{ alertId: string }>();
  const { data, loading, error, reload } = useAlert(alertId);
  const { user } = useCurrentUser();

  if (loading) {
    return (
      <div className="card" data-testid="alert-loading">
        <span className="sr-only" role="status">Loading alert</span>
        <SkeletonRows rows={7} columns={2} />
      </div>
    );
  }

  if (error) {
    const apiError = error instanceof ApiError ? error : undefined;
    if (apiError?.isNotFound) {
      return (
        <EmptyState
          title="Alert not found"
          description="This alert does not exist or may have been removed."
          action={
            <Link
              to="/alerts"
              className="rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
            >
              Back to alerts
            </Link>
          }
        />
      );
    }

    return (
      <ErrorPanel
        title="Unable to load alert"
        error={toUserMessage(error)}
        onRetry={reload}
      />
    );
  }

  if (!data) {
    return (
      <EmptyState
        title="No alert data"
        description="The server returned no content for this alert."
      />
    );
  }

  const canConvert = hasRole(user?.role, ['PlantManager']);

  return (
    <section aria-labelledby="alert-heading" className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 id="alert-heading" className="text-xl font-semibold text-slate-900">
            Alert detail
          </h1>
          <p className="mt-1 font-mono text-xs text-slate-500">{data.id}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge>{data.status}</Badge>
          <Badge>{data.priority}</Badge>
          {canConvert && (
            <Link
              to={`/alerts/${data.id}/convert`}
              className="rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
            >
              Convert to Work Order
            </Link>
          )}
        </div>
      </div>

      <div className="card p-4">
        <h2 className="text-sm font-semibold text-slate-800">Alert details</h2>
        <dl className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Equipment">
            <span className="font-mono text-xs">{data.equipment_id}</span>
          </Field>
          <Field label="Parameter">
            {data.parameter_name || data.parameter_id || '—'}
          </Field>
          <Field label="Current value">{data.current_value || '—'}</Field>
          <Field label="Breach timestamp">{formatDateTime(data.breach_timestamp)}</Field>
          <Field label="Minimum threshold">{data.min_threshold ?? '—'}</Field>
          <Field label="Maximum threshold">{data.max_threshold ?? '—'}</Field>
          <Field label="Suggested action">{data.suggested_action || '—'}</Field>
          <Field label="Why priority">{data.why_priority || '—'}</Field>
          <Field label="Issued by">{data.issuer_name || '—'}</Field>
          <Field label="Created">{formatDateTime(data.created_at)}</Field>
          <Field label="Last updated">{formatDateTime(data.updated_at)}</Field>
          <Field label="Machine details">
            <JsonField value={data.machine_details} />
          </Field>
          <Field label="Readings snapshot">
            <JsonField value={data.readings_snapshot} />
          </Field>
        </dl>
      </div>

      <Link to="/alerts" className="text-sm text-brand-700 hover:underline">
        ← Back to alerts
      </Link>
    </section>
  );
}
