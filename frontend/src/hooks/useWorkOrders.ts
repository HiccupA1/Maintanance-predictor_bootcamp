/**
 * Hooks encapsulating Work Orders data access and request state.
 *
 * Components stay presentational: they consume `{ data, loading, error }` and
 * call the returned actions. All fetch logic lives in `src/api/*`.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  clampPageSize,
  createWorkOrderFromAlert,
  getWorkOrder,
  listWorkOrders,
  updateWorkOrder,
} from '../api/workOrders';
import type {
  WorkOrder,
  WorkOrderCreatePayload,
  WorkOrderListParams,
  WorkOrderListResponse,
  WorkOrderUpdatePayload,
} from '../types/workOrders';

/** Ignore errors caused by an intentional request abort. */
function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

// PUBLIC_INTERFACE
export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: unknown;
  reload: () => void;
}
/** Common shape returned by the read hooks. */

// PUBLIC_INTERFACE
export function useWorkOrderList(
  params: WorkOrderListParams,
): AsyncState<WorkOrderListResponse> {
  /**
   * Load a page of work orders, refetching whenever the params change.
   *
   * @param params Page, page size, and optional filters.
   * @returns Async state with the paginated response and a `reload` action.
   */
  const [data, setData] = useState<WorkOrderListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<unknown>(null);
  const [nonce, setNonce] = useState(0);

  const queryKey = useMemo(
    () =>
      JSON.stringify({
        page: Math.max(params.page ?? 1, 1),
        page_size: clampPageSize(params.page_size),
        status: params.status || '',
        priority: params.priority || '',
        created_from: params.created_from || '',
        created_to: params.created_to || '',
      }),
    [
      params.page,
      params.page_size,
      params.status,
      params.priority,
      params.created_from,
      params.created_to,
    ],
  );

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    listWorkOrders(JSON.parse(queryKey) as WorkOrderListParams, controller.signal)
      .then((response) => {
        setData(response);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (isAbort(err)) return;
        setError(err);
        setData(null);
        setLoading(false);
      });
    return () => controller.abort();
  }, [queryKey, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { data, loading, error, reload };
}

// PUBLIC_INTERFACE
export function useWorkOrder(workOrderId: string | undefined): AsyncState<WorkOrder> {
  /**
   * Load a single work order by id.
   *
   * @param workOrderId UUID string from the route; when undefined no request
   *   is made and an error state is produced.
   * @returns Async state with the work order and a `reload` action.
   */
  const [data, setData] = useState<WorkOrder | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(workOrderId));
  const [error, setError] = useState<unknown>(null);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!workOrderId) {
      setData(null);
      setLoading(false);
      setError(new Error('Missing work order id.'));
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getWorkOrder(workOrderId, controller.signal)
      .then((response) => {
        setData(response);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (isAbort(err)) return;
        setError(err);
        setData(null);
        setLoading(false);
      });
    return () => controller.abort();
  }, [workOrderId, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { data, loading, error, reload };
}

// PUBLIC_INTERFACE
export interface MutationState<TArgs extends unknown[], TResult> {
  submit: (...args: TArgs) => Promise<TResult | null>;
  submitting: boolean;
  error: unknown;
  reset: () => void;
}
/** Common shape returned by the write hooks. */

// PUBLIC_INTERFACE
export function useUpdateWorkOrder(): MutationState<
  [string, WorkOrderUpdatePayload],
  WorkOrder
> {
  /**
   * Submit a work order update.
   *
   * @returns `submit(workOrderId, payload)` plus submitting/error state. On
   *   failure the error is captured (not thrown) and `null` is returned.
   */
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const submit = useCallback(
    async (workOrderId: string, payload: WorkOrderUpdatePayload) => {
      setSubmitting(true);
      setError(null);
      try {
        return await updateWorkOrder(workOrderId, payload);
      } catch (err: unknown) {
        setError(err);
        return null;
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  return { submit, submitting, error, reset: () => setError(null) };
}

// PUBLIC_INTERFACE
export function useConvertAlertToWorkOrder(): MutationState<
  [string, WorkOrderCreatePayload],
  WorkOrder
> {
  /**
   * Submit an alert-to-work-order conversion.
   *
   * @returns `submit(alertId, payload)` plus submitting/error state. On
   *   failure the error is captured (not thrown) and `null` is returned.
   */
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const submit = useCallback(
    async (alertId: string, payload: WorkOrderCreatePayload) => {
      setSubmitting(true);
      setError(null);
      try {
        return await createWorkOrderFromAlert(alertId, payload);
      } catch (err: unknown) {
        setError(err);
        return null;
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  return { submit, submitting, error, reset: () => setError(null) };
}
