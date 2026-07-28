/**
 * Health API functions for the optional backend connectivity indicator.
 *
 * Endpoints: `GET /health` (liveness) and `GET /health/db` (readiness).
 * These are not versioned under `/v1`.
 */

import { apiRequestAbsolute } from './client';

// PUBLIC_INTERFACE
export interface HealthResponse {
  status: string;
  database?: string;
}
/** Payload returned by the health probes. */

// PUBLIC_INTERFACE
export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  /**
   * Check backend liveness.
   *
   * @param signal Optional abort signal.
   * @returns `{ status: "ok" }` when the service is running.
   * @throws {ApiError} When the service is unreachable or unhealthy.
   */
  return apiRequestAbsolute<HealthResponse>('/health', { signal });
}

// PUBLIC_INTERFACE
export function getDbHealth(signal?: AbortSignal): Promise<HealthResponse> {
  /**
   * Check backend database readiness.
   *
   * @param signal Optional abort signal.
   * @returns `{ status: "ok", database: "ok" }` when reachable.
   * @throws {ApiError} `dependency_unavailable` (503) when the DB is down.
   */
  return apiRequestAbsolute<HealthResponse>('/health/db', { signal });
}
