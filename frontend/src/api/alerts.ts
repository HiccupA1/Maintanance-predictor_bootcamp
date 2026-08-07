/**
 * Alerts API functions.
 *
 * Endpoints:
 * - GET /v1/alerts
 * - GET /v1/alerts/{alert_id}
 */

import { apiRequest } from './client';

// PUBLIC_INTERFACE
export interface Alert {
  /** Alert UUID. */
  id: string;
  /** Backend equipment UUID. */
  equipment_id: string;
  /** Human-readable equipment name supplied by the backend. */
  equipment_name?: string | null;
  /** Backend parameter UUID, when available. */
  parameter_id?: string | null;
  /** Human-readable parameter name supplied by the backend. */
  parameter_name?: string | null;
  /** Alert lifecycle status. */
  status: string;
  /** Alert priority. */
  priority: string;
  /** Current breached value. */
  current_value?: string | null;
  /** Timestamp at which the threshold breach occurred. */
  breach_timestamp?: string | null;
  /** Configured minimum threshold. */
  min_threshold?: number | null;
  /** Configured maximum threshold. */
  max_threshold?: number | null;
  /** Recommended maintenance action. */
  suggested_action?: string | null;
  /** Explanation for the assigned priority. */
  why_priority?: string | null;
  /** User or process that issued the alert. */
  issuer_name?: string | null;
  /** Equipment or machine context captured with the alert. */
  machine_details?: Record<string, unknown> | null;
  /** Reading snapshot captured with the alert. */
  readings_snapshot?: Record<string, unknown> | null;
  /** Alert creation timestamp. */
  created_at: string;
  /** Alert last-update timestamp. */
  updated_at: string;
}

/** Alert collection response returned by GET /v1/alerts. */
export type AlertListResponse = Alert[];

// PUBLIC_INTERFACE
export function listAlerts(signal?: AbortSignal): Promise<AlertListResponse> {
  /**
   * Fetch all alerts, ordered newest first by the backend.
   *
   * @param signal Optional request cancellation signal.
   * @returns The alert collection.
   */
  return apiRequest<AlertListResponse>('/alerts', { signal });
}

// PUBLIC_INTERFACE
export function getAlert(alertId: string, signal?: AbortSignal): Promise<Alert> {
  /**
   * Fetch one alert by id.
   *
   * @param alertId Alert UUID from the route.
   * @param signal Optional request cancellation signal.
   * @returns The requested alert.
   * @throws {ApiError} When the alert is missing or the request fails.
   */
  return apiRequest<Alert>(`/alerts/${encodeURIComponent(alertId)}`, { signal });
}

// PUBLIC_INTERFACE
export function deleteAlert(alertId: string): Promise<void> {
  /** Delete an alert; the backend enforces Plant Manager authorization. */
  return apiRequest<void>(`/alerts/${encodeURIComponent(alertId)}`, {
    method: 'DELETE',
  });
}
