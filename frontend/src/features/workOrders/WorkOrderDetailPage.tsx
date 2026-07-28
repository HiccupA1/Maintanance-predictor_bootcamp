import { Link, useParams } from 'react-router-dom';

import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { PriorityBadge, StatusBadge } from '../../components/ui/Badge';
import { SkeletonRows } from '../../components/ui/Spinner';
import { ApiError } from '../../api/client';
import { formatDateTime } from '../../utils/format';
import { useWorkOrder } from '../../hooks/useWorkOrders';

/** Render a labelled read-only field. */
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm text-slate-800">{children}</dd>
    </div>
  );
}

// PUBLIC_INTERFACE
export function WorkOrderDetailPage() {
  /**
   * Work Order detail screen.
   *
   * Shows identity, linked alert, equipment, priority, status, due date,
   * closure fields and the spare parts checklist. Handles loading, not-found
   * (empty), error and success states.
   */
  const { id } = useParams<{ id: string }>();
  const { data, loading, error, reload } = useWorkOrder(id);

  if (loading) {
    return (
      <div className="card" data-testid="work-order-loading">
        <span className="sr-only" role="status">
          Loading work order
        </span>
        <SkeletonRows rows={6} columns={2} />
      </div>
    );
  }

  if (error) {
    const apiError = error instanceof ApiError ? error : undefined;
    if (apiError?.isNotFound) {
      return (
        <EmptyState
          title="Work order not found"
          description="This work order does not exist or may have been removed."
          action={
            <Link
              to="/work-orders"
              className="rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
            >
              Back to work orders
            </Link>
          }
        />
      );
    }
    return (
      <ErrorPanel title="Unable to load work order" error={error} onRetry={reload} />
    );
  }

  if (!data) {
    return (
      <EmptyState
        title="No work order data"
        description="The server returned no content for this work order."
      />
    );
  }

  return (
    <section aria-labelledby="work-order-heading" className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 id="work-order-heading" className="text-xl font-semibold text-slate-900">
            Work order
          </h1>
          <p className="mt-1 font-mono text-xs text-slate-500">{data.id}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={data.status} />
          <PriorityBadge priority={data.priority} />
          {data.status === 'OPEN' && (
            <Link
              to={`/work-orders/${data.id}/edit`}
              className="rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
            >
              Edit
            </Link>
          )}
        </div>
      </div>

      <div className="card p-4">
        <h2 className="text-sm font-semibold text-slate-800">Details</h2>
        <dl className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Description">{data.description}</Field>
          <Field label="Equipment">
            <span className="font-mono text-xs">{data.equipment_id}</span>
          </Field>
          <Field label="Source alert">
            <span className="font-mono text-xs">{data.alert_id}</span>
          </Field>
          <Field label="Issued by">{data.issuer_name || '—'}</Field>
          <Field label="Due">{formatDateTime(data.due_at)}</Field>
          <Field label="Created">{formatDateTime(data.created_at)}</Field>
          <Field label="Last updated">{formatDateTime(data.updated_at)}</Field>
          <Field label="Closed">{formatDateTime(data.closed_at)}</Field>
          <Field label="Resolution notes">{data.resolution_notes || '—'}</Field>
          <Field label="Root cause / failure code">{data.root_cause || '—'}</Field>
        </dl>
      </div>

      <div className="card p-4">
        <h2 className="text-sm font-semibold text-slate-800">Spare parts</h2>
        {data.parts.length === 0 ? (
          <p className="mt-2 text-sm text-slate-600">
            No spare part lines recorded yet. At least one line (which may be
            &ldquo;N/A&rdquo;) is required before closure.
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-slate-100">
            {data.parts.map((part) => (
              <li key={part.id} className="flex flex-wrap items-center gap-3 py-2 text-sm">
                <span className="font-medium text-slate-800">{part.part_name}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    part.used
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {part.used ? 'Used' : 'Not used'}
                </span>
                {part.notes && <span className="text-slate-600">{part.notes}</span>}
              </li>
            ))}
          </ul>
        )}
      </div>

      <p>
        <Link to="/work-orders" className="text-sm text-brand-700 hover:underline">
          ← Back to work orders
        </Link>
      </p>
    </section>
  );
}
