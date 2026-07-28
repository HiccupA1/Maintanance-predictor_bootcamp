import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { ApiError } from '../../api/client';
import { fromDateTimeLocalValue } from '../../utils/format';
import { useConvertAlertToWorkOrder } from '../../hooks/useWorkOrders';
import {
  PRIORITIES,
  type Priority,
  type WorkOrderPartLineInput,
} from '../../types/workOrders';

/** Editable spare-part line in the conversion form. */
interface PartLineDraft extends WorkOrderPartLineInput {
  /** Client-side key so React can track rows before ids exist. */
  key: string;
}

/** Create a blank part line draft. */
function blankPart(): PartLineDraft {
  return {
    key: `part-${Math.random().toString(36).slice(2, 10)}`,
    part_name: '',
    used: true,
    notes: '',
  };
}

// PUBLIC_INTERFACE
export function ConvertAlertPage() {
  /**
   * Convert Alert → Work Order screen
   * (POST /v1/alerts/{alert_id}/work-orders).
   *
   * The Plant Manager may edit the description, priority and due date before
   * saving, and may optionally record initial spare-part lines. Handles
   * submitting (loading), duplicate work order (409), alert not found (404),
   * validation (422) and success states.
   */
  const { alertId } = useParams<{ alertId: string }>();
  const navigate = useNavigate();
  const { submit, submitting, error: submitError } = useConvertAlertToWorkOrder();

  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<Priority>('HIGH');
  const [dueAtLocal, setDueAtLocal] = useState('');
  const [parts, setParts] = useState<PartLineDraft[]>([]);
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

  const apiError = submitError instanceof ApiError ? submitError : undefined;
  const isDuplicate =
    apiError?.code === 'duplicate_work_order' || Boolean(apiError?.isConflict);
  const isAlertMissing = apiError?.code === 'alert_not_found' || Boolean(apiError?.isNotFound);

  /** Validate the conversion form client-side. */
  const validate = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!description.trim()) {
      errors.description = 'Description is required.';
    }
    if (!PRIORITIES.includes(priority)) {
      errors.priority = 'Select a valid priority.';
    }
    if (parts.some((part) => !part.part_name.trim())) {
      errors.parts = 'Every spare part line needs a part name or ID (use "N/A" if none).';
    }
    return errors;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const errors = validate();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;

    const created = await submit(alertId, {
      description: description.trim(),
      priority,
      due_at: fromDateTimeLocalValue(dueAtLocal),
      parts: parts.map(({ part_name, used, notes }) => ({
        part_name: part_name.trim(),
        used,
        notes: notes?.trim() ? notes.trim() : null,
      })),
    });

    if (created) navigate(`/work-orders/${created.id}`);
  };

  const updatePart = (key: string, patch: Partial<PartLineDraft>) =>
    setParts((prev) => prev.map((part) => (part.key === key ? { ...part, ...patch } : part)));

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

      {isDuplicate && (
        <div role="alert" className="card border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <p className="font-semibold">This alert already has a work order.</p>
          <p className="mt-1">
            Only one work order is permitted per alert, so a second one cannot be created.
          </p>
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

          <div>
            <label className="label" htmlFor="convert-due-at">
              Due date &amp; time (optional)
            </label>
            <input
              id="convert-due-at"
              className="input"
              type="datetime-local"
              value={dueAtLocal}
              onChange={(event) => setDueAtLocal(event.target.value)}
            />
          </div>
        </div>

        <fieldset className="space-y-3">
          <legend className="text-sm font-semibold text-slate-800">
            Spare part lines (optional)
          </legend>
          {parts.length === 0 && (
            <p className="text-sm text-slate-600">
              No part lines added. You can add them now or later; at least one line
              (which may be &ldquo;N/A&rdquo;) is required before closure.
            </p>
          )}
          {parts.map((part, index) => (
            <div key={part.key} className="grid grid-cols-1 gap-3 sm:grid-cols-12">
              <div className="sm:col-span-5">
                <label className="label" htmlFor={`part-name-${part.key}`}>
                  Part name / ID {index + 1}
                </label>
                <input
                  id={`part-name-${part.key}`}
                  className="input"
                  type="text"
                  value={part.part_name}
                  onChange={(event) => updatePart(part.key, { part_name: event.target.value })}
                />
              </div>
              <div className="sm:col-span-5">
                <label className="label" htmlFor={`part-notes-${part.key}`}>
                  Notes
                </label>
                <input
                  id={`part-notes-${part.key}`}
                  className="input"
                  type="text"
                  value={part.notes ?? ''}
                  onChange={(event) => updatePart(part.key, { notes: event.target.value })}
                />
              </div>
              <div className="flex items-end gap-3 sm:col-span-2">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={part.used}
                    onChange={(event) => updatePart(part.key, { used: event.target.checked })}
                  />
                  Used
                </label>
                <button
                  type="button"
                  className="text-sm text-red-700 hover:underline"
                  onClick={() =>
                    setParts((prev) => prev.filter((item) => item.key !== part.key))
                  }
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
          {validationErrors.parts && (
            <p className="text-xs text-red-700">{validationErrors.parts}</p>
          )}
          <Button
            type="button"
            variant="secondary"
            onClick={() => setParts((prev) => [...prev, blankPart()])}
          >
            Add part line
          </Button>
        </fieldset>

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
