import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { ApiError } from '../../api/client';
import { useAlert } from '../../hooks/useAlerts';
import { useCurrentUser } from '../../hooks/useCurrentUser';
import { useConvertAlertToWorkOrder } from '../../hooks/useWorkOrders';
import { hasRole } from '../../utils/rbac';
import { PRIORITIES, type Priority } from '../../types/workOrders';

// PUBLIC_INTERFACE
export function ConvertAlertPage() {
  /**
   * Convert Alert → Work Order screen.
   *
   * The source alert is display context only. Creation uses
   * POST /v1/work-orders because public.work_orders has no alert_id column.
   *
   * Live schema constraints:
   * - public.work_orders has NO due_at column.
   * - There are no persisted part lines.
   *
   * The Plant Manager may edit the description and priority before saving.
   */
  const { alertId } = useParams<{ alertId: string }>();
  const navigate = useNavigate();
  const { user, isLoading: userLoading } = useCurrentUser();
  const { data: alert } = useAlert(alertId);
  const { submit, submitting, error: submitError } = useConvertAlertToWorkOrder();

  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<Priority>('HIGH');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  if (!alertId) {
    return (
      <EmptyState
        title="Missing alert reference"
        description="No alert id was provided, so there is nothing to convert."
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

  if (userLoading) {
    return (
      <EmptyState
        title="Checking permissions"
        description="Your access to alert conversion is being verified."
      />
    );
  }

  if (!hasRole(user?.role, ['PlantManager'])) {
    return (
      <EmptyState
        title="Conversion unavailable"
        description="Only Plant Managers can convert alerts into work orders."
        action={
          <Link
            to={`/alerts/${alertId}`}
            className="rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Back to alert
          </Link>
        }
      />
    );
  }

  const apiError = submitError instanceof ApiError ? submitError : undefined;
  const isDuplicate = Boolean(apiError?.isConflict);
  const isAlertMissing = Boolean(apiError?.isNotFound);
  const duplicateProblem = apiError?.problem as Record<string, unknown> | undefined;
  const existingWorkOrderId =
    typeof duplicateProblem?.work_order_id === 'string'
      ? duplicateProblem.work_order_id
      : typeof duplicateProblem?.existing_work_order_id === 'string'
        ? duplicateProblem.existing_work_order_id
        : null;

  /** Validate the conversion form client-side. */
  const validate = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!description.trim()) {
      errors.description = 'Description is required.';
    }
    if (!PRIORITIES.includes(priority)) {
      errors.priority = 'Select a valid priority.';
    }
    return errors;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const errors = validate();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;

    const created = await submit({
      title: 'Alert follow-up',
      description: description.trim(),
      priority,
    });

    if (created) navigate(`/work-orders/${created.id}`);
  };

  return (
    <section aria-labelledby="convert-heading" className="space-y-4">
      <div>
        <h1 id="convert-heading" className="text-xl font-semibold text-slate-900">
          Convert alert to work order
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Source alert <span className="font-mono text-xs">{alertId}</span>. Machine
          details, readings, time and issuer are captured automatically by the server.
        </p>
      </div>

      {alert && (
        <div className="card p-4" aria-label="Source alert summary">
          <h2 className="text-sm font-semibold text-slate-800">Source alert summary</h2>
          <dl className="mt-3 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Equipment</dt>
              <dd className="mt-1 font-mono text-xs text-slate-800">{alert.equipment_id}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Parameter</dt>
              <dd className="mt-1 text-slate-800">
                {alert.parameter_name || alert.parameter_id || '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Value</dt>
              <dd className="mt-1 text-slate-800">{alert.current_value || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">
                Breach timestamp
              </dt>
              <dd className="mt-1 text-slate-800">
                {alert.breach_timestamp || alert.created_at}
              </dd>
            </div>
          </dl>
        </div>
      )}

      {isDuplicate && (
        <div role="alert" className="card border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <p className="font-semibold">Work order creation conflicted with current state.</p>
          {existingWorkOrderId ? (
            <p className="mt-1">
              <Link
                to={`/work-orders/${existingWorkOrderId}`}
                className="font-medium text-amber-900 underline"
              >
                View existing work order
              </Link>
            </p>
          ) : (
            <p className="mt-1">
              Find the existing work order in the{' '}
              <Link to="/work-orders" className="font-medium text-amber-900 underline">
                Work Orders list
              </Link>
              .
            </p>
          )}
        </div>
      )}

      {isAlertMissing && (
        <div role="alert" className="card border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <p className="font-semibold">Alert not found.</p>
          <p className="mt-1">This alert no longer exists, so it cannot be converted.</p>
        </div>
      )}

      {Boolean(submitError) && !isDuplicate && !isAlertMissing && (
        <ErrorPanel title="Could not create the work order" error={submitError} />
      )}

      <form
        className="card space-y-4 p-4"
        onSubmit={(event) => {
          void handleSubmit(event);
        }}
        noValidate
      >
        <div>
          <label className="label" htmlFor="convert-description">
            Description
          </label>
          <textarea
            id="convert-description"
            className="input"
            rows={3}
            required
            value={description}
            aria-invalid={Boolean(validationErrors.description) || undefined}
            aria-describedby={
              validationErrors.description ? 'convert-description-error' : undefined
            }
            onChange={(event) => setDescription(event.target.value)}
          />
          {validationErrors.description && (
            <p id="convert-description-error" className="mt-1 text-xs text-red-700">
              {String(validationErrors.description)}
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="convert-priority">
              Priority
            </label>
            <select
              id="convert-priority"
              className="input"
              value={priority}
              onChange={(event) => setPriority(event.target.value as Priority)}
            >
              {PRIORITIES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
            {validationErrors.priority && (
              <p className="mt-1 text-xs text-red-700">{validationErrors.priority}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button type="submit" loading={submitting} disabled={isDuplicate}>
            Create work order
          </Button>
          <Link to="/work-orders" className="text-sm text-slate-600 hover:underline">
            Cancel
          </Link>
        </div>
      </form>
    </section>
  );
}
