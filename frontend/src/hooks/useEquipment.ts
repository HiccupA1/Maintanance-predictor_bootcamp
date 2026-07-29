import { useCallback, useEffect, useState } from 'react';

import {
  createEquipment,
  getEquipment,
  listEquipment,
  updateEquipment,
} from '../api/equipment';
import type {
  Equipment,
  EquipmentFormValues,
  EquipmentListResponse,
  EquipmentPayload,
  EquipmentValidationErrors,
} from '../types/equipment';

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

// PUBLIC_INTERFACE
export interface EquipmentAsyncState<T> {
  data: T | null;
  loading: boolean;
  error: unknown;
  reload: () => void;
}

// PUBLIC_INTERFACE
export function useEquipmentList(): EquipmentAsyncState<EquipmentListResponse> {
  /** Load the Equipment list and expose explicit request state. */
  const [data, setData] = useState<EquipmentListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    listEquipment(controller.signal)
      .then((response) => {
        setData(response);
        setLoading(false);
      })
      .catch((requestError: unknown) => {
        if (isAbort(requestError)) return;
        setData(null);
        setError(requestError);
        setLoading(false);
      });

    return () => controller.abort();
  }, [nonce]);

  return {
    data,
    loading,
    error,
    reload: useCallback(() => setNonce((value) => value + 1), []),
  };
}

// PUBLIC_INTERFACE
export function useEquipment(
  equipmentId: string | undefined,
): EquipmentAsyncState<Equipment> {
  /** Load one Equipment record and expose explicit request state. */
  const [data, setData] = useState<Equipment | null>(null);
  const [loading, setLoading] = useState(Boolean(equipmentId));
  const [error, setError] = useState<unknown>(null);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!equipmentId) {
      setData(null);
      setError(new Error('Missing equipment id.'));
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setError(null);

    getEquipment(equipmentId, controller.signal)
      .then((response) => {
        setData(response);
        setLoading(false);
      })
      .catch((requestError: unknown) => {
        if (isAbort(requestError)) return;
        setData(null);
        setError(requestError);
        setLoading(false);
      });

    return () => controller.abort();
  }, [equipmentId, nonce]);

  return {
    data,
    loading,
    error,
    reload: useCallback(() => setNonce((value) => value + 1), []),
  };
}

// PUBLIC_INTERFACE
export function useEquipmentMutation() {
  /** Submit Equipment create/update mutations with loading and error state. */
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const submit = useCallback(
    async (
      mode: 'create' | 'update',
      equipmentId: string | undefined,
      payload: EquipmentPayload,
    ): Promise<Equipment | null> => {
      setSubmitting(true);
      setError(null);
      try {
        return mode === 'create'
          ? await createEquipment(payload)
          : await updateEquipment(equipmentId ?? '', payload);
      } catch (requestError) {
        setError(requestError);
        return null;
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  return {
    submit,
    submitting,
    error,
    reset: () => setError(null),
  };
}

// PUBLIC_INTERFACE
export function validateEquipmentForm(
  form: EquipmentFormValues,
): EquipmentValidationErrors {
  /** Validate required fields and the inclusive 1–5 criticality range. */
  const errors: EquipmentValidationErrors = {};
  const requiredFields: Array<keyof EquipmentFormValues> = [
    'equipment_id',
    'name',
    'location',
    'type',
  ];

  requiredFields.forEach((field) => {
    if (!form[field].trim()) {
      errors[field] = 'This field is required.';
    }
  });

  const criticality = Number(form.criticality);
  if (!form.criticality.trim()) {
    errors.criticality = 'Criticality is required.';
  } else if (!Number.isInteger(criticality) || criticality < 1 || criticality > 5) {
    errors.criticality = 'Criticality must be an integer from 1 to 5.';
  }

  return errors;
}
