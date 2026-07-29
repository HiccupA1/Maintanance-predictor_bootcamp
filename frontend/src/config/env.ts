/**
 * Centralised runtime configuration read from Vite environment variables.
 *
 * All configuration must come from the environment (`.env`), never from
 * hard-coded values inside components or API modules.
 */

const DEFAULT_API_BASE_URL = 'http://localhost:8000';

/** Trim a trailing slash so path joining stays predictable. */
function normalizeBaseUrl(value: string): string {
  return value.replace(/\/+$/, '');
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
export const MAX_PAGE_SIZE = 200;
/** Maximum `page_size` accepted by the backend list endpoint. */

// PUBLIC_INTERFACE
export const DEFAULT_PAGE_SIZE = 20;
/** Default `page_size` used by the work orders list screen. */
