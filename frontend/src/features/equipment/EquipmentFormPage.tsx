import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { ApiError } from '../../api/client';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { SkeletonRows } from '../../components/ui/Spinner';
import {
  isAdminRole,
  useEquipment,
  useEquipmentMutation,
  validateEquipmentForm,
} from '../../hooks/useEquipment';
import type {
  EquipmentFormValues,
  EquipmentPayload,
  EquipmentValidationErrors,
} from '../../types/equipment';

const emptyForm: EquipmentFormValues = {
  equipment_id: '',
  name: '',
  location: '',
  type: '',
  criticality: '',
};

function toPayload(form: EquipmentFormValues): EquipmentPayload {
  return { ...form, criticality: Number(form.criticality) };
}

function formField(
  value: string,
  field: keyof EquipmentFormValues,
  errors: EquipmentValidationErrors,
  update: (field: keyof EquipmentFormValues, value: string) => void,
) {
  return (
    <div>
      <label className="label" htmlFor={`equipment-${field}`}>
        {field === 'equipment_id' ? 'Equipment ID' : field[0].toUpperCase() + field.slice(1)}
      </label>
      <input
        id={`equipment-${field}`}
        className="input"
        value={value}
        required
        type={field === 'criticality' ? 'number' : 'text'}
        min={field === 'criticality' ? 1 : undefined}
        max={field === 'criticality' ? 5 : undefined}
        aria-invalid={Boolean(errors[field]) || undefined}
        aria-describedby={errors[field] ? `equipment-${field}-error` : undefined}
        onChange={(event) => update(field, event.target.value)}
      />
      {errors[field] && (
        <p id={`equipment-${field}-error`} className="mt-1 text-xs text-red-700">
          {errors[field]}
        </p>
      )}
    </div>
  );
}

// PUBLIC_INTERFACE
export function EquipmentFormPage({ mode }: { mode: 'create' | 'edit' }) {
  /** Render the Admin-only Equipment create or edit form. */
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const admin = isAdminRole();
  const editing = mode === 'edit';
  const { data, loading, error, reload } = useEquipment(editing ? id : undefined);
  const { submit, submitting, error: submitError } = useEquipmentMutation();
  const [form, setForm] = useState<EquipmentFormValues>(emptyForm);
  const [errors, setErrors] = useState<EquipmentValidationErrors>({});

  useEffect(() => {
    if (data) {
      setForm({
        equipment_id: data.equipment_id,
        name: data.name,
        location: data.location,
        type: data.type,
        criticality: String(data.criticality),
      });
    }
  }, [data]);

  if (!admin) {
    return (
      <ErrorPanel
        title="Admin access required"
        error={new ApiError('Only Admin users can create or edit equipment.', 403, 'forbidden')}
      />
    );
  }

  if (editing && loading) {
    return <div className="card"><SkeletonRows rows={5} columns={2} /></div>;
  }

  if (editing && error) {
    return <ErrorPanel title="Unable to load equipment" error={error} onRetry={reload} />;
  }

  if (editing && !data) {
    return <EmptyState title="No equipment data" description="This equipment record could not be loaded." />;
  }

  const update = (field: keyof EquipmentFormValues, value: string) => {
    setForm((previous) => ({ ...previous, [field]: value }));
    setErrors((previous) => ({ ...previous, [field]: undefined }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const validationErrors = validateEquipmentForm(form);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    const saved = await submit(mode, id, toPayload(form));
    if (saved) navigate(`/equipment/${encodeURIComponent(saved.equipment_id)}`);
  };

  return (
    <section aria-labelledby="equipment-form-heading" className="space-y-4">
      <div>
        <h1 id="equipment-form-heading" className="text-xl font-semibold text-slate-900">
          {editing ? 'Edit equipment' : 'Add equipment'}
        </h1>
        <p className="mt-1 text-sm text-slate-600">Admin access is required for this action.</p>
      </div>

      {submitError && <ErrorPanel title="Could not save equipment" error={submitError} />}
      {errors.form && <p role="alert" className="text-sm text-red-700">{errors.form}</p>}

      <form className="card grid gap-4 p-4 sm:grid-cols-2" onSubmit={(event) => void handleSubmit(event)} noValidate>
        {formField(form.equipment_id, 'equipment_id', errors, update)}
        {formField(form.name, 'name', errors, update)}
        {formField(form.location, 'location', errors, update)}
        {formField(form.type, 'type', errors, update)}
        {formField(form.criticality, 'criticality', errors, update)}

        <div className="flex items-center gap-3 sm:col-span-2">
          <Button type="submit" loading={submitting}>{editing ? 'Save changes' : 'Create equipment'}</Button>
          <Link to={editing && id ? `/equipment/${encodeURIComponent(id)}` : '/equipment'} className="text-sm text-slate-600 hover:underline">
            Cancel
          </Link>
        </div>
      </form>
    </section>
  );
}
