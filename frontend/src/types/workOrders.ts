/**
 * Types mirroring the backend Work Order contract.
 *
 * Source of truth: `Maintanance-predictor_bootcamp/app/schemas/work_orders.py`
 * and `app/schemas/common.py`. Kept minimal but exact (field names and
 * uppercase enum values must match the API).
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
export interface WorkOrderPartLine {
  /** Unique part-line id (UUID string). */
  id: string;
  /** Name or identifier of the spare part. */
  part_name: string;
  /** Whether the part was actually used. */
  used: boolean;
  /** Optional free-text notes. */
  notes?: string | null;
}
/** Spare-part line as returned by the API. */

// PUBLIC_INTERFACE
export interface WorkOrderPartLineInput {
  part_name: string;
  used: boolean;
  notes?: string | null;
}
/** Spare-part line payload used on create/update requests. */

// PUBLIC_INTERFACE
export interface WorkOrder {
  id: string;
  alert_id: string;
  equipment_id: string;
  description: string;
  priority: Priority;
  status: WorkOrderStatus;
  issuer_name?: string | null;
  due_at?: string | null;
  machine_details?: Record<string, unknown> | null;
  readings_snapshot?: Record<string, unknown> | null;
  resolution_notes?: string | null;
  root_cause?: string | null;
  closed_at?: string | null;
  created_at: string;
  updated_at: string;
  parts: WorkOrderPartLine[];
}
/** Full work order representation (detail / create / update responses). */

// PUBLIC_INTERFACE
export interface WorkOrderSummary {
  id: string;
  alert_id: string;
  equipment_id: string;
  priority: Priority;
  status: WorkOrderStatus;
  due_at?: string | null;
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
  description: string;
  priority: Priority;
  due_at?: string | null;
  parts?: WorkOrderPartLineInput[];
}
/** Request body for `POST /v1/alerts/{alert_id}/work-orders`. */

// PUBLIC_INTERFACE
export interface WorkOrderUpdatePayload {
  description?: string;
  priority?: Priority;
  status?: WorkOrderStatus;
  due_at?: string | null;
  resolution_notes?: string | null;
  root_cause?: string | null;
  parts?: WorkOrderPartLineInput[];
}
/** Request body for `PUT /v1/work-orders/{work_order_id}` (at least one field). */
