import { useEffect, useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  createParameter,
  listParameters,
  updateParameter,
  validateParameterForm,
  type Parameter,
  type ParameterFormValues,
  type ParameterValidationErrors,
} from '../../api/parameters';
import { ApiError, toUserMessage } from '../../api/client';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { SkeletonRows } from '../../components/ui/Spinner';
import { useCurrentUser } from '../../hooks/useCurrentUser';
import { isAdminRole, useEquipment } from '../../hooks/useEquipment';
import { formatDateTime } from '../../utils/format';

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm text-slate-800">{children}</dd>
    </div>
  );
}

const EMPTY_FORM: ParameterFormValues = {
  name: '',
  unit: '',
  min_threshold: '',
  max_threshold: '',
  active: true,
  suggested_action: '',
};

function formFromParameter(parameter: Parameter): ParameterFormValues {
  return {
    name: parameter.name,
    unit: parameter.unit,
    min_threshold: parameter.min_threshold == null
      ? ''
      : String(parameter.min_threshold),
    max_threshold: parameter.max_threshold == null
      ? ''
      : String(parameter.max_threshold),
    active: parameter.active,
    suggested_action: parameter.suggested_action ?? '',
  };
}

function ParameterForm({
  values,
  errors,
  saving,
  onChange,
  onCancel,
  onSubmit,
}: {
  values: ParameterFormValues;
  errors: ParameterValidationErrors;
  saving: boolean;
  onChange: (values: ParameterFormValues) => void;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  const updateField = <K extends keyof ParameterFormValues>(
    field: K,
    value: ParameterFormValues[K],
  ) => onChange({ ...values, [field]: value });

  return (
    <form
      className="mt-4 space-y-4 rounded-md border border-slate-200 bg-slate-50 p-4"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
      noValidate
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label className="text-sm text-slate-700">
          <span className="font-medium">Name</span>
          <input
            aria-invalid={Boolean(errors.name)}
            className="input mt-1"
            value={values.name}
            onChange={(event) => updateField('name', event.target.value)}
          />
          {errors.name && <span className="field-error">{errors.name}</span>}
        </label>

        <label className="text-sm text-slate-700">
          <span className="font-medium">Unit</span>
          <input
            aria-invalid={Boolean(errors.unit)}
            className="input mt-1"
            value={values.unit}
            onChange={(event) => updateField('unit', event.target.value)}
            placeholder="e.g. °C"
          />
          {errors.unit && <span className="field-error">{errors.unit}</span>}
        </label>

        <label className="text-sm text-slate-700">
          <span className="font-medium">Minimum threshold</span>
          <input
            aria-invalid={Boolean(errors.min_threshold)}
            className="input mt-1"
            type="number"
            step="any"
            value={values.min_threshold}
            onChange={(event) => updateField('min_threshold', event.target.value)}
          />
          {errors.min_threshold && (
            <span className="field-error">{errors.min_threshold}</span>
          )}
        </label>

        <label className="text-sm text-slate-700">
          <span className="font-medium">Maximum threshold</span>
          <input
            aria-invalid={Boolean(errors.max_threshold)}
            className="input mt-1"
            type="number"
            step="any"
            value={values.max_threshold}
            onChange={(event) => updateField('max_threshold', event.target.value)}
          />
          {errors.max_threshold && (
            <span className="field-error">{errors.max_threshold}</span>
          )}
        </label>
      </div>

      <label className="flex items-center gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={values.active}
          onChange={(event) => updateField('active', event.target.checked)}
        />
        Active
      </label>

      <label className="block text-sm text-slate-700">
        <span className="font-medium">Suggested action</span>
        <textarea
          className="input mt-1 min-h-20"
          value={values.suggested_action}
          onChange={(event) => updateField('suggested_action', event.target.value)}
          placeholder="Optional response when the threshold is breached"
        />
      </label>

      {errors.form && (
        <p className="field-error" role="alert">{errors.form}</p>
      )}

      <div className="flex gap-2">
        <Button type="submit" loading={saving}>
          Save parameter
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

// PUBLIC_INTERFACE
export function EquipmentDetailPage() {
  /** Render equipment metadata and configurable MVP threshold parameters. */
  const { id } = useParams<{ id: string }>();
  const { data, loading, error, reload } = useEquipment(id);
  const { user } = useCurrentUser();

  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [parametersLoading, setParametersLoading] = useState(false);
  const [parametersError, setParametersError] = useState<unknown>(null);
  const [parameterReload, setParameterReload] = useState(0);
  const [formValues, setFormValues] = useState<ParameterFormValues>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<ParameterValidationErrors>({});
  const [editingParameter, setEditingParameter] = useState<Parameter | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const equipmentId = data?.equipment_id;
  const canManageParameters = user?.role === 'PlantManager';

  useEffect(() => {
    if (!equipmentId) {
      setParameters([]);
      setParametersLoading(false);
      return;
    }

    const controller = new AbortController();
    setParametersLoading(true);
    setParametersError(null);

    listParameters(equipmentId, controller.signal)
      .then((items) => {
        setParameters(items);
        setParametersLoading(false);
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') {
          return;
        }
        setParametersError(requestError);
        setParametersLoading(false);
      });

    return () => controller.abort();
  }, [equipmentId, parameterReload]);

  const openAddForm = () => {
    setEditingParameter(null);
    setFormValues(EMPTY_FORM);
    setFormErrors({});
    setFormOpen(true);
  };

  const openEditForm = (parameter: Parameter) => {
    setEditingParameter(parameter);
    setFormValues(formFromParameter(parameter));
    setFormErrors({});
    setFormOpen(true);
  };

  const saveParameter = async () => {
    const validationErrors = validateParameterForm(formValues);
    setFormErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0 || !equipmentId) return;

    setSaving(true);
    try {
      const saved = editingParameter
        ? await updateParameter(editingParameter.id, formValues)
        : await createParameter(equipmentId, formValues);

      setParameters((current) => editingParameter
        ? current.map((item) => item.id === saved.id ? saved : item)
        : [...current, saved].sort((a, b) => a.name.localeCompare(b.name)));
      setFormOpen(false);
      setFormErrors({});
    } catch (requestError) {
      setFormErrors({ form: toUserMessage(requestError) });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="card" data-testid="equipment-detail-loading">
        <span className="sr-only" role="status">Loading equipment</span>
        <SkeletonRows rows={5} columns={2} />
      </div>
    );
  }

  if (error) {
    const notFound = error instanceof ApiError && error.isNotFound;
    return notFound ? (
      <EmptyState
        title="Equipment not found"
        description="This equipment record does not exist or may have been removed."
        action={<Link to="/equipment"><Button>Back to equipment</Button></Link>}
      />
    ) : (
      <ErrorPanel title="Unable to load equipment" error={error} onRetry={reload} />
    );
  }

  if (!data) {
    return <EmptyState title="No equipment data" description="The server returned no equipment data." />;
  }

  return (
    <section aria-labelledby="equipment-detail-heading" className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 id="equipment-detail-heading" className="text-xl font-semibold text-slate-900">
            {data.name}
          </h1>
          <p className="mt-1 font-mono text-xs text-slate-500">{data.equipment_id}</p>
        </div>
        {isAdminRole() && (
          <Link to={`/equipment/${encodeURIComponent(data.equipment_id)}/edit`}>
            <Button>Edit equipment</Button>
          </Link>
        )}
      </div>

      <div className="card p-4">
        <h2 className="text-sm font-semibold text-slate-800">Equipment metadata</h2>
        <dl className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Equipment ID"><span className="font-mono">{data.equipment_id}</span></Field>
          <Field label="Name">{data.name}</Field>
          <Field label="Location">{data.location}</Field>
          <Field label="Type">{data.type}</Field>
          <Field label="Criticality">{data.criticality} / 5</Field>
          <Field label="Health"><Badge>{data.health_status === 'AT_RISK' ? 'At Risk' : data.health_status || 'Unknown'}</Badge></Field>
          <Field label="Last service">{formatDateTime(data.last_service_date)}</Field>
          <Field label="Updated">{formatDateTime(data.updated_at)}</Field>
        </dl>
      </div>

      <div className="card p-4" data-testid="equipment-parameters">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-800">Parameters and thresholds</h2>
            <p className="mt-1 text-sm text-slate-600">
              Configure active limits and suggested responses for this equipment.
            </p>
          </div>
          {canManageParameters && (
            <Button type="button" onClick={openAddForm}>Add parameter</Button>
          )}
        </div>

        {parametersLoading && (
          <div className="mt-4" data-testid="parameters-loading">
            <SkeletonRows rows={2} columns={3} />
          </div>
        )}

        {!parametersLoading && parametersError && (
          <ErrorPanel
            title="Unable to load parameters"
            error={parametersError}
            onRetry={() => setParameterReload((value) => value + 1)}
          />
        )}

        {!parametersLoading && !parametersError && parameters.length === 0 && (
          <p className="mt-4 text-sm text-slate-600" data-testid="parameters-empty">
            No parameters have been configured for this equipment.
          </p>
        )}

        {!parametersLoading && !parametersError && parameters.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-2 py-2">Name</th>
                  <th className="px-2 py-2">Unit</th>
                  <th className="px-2 py-2">Min</th>
                  <th className="px-2 py-2">Max</th>
                  <th className="px-2 py-2">Active</th>
                  <th className="px-2 py-2">Suggested action</th>
                  {canManageParameters && <th className="px-2 py-2">Actions</th>}
                </tr>
              </thead>
              <tbody>
                {parameters.map((parameter) => (
                  <tr key={parameter.id} className="border-b border-slate-100">
                    <td className="px-2 py-3 font-medium text-slate-800">{parameter.name}</td>
                    <td className="px-2 py-3">{parameter.unit}</td>
                    <td className="px-2 py-3">{parameter.min_threshold ?? '—'}</td>
                    <td className="px-2 py-3">{parameter.max_threshold ?? '—'}</td>
                    <td className="px-2 py-3">{parameter.active ? 'Yes' : 'No'}</td>
                    <td className="max-w-xs px-2 py-3">{parameter.suggested_action || '—'}</td>
                    {canManageParameters && (
                      <td className="px-2 py-3">
                        <Button
                          type="button"
                          variant="secondary"
                          onClick={() => openEditForm(parameter)}
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

        {canManageParameters && formOpen && (
          <ParameterForm
            values={formValues}
            errors={formErrors}
            saving={saving}
            onChange={setFormValues}
            onCancel={() => setFormOpen(false)}
            onSubmit={saveParameter}
          />
        )}
      </div>

      <Link to="/equipment" className="text-sm text-brand-700 hover:underline">← Back to equipment</Link>
    </section>
  );
}
