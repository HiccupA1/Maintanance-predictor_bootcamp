/**
 * Centralised runtime configuration read from Vite environment variables.
 *
 * All configuration must come from the environment (`.env`), never from
 * hard-coded values inside components or API modules.
 */

import type { Role } from '../utils/rbac';

const DEFAULT_API_BASE_URL = 'http://localhost:8000';
const DEVELOPMENT_IDENTITY_STORAGE_KEY = 'maintenance-predictor.development-identity';

/** Trim a trailing slash so path joining stays predictable. */
function normalizeBaseUrl(value: string): string {
  return value.replace(/\/+$/, '');
}

/** Check that a runtime role matches the supported development RBAC roles. */
function isRole(value: unknown): value is Role {
  return DEVELOPMENT_ROLES.includes(value as Role);
}

/** Read a valid development identity override from browser storage. */
function readStoredDevelopmentIdentity(): DevelopmentIdentity | null {
  try {
    const rawValue = window.localStorage.getItem(DEVELOPMENT_IDENTITY_STORAGE_KEY);
    if (!rawValue) return null;

    const parsed: unknown = JSON.parse(rawValue);
    if (
      !parsed ||
      typeof parsed !== 'object' ||
      !isRole((parsed as Partial<DevelopmentIdentity>).role)
    ) {
      return null;
    }

    const name = (parsed as Partial<DevelopmentIdentity>).name;
    return {
      role: (parsed as DevelopmentIdentity).role,
      name: typeof name === 'string' && name.trim() ? name.trim() : 'Dev User',
    };
  } catch {
    return null;
  }
}

// PUBLIC_INTERFACE
export const API_BASE_URL: string = normalizeBaseUrl(
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
    DEFAULT_API_BASE_URL,
);
/** Base URL of the backend API, from `VITE_API_BASE_URL` (default localhost:8000). */

// PUBLIC_INTERFACE
export const API_VERSION_PREFIX = '/v1';
/** Version prefix used by all business endpoints of the backend contract. */

// PUBLIC_INTERFACE
export const USER_ROLE: string | undefined = (
  import.meta.env.VITE_USER_ROLE as string | undefined
)?.trim() || undefined;
/** Optional development role sent as the `X-User-Role` request header. */

// PUBLIC_INTERFACE
export const USER_NAME: string | undefined = (
  import.meta.env.VITE_USER_NAME as string | undefined
)?.trim() || undefined;
/** Optional development display name sent as the `X-User-Name` request header. */

// PUBLIC_INTERFACE
export const DEVELOPMENT_ROLES = [
  'Admin',
  'PlantManager',
  'Operator',
  'MaintenanceEngineer',
] as const satisfies readonly Role[];
/** Roles supported by the development identity switcher and backend RBAC shim. */

// PUBLIC_INTERFACE
export interface DevelopmentIdentity {
  /** Effective role sent to the development identity shim. */
  role: Role;
  /** Display name sent with the development identity shim request. */
  name: string;
}
/** Browser-persisted identity used only by the Vite development server. */

// PUBLIC_INTERFACE
export function getDevelopmentIdentity(): DevelopmentIdentity {
  /**
   * Return the effective local development identity.
   *
   * A stored developer selection takes precedence over Vite environment
   * defaults. When no role is configured, this mirrors the backend's
   * PlantManager fallback.
   *
   * @returns The role and display name for development API requests.
   */
  const storedIdentity = readStoredDevelopmentIdentity();
  if (storedIdentity) return storedIdentity;

  return {
    role: isRole(USER_ROLE) ? USER_ROLE : 'PlantManager',
    name: USER_NAME || 'Dev User',
  };
}

// PUBLIC_INTERFACE
export function setDevelopmentRole(role: Role): void {
  /**
   * Persist a Vite-development role selection for subsequent API requests.
   *
   * @param role One of the roles recognized by the backend development shim.
   */
  const identity: DevelopmentIdentity = {
    role,
    name: `${role} Dev`,
  };
  window.localStorage.setItem(
    DEVELOPMENT_IDENTITY_STORAGE_KEY,
    JSON.stringify(identity),
  );
}

// PUBLIC_INTERFACE
export function getRequestIdentity(): {
  role?: string;
  name?: string;
} {
  /**
   * Return the identity headers used by the shared API client.
   *
   * In Vite development, the in-app switcher overrides the configured role.
   * Production builds continue to use only environment-provided values.
   *
   * @returns Optional role and name values for development request headers.
   */
  if (import.meta.env.DEV) {
    return getDevelopmentIdentity();
  }

  return { role: USER_ROLE, name: USER_NAME };
}

// PUBLIC_INTERFACE
export const MAX_PAGE_SIZE = 200;
/** Maximum `page_size` accepted by the backend list endpoint. */

// PUBLIC_INTERFACE
export const DEFAULT_PAGE_SIZE = 20;
/** Default `page_size` used by the work orders list screen. */
