import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { SkeletonRows } from '../../components/ui/Spinner';
import { ApiError } from '../../api/client';
import {
  fromDateTimeLocalValue,
  toDateTimeLocalValue,
} from '../../utils/format';
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
  description: string;
  priority: Priority;
  status: WorkOrderStatus;
  dueAtLocal: string;
  resolutionNotes: string;
  rootCause: string;
}

// PUBLIC_INTERFACE
export function WorkOrderEditPage() {
  /**
   * Edit Work Order screen (PUT /v1/work-orders/{id}).
   *
   * Loads the current work order, lets the user change the editable fields,
   * validates client-side (non-empty description, closure fields required when
   * moving to CLOSED, at least one change), and surfaces backend Problem JSON
   * errors inline.
   */
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, loading, error, reload } = useWorkOrder(id);
  const { submit, submitting, error: submitError } = useUpdateWorkOrder();

  const [form, setForm] = useState<FormState | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Seed the form once the work order has loaded.
  useEffect(() => {
    if (!data) return;
    setForm({
      description: data.description,
      priority: data.priority,
      status: data.status,
      dueAtLocal: toDateTimeLocalValue(data.due_at),
      resolutionNotes: data.resolution_notes ?? '',
      rootCause: data.root_cause ?? '',
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

  /** Build the minimal update payload containing only changed fields. */
  const buildPayload = (): WorkOrderUpdatePayload => {
    const payload: WorkOrderUpdatePayload = {};
    if (form.description.trim() !== data.description) {
      payload.description = form.description.trim();
    }
    if (form.priority !== data.priority) payload.priority = form.priority;
    if (form.status !== data.status) payload.status = form.status;

    const dueAtIso = fromDateTimeLocalValue(form.dueAtLocal);
    const currentDueIso = data.due_at ? new Date(data.due_at).toISOString() : null;
    if (dueAtIso !== currentDueIso) payload.due_at = dueAtIso;

    const notes = form.resolutionNotes.trim();
    if (notes !== (data.resolution_notes ?? '')) {
      payload.resolution_notes = notes || null;
    }
    const rootCause = form.rootCause.trim();
    if (rootCause !== (data.root_cause ?? '')) {
      payload.root_cause = rootCause || null;
    }
    return payload;
  };

  /** Validate the form and return field-level messages. */
  const validate = (payload: WorkOrderUpdatePayload): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!form.description.trim()) {
      errors.description = 'Description is required.';
    }
    if (form.status === 'CLOSED' && data.status !== 'CLOSED') {
      if (!form.resolutionNotes.trim()) {
        errors.resolution_notes = 'Resolution notes are required to close a work order.';
      }
      if (!form.rootCause.trim()) {
        errors.root_cause = 'Root cause or failure code is required to close a work order.';
      }
      if (data.parts.length === 0) {
        errors.parts =
          'At least one spare part line (which may be "N/A") is required before closure.';
      }
    }
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

      {Boolean(submitError) && (
        <ErrorPanel title="Could not save changes" error={submitError} />
      )}

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
          <label className="label" htmlFor="description">
            Description
          </label>
          <textarea
            id="description"
            className="input"
            rows={3}
            required
            disabled={isClosed}
            value={form.description}
            aria-invalid={Boolean(validationErrors.description) || undefined}
            aria-describedby={validationErrors.description ? 'description-error' : undefined}
            onChange={(event) => update('description', event.target.value)}
          />
          {validationErrors.description && (
            <p id="description-error" className="mt-1 text-xs text-red-700">
              {validationErrors.description}
            </p>
          )}
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
            <label className="label" htmlFor="due-at">
              Due date &amp; time
            </label>
            <input
              id="due-at"
              className="input"
              type="datetime-local"
              disabled={isClosed}
              value={form.dueAtLocal}
              onChange={(event) => update('dueAtLocal', event.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="label" htmlFor="resolution-notes">
            Resolution notes
          </label>
          <textarea
            id="resolution-notes"
            className="input"
            rows={3}
            disabled={isClosed}
            value={form.resolutionNotes}
            aria-invalid={Boolean(validationErrors.resolution_notes) || undefined}
            onChange={(event) => update('resolutionNotes', event.target.value)}
          />
          {validationErrors.resolution_notes && (
            <p className="mt-1 text-xs text-red-700">{validationErrors.resolution_notes}</p>
          )}
        </div>

        <div>
          <label className="label" htmlFor="root-cause">
            Root cause / failure code
          </label>
          <input
            id="root-cause"
            className="input"
            type="text"
            disabled={isClosed}
            value={form.rootCause}
            aria-invalid={Boolean(validationErrors.root_cause) || undefined}
            onChange={(event) => update('rootCause', event.target.value)}
          />
          {validationErrors.root_cause && (
            <p className="mt-1 text-xs text-red-700">{validationErrors.root_cause}</p>
          )}
        </div>

        {validationErrors.parts && (
          <p className="text-xs text-red-700">{validationErrors.parts}</p>
        )}

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
