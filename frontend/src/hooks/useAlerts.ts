/**
 * Hooks encapsulating alert data access and request state.
 */

import { useCallback, useEffect, useState } from 'react';

import { getAlert, listAlerts, type Alert } from '../api/alerts';

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

// PUBLIC_INTERFACE
export interface AlertAsyncState<T> {
  /** Loaded response, or null before a successful response. */
  data: T | null;
  /** Whether the request is currently running. */
  loading: boolean;
  /** Request failure, if any. */
  error: unknown;
  /** Re-run the request. */
  reload: () => void;
}

/** Common asynchronous state returned by alert read hooks. */

// PUBLIC_INTERFACE
export function useAlertList(): AlertAsyncState<Alert[]> {
  /**
   * Load the alert collection.
   *
   * @returns Alert collection request state.
   */
  const [data, setData] = useState<Alert[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    void listAlerts(controller.signal)
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

  const reload = useCallback(() => setNonce((value) => value + 1), []);
  return { data, loading, error, reload };
}

// PUBLIC_INTERFACE
export function useAlert(alertId: string | undefined): AlertAsyncState<Alert> {
  /**
   * Load one alert by its route id.
   *
   * @param alertId Alert UUID, or undefined when the route is incomplete.
   * @returns Alert request state.
   */
  const [data, setData] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(Boolean(alertId));
  const [error, setError] = useState<unknown>(null);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!alertId) {
      setData(null);
      setError(new Error('Missing alert id.'));
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setError(null);

    void getAlert(alertId, controller.signal)
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
  }, [alertId, nonce]);

  const reload = useCallback(() => setNonce((value) => value + 1), []);
  return { data, loading, error, reload };
}
