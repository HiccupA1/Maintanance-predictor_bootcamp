import { Link, useParams } from 'react-router-dom';

import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { PriorityBadge, StatusBadge } from '../../components/ui/Badge';
import { SkeletonRows } from '../../components/ui/Spinner';
import { ApiError } from '../../api/client';
import { useWorkOrder } from '../../hooks/useWorkOrders';
import { formatDateTime } from '../../utils/format';

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
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
   * Work-order detail screen (aligned to live Supabase schema).
   *
   * This view renders only fields that exist in the reconciled backend contract:
   * title, description, status/priority, equipment, assigned_to/closed_by, timestamps.
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
      <ErrorPanel
        title="Unable to load work order"
        error={error}
        onRetry={reload}
      />
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
          <h1
            id="work-order-heading"
            className="text-xl font-semibold text-slate-900"
          >
            Work order {data.work_order_number}
          </h1>
          <p className="mt-1 text-sm font-medium text-slate-800">{data.title}</p>
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
          <Field label="Equipment">
            {data.equipment_name || data.equipment_id || '—'}
          </Field>
          <Field label="Assigned to">{data.assigned_to || '—'}</Field>
          <Field label="Closed by">{data.closed_by || '—'}</Field>
          <Field label="Created">{formatDateTime(data.created_at)}</Field>
          <Field label="Last updated">{formatDateTime(data.updated_at)}</Field>
          <Field label="Description">{data.description || '—'}</Field>
        </dl>
      </div>

      <p>
        <Link
          to="/work-orders"
          className="text-sm text-brand-700 hover:underline"
        >
          ← Back to work orders
        </Link>
      </p>
    </section>
  );
}
