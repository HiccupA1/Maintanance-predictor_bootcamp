/**
 * Types mirroring the backend Work Order contract.
 *
 * Source of truth:
 * - `Maintanance-predictor_bootcamp/app/schemas/work_orders.py`
 * - `Maintanance-predictor_bootcamp/app/schemas/common.py`
 *
 * IMPORTANT (live Supabase schema):
 * - `public.work_orders` has NO `alert_id` column (no FK link to alerts).
 * - There are no persisted part lines.
 * - There are no closure metadata fields (resolution_notes, root_cause, closed_at).
 * - There is no due_at column on the live table.
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
export interface WorkOrder {
  id: string;
  equipment_id?: string | null;
  equipment_name?: string | null;
  work_order_number: number;
  title: string;
  description?: string | null;
  priority: Priority;
  status: WorkOrderStatus;
  assigned_to?: string | null;
  closed_by?: string | null;
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
  /** Optional equipment id; may be ignored by the create-from-alert route. */
  equipment_id?: string | null;
  /** Optional description; the create-from-alert route may append alert context. */
  description?: string | null;
  priority: Priority;
}
/** Request body for `POST /v1/alerts/{alert_id}/work-orders`. */

// PUBLIC_INTERFACE
export interface WorkOrderUpdatePayload {
  title?: string;
  description?: string | null;
  priority?: Priority;
  status?: WorkOrderStatus;
  assigned_to?: string | null;
  closed_by?: string | null;
}
/** Request body for `PUT /v1/work-orders/{work_order_id}` (at least one field). */
