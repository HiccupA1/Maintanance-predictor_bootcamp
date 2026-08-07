import { apiRequest } from './client';

/** Reading returned by the backend, including correction audit fields. */
export interface Reading {
  id: string;
  equipment_id: string;
  parameter_id: string;
  value: string;
  timestamp: string;
  entered_by: string;
  modified_by?: string | null;
  modified_at?: string | null;
  modification_reason?: string | null;
}

/** Payload used to create a manual reading. */
export interface ReadingCreatePayload {
  equipment_id: string;
  parameter_id: string;
  value: string;
  timestamp?: string | null;
}

/** Payload used to correct an existing reading. */
export interface ReadingUpdatePayload {
  value: string;
  modification_reason: string;
}

/** Values collected by the manual reading form. */
export interface ReadingFormValues {
  equipment_id: string;
  parameter_id: string;
  value: string;
}

/** Values collected by the correction form. */
export interface ReadingCorrectionValues {
  value: string;
  modification_reason: string;
}

/** Validation errors for the manual reading form. */
export type ReadingValidationErrors = Partial<
  Record<keyof ReadingFormValues | 'form', string>
>;

/** Validation errors for the correction form. */
export type ReadingCorrectionErrors = Partial<
  Record<keyof ReadingCorrectionValues | 'form', string>
>;

/**
 * Validate the required fields for a manual reading.
 *
 * @param form Current manual reading form values.
 * @returns Field-level errors, or an empty object when valid.
 */
// PUBLIC_INTERFACE
export function validateReadingForm(
  form: ReadingFormValues,
): ReadingValidationErrors {
  const errors: ReadingValidationErrors = {};

  if (!form.equipment_id.trim()) {
    errors.equipment_id = 'Equipment is required.';
  }

  if (!form.parameter_id.trim()) {
    errors.parameter_id = 'Parameter is required.';
  }

  if (!form.value.trim()) {
    errors.value = 'Value is required.';
  }

  return errors;
}

/**
 * Validate the required fields for a reading correction.
 *
 * @param form Current correction form values.
 * @returns Field-level errors, or an empty object when valid.
 */
// PUBLIC_INTERFACE
export function validateReadingCorrection(
  form: ReadingCorrectionValues,
): ReadingCorrectionErrors {
  const errors: ReadingCorrectionErrors = {};

  if (!form.value.trim()) {
    errors.value = 'Value is required.';
  }

  if (!form.modification_reason.trim()) {
    errors.modification_reason = 'Modification reason is required.';
  }

  return errors;
}

/**
 * Create a manual reading.
 *
 * @param payload Reading equipment, parameter, value, and optional timestamp.
 * @returns The newly created reading.
 */
// PUBLIC_INTERFACE
export function createReading(
  payload: ReadingCreatePayload,
): Promise<Reading> {
  return apiRequest<Reading>('/readings', {
    method: 'POST',
    body: payload,
  });
}

/**
 * List readings for an equipment parameter pair.
 *
 * The backend returns readings in reverse chronological order.
 *
 * @param equipmentId Public equipment identifier.
 * @param parameterId Parameter identifier.
 * @param signal Optional request cancellation signal.
 * @returns Readings newest first.
 */
// PUBLIC_INTERFACE
export function listReadings(
  equipmentId: string,
  parameterId: string,
  signal?: AbortSignal,
): Promise<Reading[]> {
  return apiRequest<Reading[]>(
    `/equipment/${encodeURIComponent(equipmentId)}/parameters/${encodeURIComponent(parameterId)}/readings`,
    { signal },
  );
}

/**
 * Correct a reading through the backend's five-minute correction window.
 *
 * @param readingId Reading identifier.
 * @param payload Replacement value and required audit reason.
 * @returns The corrected reading.
 */
// PUBLIC_INTERFACE
export function updateReading(
  readingId: string,
  payload: ReadingUpdatePayload,
): Promise<Reading> {
  return apiRequest<Reading>(`/readings/${encodeURIComponent(readingId)}`, {
    method: 'PUT',
    body: payload,
  });
}

// PUBLIC_INTERFACE
export function deleteReading(readingId: string): Promise<void> {
  /** Delete a reading; the backend enforces Operator authorization. */
  return apiRequest<void>(`/readings/${encodeURIComponent(readingId)}`, {
    method: 'DELETE',
  });
}
