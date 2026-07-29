import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { PriorityBadge, StatusBadge } from '../../components/ui/Badge';
import { SkeletonRows } from '../../components/ui/Spinner';
import { ApiError } from '../../api/client';
import { useCurrentUser } from '../../hooks/useCurrentUser';
import { useUpdateWorkOrder, useWorkOrder } from '../../hooks/useWorkOrders';
import type { WorkOrderPartLineInput } from '../../types/workOrders';
import { formatDateTime } from '../../utils/format';
import { SparePartsChecklist } from './SparePartsChecklist';

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

function initialParts(
  parts: { part_name: string; used: boolean; notes?: string | null }[],
): WorkOrderPartLineInput[] {
  return parts.map(({ part_name, used, notes }) => ({
    part_name,
    used,
    notes: notes ?? '',
  }));
}

// PUBLIC_INTERFACE
export function WorkOrderDetailPage() {
  /**
   * Work-order detail screen with spare-parts logging and role-gated closure.
   *
   * Closure sends the backend-required fields in one PUT and reloads the
   * resource after success so linked alert and equipment changes are visible.
   */
  const { id } = useParams<{ id: string }>();
  const { data, loading, error, reload } = useWorkOrder(id);
  const { user, isLoading: userLoading } = useCurrentUser();
  const {
    submit: updateWorkOrder,
    submitting,
    error: updateError,
  } = useUpdateWorkOrder();

  const [parts, setParts] = useState<WorkOrderPartLineInput[]>([]);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [rootCause, setRootCause] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [closedMessage, setClosedMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!data) return;
    setParts(initialParts(data.parts));
    setResolutionNotes(data.resolution_notes ?? '');
    setRootCause(data.root_cause ?? '');
  }, [data]);

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

  const canClose =
    data.status === 'OPEN' &&
    !userLoading &&
    user?.role === 'MaintenanceEngineer';

  const handleClose = async () => {
    setValidationError(null);
    setClosedMessage(null);

    if (!resolutionNotes.trim()) {
      setValidationError('Resolution notes are required before closing.');
      return;
    }

    if (!rootCause.trim()) {
      setValidationError('Root cause is required before closing.');
      return;
    }

    if (parts.length === 0) {
      setValidationError(
        'At least one spare-part line is required before closing. Use N/A when no part was used.',
      );
      return;
    }

    if (parts.some((part) => !part.part_name.trim())) {
      setValidationError('Every spare-part line must have a part name.');
      return;
    }

    const updated = await updateWorkOrder(data.id, {
      status: 'CLOSED',
      resolution_notes: resolutionNotes.trim(),
      root_cause: rootCause.trim(),
      parts: parts.map((part) => ({
        part_name: part.part_name.trim(),
        used: part.used,
        notes: part.notes?.trim() || null,
      })),
    });

    if (updated) {
      setClosedMessage('Work order closed successfully.');
      reload();
    }
  };

  return (
    <section aria-labelledby="work-order-heading" className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1
            id="work-order-heading"
            className="text-xl font-semibold text-slate-900"
          >
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
          <Field label="Resolution notes">
            {data.resolution_notes || '—'}
          </Field>
          <Field label="Root cause / failure code">
            {data.root_cause || '—'}
          </Field>
        </dl>
      </div>

      <div className="card p-4">
        <h2 className="text-sm font-semibold text-slate-800">Spare parts</h2>
        {data.status === 'OPEN' && canClose ? (
          <SparePartsChecklist parts={parts} onChange={setParts} />
        ) : data.parts.length === 0 ? (
          <p className="mt-2 text-sm text-slate-600">
            No spare part lines recorded yet. At least one line, which may be
            “N/A”, is required before closure.
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-slate-100">
            {data.parts.map((part) => (
              <li
                key={part.id}
                className="flex flex-wrap items-center gap-3 py-2 text-sm"
              >
                <span className="font-medium text-slate-800">
                  {part.part_name}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    part.used
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {part.used ? 'Used' : 'Not used'}
                </span>
                {part.notes && (
                  <span className="text-slate-600">{part.notes}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {data.status === 'OPEN' && canClose && (
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-slate-800">
            Close work order
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Only a Maintenance Engineer can close a work order.
          </p>

          <label className="mt-3 block text-sm text-slate-700">
            Resolution notes
            <textarea
              aria-label="Resolution notes"
              className="mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              onChange={(event) => setResolutionNotes(event.target.value)}
              value={resolutionNotes}
            />
          </label>

          <label className="mt-3 block text-sm text-slate-700">
            Root cause
            <textarea
              aria-label="Root cause"
              className="mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              onChange={(event) => setRootCause(event.target.value)}
              value={rootCause}
            />
          </label>

          {validationError && (
            <p className="mt-3 text-sm text-red-700" role="alert">
              {validationError}
            </p>
          )}

          {updateError && (
            <div className="mt-3">
              <ErrorPanel
                title="Unable to close work order"
                error={updateError}
              />
            </div>
          )}

          {closedMessage && (
            <p className="mt-3 text-sm text-emerald-700" role="status">
              {closedMessage}
            </p>
          )}

          <Button
            className="mt-4"
            loading={submitting}
            onClick={handleClose}
            type="button"
          >
            Close work order
          </Button>
        </div>
      )}

      {data.status === 'CLOSED' && (
        <div
          className="card border-emerald-200 bg-emerald-50 p-4"
          data-testid="closure-summary"
        >
          <h2 className="text-sm font-semibold text-emerald-900">
            Closure summary
          </h2>
          <dl className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Field label="Closed at">{formatDateTime(data.closed_at)}</Field>
            <Field label="Resolution notes">
              {data.resolution_notes || '—'}
            </Field>
            <Field label="Root cause">{data.root_cause || '—'}</Field>
          </dl>
        </div>
      )}

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
