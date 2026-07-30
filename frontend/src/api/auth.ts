/**
 * Authentication and current-user API functions.
 *
 * The MVP uses the backend development RBAC shim at `GET /v1/me`.
 */

import { apiRequest } from './client';
import type { Role } from '../utils/rbac';

// PUBLIC_INTERFACE
export interface CurrentUser {
  /** Stable backend user identifier. */
  user_id: string;
  /** Display name resolved by the backend. */
  name: string;
  /** Effective RBAC role for the current request. */
  role: Role;
}
/** Current-user payload returned by `GET /v1/me`. */

// PUBLIC_INTERFACE
export function getMe(signal?: AbortSignal): Promise<CurrentUser> {
  /**
   * Fetch the effective development user identity and role.
   *
   * @param signal Optional abort signal for cancelling the request.
   * @returns The current user returned by the backend RBAC shim.
   * @throws {ApiError} When the backend is unavailable or rejects the request.
   */
  return apiRequest<CurrentUser>('/me', { signal });
}
