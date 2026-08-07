/**
 * Work Orders API functions.
 *
 * Endpoints (must match the backend contract exactly):
 * - GET    /v1/work-orders
 * - GET    /v1/work-orders/{work_order_id}
 * - PUT    /v1/work-orders/{work_order_id}
 * - POST   /v1/alerts/{alert_id}/work-orders
 */

import { DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE } from '../config/env';
import { apiRequest } from './client';
import type {
  WorkOrder,
  WorkOrderCreatePayload,
  WorkOrderListParams,
  WorkOrderListResponse,
  WorkOrderUpdatePayload,
} from '../types/workOrders';

// PUBLIC_INTERFACE
export function clampPageSize(pageSize: number | undefined): number {
  /**
   * Clamp a requested page size into the backend-accepted range.
   *
   * @param pageSize Requested page size (may be undefined or out of range).
   * @returns A page size between 1 and {@link MAX_PAGE_SIZE}.
   */
  if (!pageSize || Number.isNaN(pageSize)) return DEFAULT_PAGE_SIZE;
  return Math.min(Math.max(Math.trunc(pageSize), 1), MAX_PAGE_SIZE);
}

// PUBLIC_INTERFACE
export function listWorkOrders(
  params: WorkOrderListParams = {},
  signal?: AbortSignal,
): Promise<WorkOrderListResponse> {
  /**
   * List work orders with pagination and optional filters.
   *
   * @param params Page, page size (clamped to <= 200), status, priority and
   *   created_from/created_to window.
   * @param signal Optional abort signal.
   * @returns The paginated work order list response.
   * @throws {ApiError} On validation failure or transport error.
   */
  return apiRequest<WorkOrderListResponse>('/work-orders', {
    query: {
      page: Math.max(params.page ?? 1, 1),
      page_size: clampPageSize(params.page_size),
      status: params.status || undefined,
      priority: params.priority || undefined,
      created_from: params.created_from || undefined,
      created_to: params.created_to || undefined,
    },
    signal,
  });
}

// PUBLIC_INTERFACE
export function getWorkOrder(
  workOrderId: string,
  signal?: AbortSignal,
): Promise<WorkOrder> {
  /**
   * Fetch a single work order by id.
   *
   * @param workOrderId UUID string of the work order.
   * @param signal Optional abort signal.
   * @returns The full work order.
   * @throws {ApiError} `work_order_not_found` (404) when it does not exist.
   */
  return apiRequest<WorkOrder>(`/work-orders/${encodeURIComponent(workOrderId)}`, {
    signal,
  });
}

// PUBLIC_INTERFACE
export function updateWorkOrder(
  workOrderId: string,
  payload: WorkOrderUpdatePayload,
): Promise<WorkOrder> {
  /**
   * Apply a partial update to a work order.
   *
   * @param workOrderId UUID string of the work order.
   * @param payload At least one field; empty bodies are rejected (422).
   * @returns The updated work order.
   * @throws {ApiError} 404 when missing, 409 when closed, 422 when invalid.
   */
  return apiRequest<WorkOrder>(`/work-orders/${encodeURIComponent(workOrderId)}`, {
    method: 'PUT',
    body: payload,
  });
}

// PUBLIC_INTERFACE
export function createWorkOrderFromAlert(
  alertId: string,
  payload: WorkOrderCreatePayload,
): Promise<WorkOrder> {
  /**
   * Convert an alert into a work order.
   *
   * @param alertId UUID string of the source alert.
   * @param payload Description and priority (live schema has no due_at/parts).
   * @returns The created work order (HTTP 201).
   * @throws {ApiError} `alert_not_found` (404), `duplicate_work_order` (409),
   *   or `invalid_request` (422).
   */
  return apiRequest<WorkOrder>(
    `/alerts/${encodeURIComponent(alertId)}/work-orders`,
    { method: 'POST', body: payload },
  );
}
