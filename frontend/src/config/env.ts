/**
 * Centralised runtime configuration read from Vite environment variables.
 *
 * Authentication is intentionally Supabase-only. The former development
 * identity shim could make the UI appear authenticated while API requests were
 * unauthenticated, which hid tables and role-gated inputs.
 */

const DEFAULT_API_BASE_URL = 'http://localhost:8000';

function normalizeBaseUrl(value: string): string {
  return value.replace(/\/+$/, '').replace(/\/v1$/, '');
}

// PUBLIC_INTERFACE
export const API_BASE_URL: string = normalizeBaseUrl(
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
    DEFAULT_API_BASE_URL,
);
/** Base URL of the backend API, from `VITE_API_BASE_URL`. */

// PUBLIC_INTERFACE
export const API_VERSION_PREFIX = '/v1';
/** Version prefix used by business endpoints. */

// PUBLIC_INTERFACE
export const MAX_PAGE_SIZE = 200;
/** Maximum page size accepted by the backend list endpoints. */

// PUBLIC_INTERFACE
export const DEFAULT_PAGE_SIZE = 20;
/** Default page size used by list screens. */

// PUBLIC_INTERFACE
export type AuthMode = 'supabase';
/** Browser authentication mode. Supabase is the only supported mode. */

// PUBLIC_INTERFACE
export const AUTH_MODE: AuthMode = 'supabase';
/** Effective browser authentication mode. */

// PUBLIC_INTERFACE
export const SUPABASE_URL: string | undefined = (
  import.meta.env.VITE_SUPABASE_URL as string | undefined
)?.trim();
/** Supabase project URL. */

// PUBLIC_INTERFACE
export const SUPABASE_ANON_KEY: string | undefined = (
  import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined
)?.trim();
/** Supabase anonymous browser key. */
