import { apiRequest } from './client';

/** A threshold parameter configured for a piece of equipment. */
export interface Parameter {
  id: string;
  equipment_id: string;
  name: string;
  unit: string;
  min_threshold: number | null;
  max_threshold: number | null;
  active: boolean;
  suggested_action: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

/** Values displayed and edited by the parameter form. */
export interface ParameterFormValues {
  name: string;
  unit: string;
  min_threshold: string;
  max_threshold: string;
  active: boolean;
  suggested_action: string;
}

/** JSON payload accepted by the parameter create and update endpoints. */
export interface ParameterPayload {
  name: string;
  unit: string;
  min_threshold: number | null;
  max_threshold: number | null;
  active: boolean;
  suggested_action: string | null;
}

/** Field-level validation errors for the parameter form. */
export type ParameterValidationErrors = Partial<
  Record<keyof ParameterFormValues | 'form', string>
>;

/**
 * Validate parameter fields before submitting them to the backend.
 *
 * The checks intentionally mirror the backend contract: name and unit are
 * required, at least one threshold is required, and a supplied range must be
 * ordered from minimum to maximum.
 *
 * @param form Current parameter form values.
 * @returns An empty object when valid, otherwise field-level messages.
 */
// PUBLIC_INTERFACE
export function validateParameterForm(
  form: ParameterFormValues,
): ParameterValidationErrors {
  const errors: ParameterValidationErrors = {};

  if (!form.name.trim()) {
    errors.name = 'Name is required.';
  }

  if (!form.unit.trim()) {
    errors.unit = 'Unit is required.';
  }

  const hasMin = form.min_threshold.trim() !== '';
  const hasMax = form.max_threshold.trim() !== '';

  if (!hasMin && !hasMax) {
    errors.form = 'At least one minimum or maximum threshold is required.';
  }

  const min = hasMin ? Number(form.min_threshold) : null;
  const max = hasMax ? Number(form.max_threshold) : null;

  if (hasMin && !Number.isFinite(min)) {
    errors.min_threshold = 'Minimum threshold must be a valid number.';
  }

  if (hasMax && !Number.isFinite(max)) {
    errors.max_threshold = 'Maximum threshold must be a valid number.';
  }

  if (
    min !== null &&
    max !== null &&
    Number.isFinite(min) &&
    Number.isFinite(max) &&
    min > max
  ) {
    errors.form = 'Minimum threshold must not exceed maximum threshold.';
  }

  return errors;
}

/** Convert validated form values into the backend request shape. */
function toPayload(form: ParameterFormValues): ParameterPayload {
  return {
    name: form.name.trim(),
    unit: form.unit.trim(),
    min_threshold: form.min_threshold.trim()
      ? Number(form.min_threshold)
      : null,
    max_threshold: form.max_threshold.trim()
      ? Number(form.max_threshold)
      : null,
    active: form.active,
    suggested_action: form.suggested_action.trim() || null,
  };
}

// PUBLIC_INTERFACE
export function listParameters(
  equipmentId: string,
  signal?: AbortSignal,
): Promise<Parameter[]> {
  /** Fetch all threshold parameters configured for one equipment record. */
  return apiRequest<Parameter[]>(
    `/equipment/${encodeURIComponent(equipmentId)}/parameters`,
    { signal },
  );
}

// PUBLIC_INTERFACE
export function createParameter(
  equipmentId: string,
  form: ParameterFormValues,
): Promise<Parameter> {
  /** Create a threshold parameter under an equipment record. */
  return apiRequest<Parameter>(
    `/equipment/${encodeURIComponent(equipmentId)}/parameters`,
    {
      method: 'POST',
      body: toPayload(form),
    },
  );
}

// PUBLIC_INTERFACE
export function updateParameter(
  parameterId: string,
  form: ParameterFormValues,
): Promise<Parameter> {
  /** Replace an existing threshold parameter configuration. */
  return apiRequest<Parameter>(
    `/parameters/${encodeURIComponent(parameterId)}`,
    {
      method: 'PUT',
      body: toPayload(form),
    },
  );
}
