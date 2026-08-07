import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { SkeletonRows } from '../../components/ui/Spinner';
import { ApiError } from '../../api/client';
import { useUpdateWorkOrder, useWorkOrder } from '../../hooks/useWorkOrders';
import {
  PRIORITIES,
  WORK_ORDER_STATUSES,
  type Priority,
  type WorkOrderStatus,
  type WorkOrderUpdatePayload,
} from '../../types/workOrders';

/** Local, editable representation of the work order form. */
interface FormState {
  title: string;
  description: string;
  priority: Priority;
  status: WorkOrderStatus;
  assignedTo: string;
  closedBy: string;
}

// PUBLIC_INTERFACE
export function WorkOrderEditPage() {
  /**
   * Edit Work Order screen (PUT /v1/work-orders/{id}).
   *
   * Live schema constraints:
   * - No due_at / parts / resolution notes / root cause fields exist.
   * - Only updates to real columns are permitted.
   */
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, loading, error, reload } = useWorkOrder(id);
  const { submit, submitting, error: submitError } = useUpdateWorkOrder();

  const [form, setForm] = useState<FormState | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>(
    {},
  );

  useEffect(() => {
    if (!data) return;
    setForm({
      title: data.title,
      description: data.description ?? '',
      priority: data.priority,
      status: data.status,
      assignedTo: data.assigned_to ?? '',
      closedBy: data.closed_by ?? '',
    });
  }, [data]);

  if (loading) {
    return (
      <div className="card" data-testid="work-order-edit-loading">
        <span className="sr-only" role="status">
          Loading work order
        </span>
        <SkeletonRows rows={5} columns={2} />
      </div>
    );
  }

  if (error) {
    const apiError = error instanceof ApiError ? error : undefined;
    if (apiError?.isNotFound) {
      return (
        <EmptyState
          title="Work order not found"
          description="This work order does not exist, so it cannot be edited."
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

  if (!data || !form) {
    return (
      <EmptyState
        title="No work order data"
        description="The server returned no content for this work order."
      />
    );
  }

  const isClosed = data.status === 'CLOSED';

  const buildPayload = (): WorkOrderUpdatePayload => {
    const payload: WorkOrderUpdatePayload = {};

    if (form.title.trim() !== data.title) payload.title = form.title.trim();

    const nextDescription = form.description.trim() || null;
    const currentDescription = (data.description ?? '').trim() || null;
    if (nextDescription !== currentDescription) payload.description = nextDescription;

    if (form.priority !== data.priority) payload.priority = form.priority;
    if (form.status !== data.status) payload.status = form.status;

    const nextAssignedTo = form.assignedTo.trim() || null;
    const currentAssignedTo = (data.assigned_to ?? '').trim() || null;
    if (nextAssignedTo !== currentAssignedTo) payload.assigned_to = nextAssignedTo;

    const nextClosedBy = form.closedBy.trim() || null;
    const currentClosedBy = (data.closed_by ?? '').trim() || null;
    if (nextClosedBy !== currentClosedBy) payload.closed_by = nextClosedBy;

    return payload;
  };

  const validate = (payload: WorkOrderUpdatePayload): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!form.title.trim()) errors.title = 'Title is required.';
    if (Object.keys(payload).length === 0) {
      errors.form = 'Change at least one field before saving.';
    }
    return errors;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const payload = buildPayload();
    const errors = validate(payload);
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;

    const updated = await submit(data.id, payload);
    if (updated) navigate(`/work-orders/${updated.id}`);
  };

  const update = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));

  return (
    <section aria-labelledby="edit-heading" className="space-y-4">
      <div>
        <h1 id="edit-heading" className="text-xl font-semibold text-slate-900">
          Edit work order
        </h1>
        <p className="mt-1 font-mono text-xs text-slate-500">{data.id}</p>
      </div>

      {isClosed && (
        <div role="status" className="card border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          This work order is closed. Closed work orders cannot be modified.
        </div>
      )}

      {Boolean(submitError) && <ErrorPanel title="Could not save changes" error={submitError} />}

      {validationErrors.form && (
        <div role="alert" className="card border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          {String(validationErrors.form)}
        </div>
      )}

      <form
        className="card space-y-4 p-4"
        onSubmit={(event) => {
          void handleSubmit(event);
        }}
        noValidate
      >
        <div>
          <label className="label" htmlFor="title">
            Title
          </label>
          <input
            id="title"
            className="input"
            type="text"
            required
            disabled={isClosed}
            value={form.title}
            aria-invalid={Boolean(validationErrors.title) || undefined}
            onChange={(event) => update('title', event.target.value)}
          />
          {validationErrors.title && (
            <p className="mt-1 text-xs text-red-700">{validationErrors.title}</p>
          )}
        </div>

        <div>
          <label className="label" htmlFor="description">
            Description
          </label>
          <textarea
            id="description"
            className="input"
            rows={3}
            disabled={isClosed}
            value={form.description}
            onChange={(event) => update('description', event.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="label" htmlFor="priority">
              Priority
            </label>
            <select
              id="priority"
              className="input"
              disabled={isClosed}
              value={form.priority}
              onChange={(event) => update('priority', event.target.value as Priority)}
            >
              {PRIORITIES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label" htmlFor="status">
              Status
            </label>
            <select
              id="status"
              className="input"
              disabled={isClosed}
              value={form.status}
              onChange={(event) => update('status', event.target.value as WorkOrderStatus)}
            >
              {WORK_ORDER_STATUSES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label" htmlFor="assigned-to">
              Assigned to
            </label>
            <input
              id="assigned-to"
              className="input"
              type="text"
              disabled={isClosed}
              value={form.assignedTo}
              onChange={(event) => update('assignedTo', event.target.value)}
              placeholder="(optional)"
            />
          </div>
        </div>

        <div>
          <label className="label" htmlFor="closed-by">
            Closed by
          </label>
          <input
            id="closed-by"
            className="input"
            type="text"
            disabled={isClosed}
            value={form.closedBy}
            onChange={(event) => update('closedBy', event.target.value)}
            placeholder="(optional)"
          />
        </div>

        <div className="flex items-center gap-3">
          <Button type="submit" loading={submitting} disabled={isClosed}>
            Save changes
          </Button>
          <Link
            to={`/work-orders/${data.id}`}
            className="text-sm text-slate-600 hover:underline"
          >
            Cancel
          </Link>
        </div>
      </form>
    </section>
  );
}
