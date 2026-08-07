import { useEffect, useState } from 'react';

import { ApiError, toUserMessage } from '../../api/client';
import {
  createReading,
  listReadings,
  updateReading,
  validateReadingCorrection,
  validateReadingForm,
  type Reading,
  type ReadingCorrectionErrors,
  type ReadingCorrectionValues,
  type ReadingFormValues,
  type ReadingValidationErrors,
} from '../../api/readings';
import { listParameters, type Parameter } from '../../api/parameters';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { SkeletonRows } from '../../components/ui/Spinner';
import { useEquipmentList } from '../../hooks/useEquipment';
import { useCurrentUser } from '../../hooks/useCurrentUser';
import { formatDateTime } from '../../utils/format';
import { hasRole } from '../../utils/rbac';

const EMPTY_FORM: ReadingFormValues = {
  equipment_id: '',
  parameter_id: '',
  value: '',
};

const EMPTY_CORRECTION: ReadingCorrectionValues = {
  value: '',
  modification_reason: '',
};

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

function isCorrectionWindowError(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 400 || error.status === 403);
}

// PUBLIC_INTERFACE
export function ReadingsPage() {
  /** Render manual reading capture, reverse-chronological history, and corrections. */
  const { data: equipmentData, loading: equipmentLoading, error: equipmentError } =
    useEquipmentList();
  const { user, isLoading: userLoading, error: userError } = useCurrentUser();
  const canOperate = hasRole(user?.role, ['Operator']);

  const [form, setForm] = useState<ReadingFormValues>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<ReadingValidationErrors>({});
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [parametersLoading, setParametersLoading] = useState(false);
  const [parametersError, setParametersError] = useState<unknown>(null);
  const [readings, setReadings] = useState<Reading[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);
  const [editingReading, setEditingReading] = useState<Reading | null>(null);
  const [correction, setCorrection] =
    useState<ReadingCorrectionValues>(EMPTY_CORRECTION);
  const [correctionErrors, setCorrectionErrors] =
    useState<ReadingCorrectionErrors>({});
  const [correctionMessage, setCorrectionMessage] = useState('');
  const [correctionSaving, setCorrectionSaving] = useState(false);

  const equipment = equipmentData?.items ?? [];

  useEffect(() => {
    if (!form.equipment_id) {
      setParameters([]);
      setParametersError(null);
      setParametersLoading(false);
      return;
    }

    const controller = new AbortController();
    setParametersLoading(true);
    setParametersError(null);

    listParameters(form.equipment_id, controller.signal)
      .then((items) => {
        setParameters(items);
        setParametersLoading(false);
      })
      .catch((error: unknown) => {
        if (isAbort(error)) return;
        setParameters([]);
        setParametersError(error);
        setParametersLoading(false);
      });

    return () => controller.abort();
  }, [form.equipment_id]);

  useEffect(() => {
    if (!form.equipment_id || !form.parameter_id) {
      setReadings([]);
      setHistoryError(null);
      setHistoryLoading(false);
      return;
    }

    const controller = new AbortController();
    setHistoryLoading(true);
    setHistoryError(null);

    listReadings(form.equipment_id, form.parameter_id, controller.signal)
      .then((items) => {
        setReadings(items);
        setHistoryLoading(false);
      })
      .catch((error: unknown) => {
        if (isAbort(error)) return;
        setReadings([]);
        setHistoryError(error);
        setHistoryLoading(false);
      });

    return () => controller.abort();
  }, [form.equipment_id, form.parameter_id]);

  const refreshHistory = async () => {
    if (!form.equipment_id || !form.parameter_id) return;
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      setReadings(await listReadings(form.equipment_id, form.parameter_id));
    } catch (error) {
      setHistoryError(error);
    } finally {
      setHistoryLoading(false);
    }
  };

  const submitReading = async () => {
    const errors = validateReadingForm(form);
    setFormErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSaving(true);
    try {
      await createReading({
        equipment_id: form.equipment_id.trim(),
        parameter_id: form.parameter_id.trim(),
        value: form.value.trim(),
      });
      setForm((current) => ({ ...current, value: '' }));
      setFormErrors({});
      await refreshHistory();
    } catch (error) {
      setFormErrors({ form: toUserMessage(error) });
    } finally {
      setSaving(false);
    }
  };

  const beginCorrection = (reading: Reading) => {
    setEditingReading(reading);
    setCorrection({ value: reading.value, modification_reason: '' });
    setCorrectionErrors({});
    setCorrectionMessage('');
  };

  const cancelCorrection = () => {
    setEditingReading(null);
    setCorrection(EMPTY_CORRECTION);
    setCorrectionErrors({});
    setCorrectionMessage('');
  };

  const saveCorrection = async () => {
    const errors = validateReadingCorrection(correction);
    setCorrectionErrors(errors);
    setCorrectionMessage('');
    if (Object.keys(errors).length > 0 || !editingReading) return;

    setCorrectionSaving(true);
    try {
      await updateReading(editingReading.id, {
        value: correction.value.trim(),
        modification_reason: correction.modification_reason.trim(),
      });
      cancelCorrection();
      await refreshHistory();
    } catch (error) {
      if (isCorrectionWindowError(error)) {
        setCorrectionMessage('Edit window expired');
      } else {
        setCorrectionErrors({ form: toUserMessage(error) });
      }
    } finally {
      setCorrectionSaving(false);
    }
  };

  return (
    <section aria-labelledby="readings-heading" className="space-y-4">
      <div>
        <h1 id="readings-heading" className="text-xl font-semibold text-slate-900">
          Manual readings
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Capture measurements instantly and review recent changes in real time.
        </p>
      </div>

      {Boolean(userError) && (
        <ErrorPanel
          title="Unable to determine your access"
          error={toUserMessage(userError)}
        />
      )}

      {!userLoading && !userError && !canOperate && (
        <div className="card border-amber-200 bg-amber-50 p-4" role="status">
          <h2 className="text-sm font-semibold text-amber-900">Operator access required</h2>
          <p className="mt-1 text-sm text-amber-800">
            Only Operators can capture or correct manual readings.
          </p>
        </div>
      )}

      <div className="card p-4" data-testid="reading-capture">
        <h2 className="text-sm font-semibold text-slate-800">Capture reading</h2>
        <p className="mt-1 text-sm text-slate-600">
          Values are stored as entered, including non-numeric observations.
        </p>

        {equipmentLoading && <SkeletonRows rows={2} columns={3} />}

        {!equipmentLoading && Boolean(equipmentError) && (
          <ErrorPanel title="Unable to load equipment" error={toUserMessage(equipmentError)} />
        )}

        {!equipmentLoading && !equipmentError && (
          <form
            className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3"
            onSubmit={(event) => {
              event.preventDefault();
              void submitReading();
            }}
            noValidate
          >
            <label className="label">
              Equipment
              <select
                className="input"
                value={form.equipment_id}
                disabled={!canOperate}
                aria-invalid={Boolean(formErrors.equipment_id)}
                onChange={(event) =>
                  setForm({
                    equipment_id: event.target.value,
                    parameter_id: '',
                    value: form.value,
                  })
                }
              >
                <option value="">Select equipment</option>
                {equipment.map((item) => (
                  <option key={item.id} value={item.equipment_id}>
                    {item.name} ({item.equipment_id})
                  </option>
                ))}
              </select>
              {formErrors.equipment_id && (
                <span className="field-error">{formErrors.equipment_id}</span>
              )}
            </label>

            <label className="label">
              Parameter
              <select
                className="input"
                value={form.parameter_id}
                disabled={!canOperate || !form.equipment_id || parametersLoading}
                aria-invalid={Boolean(formErrors.parameter_id)}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    parameter_id: event.target.value,
                  }))
                }
              >
                <option value="">
                  {parametersLoading ? 'Loading parameters…' : 'Select parameter'}
                </option>
                {parameters.map((parameter) => (
                  <option key={parameter.id} value={parameter.id}>
                    {parameter.name} ({parameter.unit})
                  </option>
                ))}
              </select>
              {formErrors.parameter_id && (
                <span className="field-error">{formErrors.parameter_id}</span>
              )}
            </label>

            <label className="label">
              Value
              <input
                className="input"
                value={form.value}
                disabled={!canOperate}
                aria-invalid={Boolean(formErrors.value)}
                onChange={(event) =>
                  setForm((current) => ({ ...current, value: event.target.value }))
                }
                placeholder="Try “72.4”, “normal”, or “abnormal vibration”"
              />
              {formErrors.value && <span className="field-error">{formErrors.value}</span>}
            </label>

            {Boolean(parametersError) && (
              <p className="field-error md:col-span-3" role="alert">
                {toUserMessage(parametersError)}
              </p>
            )}
            {formErrors.form && (
              <p className="field-error md:col-span-3" role="alert">
                {formErrors.form}
              </p>
            )}

            <div className="md:col-span-3">
              <Button type="submit" loading={saving} disabled={!canOperate}>
                Save reading
              </Button>
            </div>
          </form>
        )}
      </div>

      <div className="card p-4" data-testid="reading-history">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-800">Reading history</h2>
            <p className="mt-1 text-sm text-slate-600">
              Pick an equipment + parameter to see the most recent readings first.
            </p>
          </div>
          {form.equipment_id && form.parameter_id && (
            <span className="text-xs text-slate-500">
              {readings.length} reading{readings.length === 1 ? '' : 's'}
            </span>
          )}
        </div>

        {!form.equipment_id || !form.parameter_id ? (
          <EmptyState
            title="Choose an equipment parameter"
            description="History will appear after both selections are made."
          />
        ) : historyLoading ? (
          <div className="mt-4">
            <SkeletonRows rows={3} columns={5} />
          </div>
        ) : historyError ? (
          <div className="mt-4">
            <ErrorPanel
              title="Unable to load reading history"
              error={toUserMessage(historyError)}
              onRetry={() => void refreshHistory()}
            />
          </div>
        ) : readings.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              title="No readings yet"
              description="Save the first reading for this equipment parameter."
            />
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <caption className="sr-only">Reading history, newest first</caption>
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th scope="col" className="px-3 py-2">Value</th>
                  <th scope="col" className="px-3 py-2">Timestamp</th>
                  <th scope="col" className="px-3 py-2">Entered by</th>
                  <th scope="col" className="px-3 py-2">Status</th>
                  {canOperate && <th scope="col" className="px-3 py-2">Actions</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {readings.map((reading) => (
                  <tr key={reading.id}>
                    <td className="px-3 py-3 font-medium text-slate-800">{reading.value}</td>
                    <td className="px-3 py-3 text-slate-600">
                      {formatDateTime(reading.timestamp)}
                    </td>
                    <td className="px-3 py-3 text-slate-600">{reading.entered_by}</td>
                    <td className="px-3 py-3 text-slate-600">
                      {reading.modified_at
                        ? `Modified by ${reading.modified_by ?? 'unknown'}`
                        : 'Original'}
                    </td>
                    {canOperate && (
                      <td className="px-3 py-3">
                        <Button
                          type="button"
                          variant="secondary"
                          onClick={() => beginCorrection(reading)}
                        >
                          Edit
                        </Button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {canOperate && editingReading && (
          <form
            className="mt-4 space-y-4 rounded-md border border-slate-200 bg-slate-50 p-4"
            onSubmit={(event) => {
              event.preventDefault();
              void saveCorrection();
            }}
            noValidate
          >
            <h3 className="text-sm font-semibold text-slate-800">
              Correct reading from {formatDateTime(editingReading.timestamp)}
            </h3>
            <label className="label">
              Value
              <input
                className="input"
                value={correction.value}
                aria-invalid={Boolean(correctionErrors.value)}
                onChange={(event) =>
                  setCorrection((current) => ({ ...current, value: event.target.value }))
                }
              />
              {correctionErrors.value && (
                <span className="field-error">{correctionErrors.value}</span>
              )}
            </label>
            <label className="label">
              Modification reason
              <textarea
                className="input min-h-20"
                value={correction.modification_reason}
                aria-invalid={Boolean(correctionErrors.modification_reason)}
                onChange={(event) =>
                  setCorrection((current) => ({
                    ...current,
                    modification_reason: event.target.value,
                  }))
                }
                placeholder="Explain why this reading is being corrected"
              />
              {correctionErrors.modification_reason && (
                <span className="field-error">
                  {correctionErrors.modification_reason}
                </span>
              )}
            </label>
            {correctionMessage && (
              <p className="field-error" role="alert">{correctionMessage}</p>
            )}
            {correctionErrors.form && (
              <p className="field-error" role="alert">{correctionErrors.form}</p>
            )}
            <div className="flex gap-2">
              <Button type="submit" loading={correctionSaving}>
                Save correction
              </Button>
              <Button type="button" variant="secondary" onClick={cancelCorrection}>
                Cancel
              </Button>
            </div>
          </form>
        )}
      </div>
    </section>
  );
}
