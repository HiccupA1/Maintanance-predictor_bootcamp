/**
 * Shared HTTP client for the backend API.
 *
 * Responsibilities:
 * - Build absolute URLs from the env-driven base URL and the `/v1` prefix.
 * - Serialize/deserialize JSON.
 * - Add optional development RBAC identity headers.
 * - Normalize backend RFC7807 "problem+json" errors into a single `ApiError`
 *   type so UI code never has to parse raw responses or show stack traces.
 */

import {
  API_BASE_URL,
  API_VERSION_PREFIX,
  getRequestIdentity,
} from '../config/env';

/** Build optional development identity headers without sending empty values. */
function userHeaders(): Record<string, string> {
  const { role, name } = getRequestIdentity();
  return {
    ...(role ? { 'X-User-Role': role } : {}),
    ...(name ? { 'X-User-Name': name } : {}),
  };
}

// PUBLIC_INTERFACE
export interface ProblemErrorItem {
  field?: string | null;
  message: string;
  rule?: string | null;
  expected?: string | null;
}
/** A single field-level error entry from the backend `errors[]` array. */

// PUBLIC_INTERFACE
export interface Problem {
  type?: string;
  title?: string;
  status: number;
  detail?: string | null;
  instance?: string | null;
  code?: string;
  correlation_id?: string | null;
  errors?: ProblemErrorItem[];
}
/** RFC7807-like problem envelope returned by the backend on every error. */

// PUBLIC_INTERFACE
export class ApiError extends Error {
  /** HTTP status code (0 when the request never reached the server). */
  readonly status: number;

  /** Stable machine-readable backend error code, when available. */
  readonly code: string;

  /** Full problem envelope, when the backend returned one. */
  readonly problem?: Problem;

  /** Field-level messages keyed by field name, for inline form errors. */
  readonly fieldErrors: Record<string, string>;

  /**
   * Create a normalized API error.
   *
   * @param message User-readable message (never a stack trace).
   * @param status HTTP status code, or 0 for network/parse failures.
   * @param code Machine-readable error code.
   * @param problem Optional raw problem envelope.
   */
  constructor(message: string, status: number, code: string, problem?: Problem) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.problem = problem;
    this.fieldErrors = {};
    for (const item of problem?.errors ?? []) {
      if (item.field) {
        this.fieldErrors[item.field] = item.message;
      }
    }
  }

  // PUBLIC_INTERFACE
  /** True when the resource was not found (404 / *_not_found codes). */
  get isNotFound(): boolean {
    return (
      this.status === 404 ||
      this.code === 'work_order_not_found' ||
      this.code === 'alert_not_found' ||
      this.code === 'equipment_not_found'
    );
  }

  // PUBLIC_INTERFACE
  /** True when the request conflicted with current state (409). */
  get isConflict(): boolean {
    return this.status === 409;
  }

  // PUBLIC_INTERFACE
  /** True when the request failed validation (422). */
  get isValidation(): boolean {
    return this.status === 422;
  }
}
/** Normalized error thrown by every API function in `src/api/*`. */

/** Values accepted as query parameters. */
type QueryValue = string | number | boolean | null | undefined;

// PUBLIC_INTERFACE
export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  /** JSON-serializable request body. */
  body?: unknown;
  /** Query parameters; empty/null/undefined values are omitted. */
  query?: Record<string, QueryValue>;
  /** Abort signal so callers can cancel in-flight requests. */
  signal?: AbortSignal;
}
/** Options accepted by {@link apiRequest}. */

/** Build a fully-qualified URL including query string. */
function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(
    `${API_BASE_URL}${API_VERSION_PREFIX}${normalizedPath}`.replace(
      /([^:]\/)\/+/g,
      '$1',
    ),
  );
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null || value === '') continue;
    url.searchParams.set(key, String(value));
  }
  return url.toString();
}

/** Best-effort JSON parse; returns undefined for empty/non-JSON bodies. */
async function parseJsonSafely(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return undefined;
  }
}

/** Turn a problem envelope (or fallback) into a user-readable message. */
function messageFromProblem(problem: Problem | undefined, status: number): string {
  if (problem) {
    const fieldMessages = (problem.errors ?? [])
      .map((e) => (e.field ? `${e.field}: ${e.message}` : e.message))
      .filter(Boolean);
    return (
      problem.detail ||
      problem.title ||
      (fieldMessages.length > 0 ? fieldMessages.join('; ') : '') ||
      `Request failed with status ${status}.`
    );
  }
  return `Request failed with status ${status}.`;
}

// PUBLIC_INTERFACE
export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  /**
   * Perform a JSON request against the backend API.
   *
   * @param path Path relative to the `/v1` prefix, e.g. `/work-orders`.
   * @param options Method, JSON body, query params, and abort signal.
   * @returns The parsed JSON response body typed as `T` (or `undefined` cast
   *   to `T` when the response has no content).
   * @throws {ApiError} For network failures and for any non-2xx response,
   *   with the backend problem details normalized.
   */
  const { method = 'GET', body, query, signal } = options;

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      signal,
      headers: {
        Accept: 'application/json',
        ...userHeaders(),
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    // Re-throw aborts untouched so callers can ignore cancelled requests.
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error;
    }
    throw new ApiError(
      'Unable to reach the server. Check your connection and that the API is running.',
      0,
      'network_error',
    );
  }

  const payload = await parseJsonSafely(response);

  if (!response.ok) {
    const problem: Problem | undefined =
      payload && typeof payload === 'object'
        ? { status: response.status, ...(payload as Partial<Problem>) }
        : undefined;
    throw new ApiError(
      messageFromProblem(problem, response.status),
      response.status,
      problem?.code ?? 'unexpected_error',
      problem,
    );
  }

  return payload as T;
}

// PUBLIC_INTERFACE
export async function apiRequestAbsolute<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  /**
   * Perform a JSON request against a non-versioned path (e.g. `/health`).
   *
   * @param path Path relative to the API base URL, without the `/v1` prefix.
   * @param options Method, JSON body, query params, and abort signal.
   * @returns The parsed JSON response body typed as `T`.
   * @throws {ApiError} On network failure or non-2xx response.
   */
  const normalized = path.startsWith('/') ? path : `/${path}`;
  // Reuse apiRequest by temporarily bypassing the version prefix.
  const { method = 'GET', body, query, signal } = options;
  const url = new URL(`${API_BASE_URL}${normalized}`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null || value === '') continue;
    url.searchParams.set(key, String(value));
  }

  let response: Response;
  try {
    response = await fetch(url.toString(), {
      method,
      signal,
      headers: {
        Accept: 'application/json',
        ...userHeaders(),
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error;
    }
    throw new ApiError(
      'Unable to reach the server. Check your connection and that the API is running.',
      0,
      'network_error',
    );
  }

  const payload = await parseJsonSafely(response);
  if (!response.ok) {
    const problem: Problem | undefined =
      payload && typeof payload === 'object'
        ? { status: response.status, ...(payload as Partial<Problem>) }
        : undefined;
    throw new ApiError(
      messageFromProblem(problem, response.status),
      response.status,
      problem?.code ?? 'unexpected_error',
      problem,
    );
  }
  return payload as T;
}

// PUBLIC_INTERFACE
export function toUserMessage(error: unknown): string {
  /**
   * Convert any thrown value into a user-readable message.
   *
   * @param error The caught value.
   * @returns A safe, human-readable message (never a stack trace).
   */
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error && error.message) {
    return 'Something went wrong while contacting the server.';
  }
  return 'An unexpected error occurred.';
}
