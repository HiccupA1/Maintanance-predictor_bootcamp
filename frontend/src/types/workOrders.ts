/**
 * Types mirroring the backend Work Order contract.
 *
 * Source of truth:
 * - `Maintanance-predictor_bootcamp/app/schemas/work_orders.py`
 * - `Maintanance-predictor_bootcamp/app/schemas/common.py`
 *
 * Closure (FR9-FR10, migration 0002): setting status CLOSED requires
 * resolution_notes, root_cause and failure_confirmed (+ failure_mode when a
 * failure is confirmed). These labels train the risk model (ADR-0006).
 * Spare-parts lines are not yet persisted.
 */

// PUBLIC_INTERFACE
export type Priority = 'CRITICAL' | 'HIGH' | 'MEDIUM';
/** Work order priority values accepted/returned by the backend. */

// PUBLIC_INTERFACE
export type WorkOrderStatus = 'OPEN' | 'CLOSED';
/** Work order lifecycle status values accepted/returned by the backend. */

// PUBLIC_INTERFACE
export const PRIORITIES: Priority[] = ['CRITICAL', 'HIGH', 'MEDIUM'];
/** Ordered list of priorities for select inputs and filters. */

// PUBLIC_INTERFACE
export const WORK_ORDER_STATUSES: WorkOrderStatus[] = ['OPEN', 'CLOSED'];
/** Ordered list of statuses for select inputs and filters. */

// PUBLIC_INTERFACE
export type FailureMode = 'TWF' | 'HDF' | 'PWF' | 'OSF' | 'RNF' | 'OTHER';
/** Failure modes recorded at closure (AI4I taxonomy plus OTHER). */

// PUBLIC_INTERFACE
export const FAILURE_MODES: { value: FailureMode; label: string }[] = [
  { value: 'TWF', label: 'Tool wear' },
  { value: 'HDF', label: 'Heat dissipation' },
  { value: 'PWF', label: 'Power' },
  { value: 'OSF', label: 'Overstrain' },
  { value: 'RNF', label: 'Random / unexplained' },
  { value: 'OTHER', label: 'Other' },
];

// PUBLIC_INTERFACE
export interface WorkOrder {
  id: string;
  equipment_id?: string | null;
  equipment_name?: string | null;
  /** Not returned by the API since schema reconciliation; lists number rows by position. */
  work_order_number?: number;
  title: string;
  description?: string | null;
  priority: Priority;
  status: WorkOrderStatus;
  assigned_to?: string | null;
  closed_by?: string | null;
  alert_id?: string | null;
  resolution_notes?: string | null;
  root_cause?: string | null;
  closed_at?: string | null;
  failure_confirmed?: boolean | null;
  failure_mode?: FailureMode | null;
  created_at: string;
  updated_at: string;
}
/** Full work order representation (detail / create / update responses). */

// PUBLIC_INTERFACE
export interface WorkOrderSummary {
  id: string;
  equipment_id?: string | null;
  equipment_name?: string | null;
  work_order_number: number;
  title: string;
  priority: Priority;
  status: WorkOrderStatus;
  created_at: string;
}
/** Condensed work order representation used in list responses. */

// PUBLIC_INTERFACE
export interface WorkOrderListResponse {
  items: WorkOrderSummary[];
  total: number;
  page: number;
  page_size: number;
}
/** Paginated list payload returned by `GET /v1/work-orders`. */

// PUBLIC_INTERFACE
export interface WorkOrderListParams {
  page?: number;
  page_size?: number;
  status?: WorkOrderStatus | '';
  priority?: Priority | '';
  created_from?: string;
  created_to?: string;
}
/** Query parameters supported by the work orders list endpoint. */

// PUBLIC_INTERFACE
export interface WorkOrderCreatePayload {
  /** Required title; backend persists to public.work_orders. */
  title: string;
  /** Optional equipment id. */
  equipment_id?: string | null;
  /** Optional description. */
  description?: string | null;
  priority: Priority;
  /** Source alert (FR7); one work order per alert. */
  alert_id?: string | null;
}
/** Request body for `POST /v1/work-orders`. */

// PUBLIC_INTERFACE
export interface WorkOrderUpdatePayload {
  title?: string;
  description?: string | null;
  priority?: Priority;
  status?: WorkOrderStatus;
  assigned_to?: string | null;
  closed_by?: string | null;
  resolution_notes?: string;
  root_cause?: string;
  failure_confirmed?: boolean;
  failure_mode?: FailureMode;
}
/** Request body for `PUT /v1/work-orders/{work_order_id}` (at least one field). */
