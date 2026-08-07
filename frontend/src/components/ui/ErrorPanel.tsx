import type { ReactNode } from 'react';

import { ApiError } from '../../api/client';

// PUBLIC_INTERFACE
export function ErrorPanel({
  title = 'Something went wrong',
  error,
  hint,
  onRetry,
}: {
  title?: string;
  error: unknown;
  hint?: ReactNode;
  onRetry?: () => void;
}) {
  /**
   * Render a user-readable error state from a normalized API error.
   *
   * Shows the backend Problem JSON `detail`/`title`, the machine-readable
   * `code`, all error entries and the correlation id when available.
   * Never renders stack traces.
   *
   * @param title Heading for the error panel.
   * @param error The caught error (ideally an `ApiError`) or any user-displayable node.
   * @param onRetry Optional retry handler.
   */
  const apiError = error instanceof ApiError ? error : undefined;

  const message =
    apiError?.message ??
    (error instanceof Error && error.message
      ? error.message
      : typeof error === 'string'
        ? error
        : typeof error === 'number' || typeof error === 'boolean'
          ? String(error)
          : 'An unexpected error occurred while contacting the server.');

  return (
    <div
      role="alert"
      className="card relative overflow-hidden border border-rose-400/20 bg-[linear-gradient(180deg,rgba(251,113,133,.16)_0%,rgba(255,255,255,.04)_100%)] p-4"
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-70 [background:radial-gradient(circle_at_20%_0%,rgba(251,113,133,.25),transparent_55%)]"
      />
      <h2 className="relative text-sm font-semibold text-rose-100">{title}</h2>
      <p className="relative mt-1 text-sm text-rose-50/85">{message}</p>
      {hint && <p className="relative mt-2 text-xs text-rose-50/70">{hint}</p>}

      {apiError?.code && (
        <p className="relative mt-1 text-xs text-rose-100/70">
          Code: <span className="font-mono">{apiError.code}</span>
          {apiError.status ? ` (HTTP ${apiError.status})` : ''}
        </p>
      )}

      {apiError?.problem?.errors && apiError.problem.errors.length > 0 && (
        <ul className="relative mt-2 list-inside list-disc text-xs text-rose-50/80">
          {apiError.problem.errors.map((item, index) => (
            <li key={`${item.field ?? 'error'}-${index}`}>
              {item.field && <span className="font-medium">{item.field}: </span>}
              {item.message}
            </li>
          ))}
        </ul>
      )}

      {apiError?.problem?.correlation_id && (
        <p className="relative mt-2 text-xs text-rose-50/60">
          Correlation id: <span className="font-mono">{apiError.problem.correlation_id}</span>
        </p>
      )}

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="relative mt-3 rounded-md border border-rose-200/25 bg-white/5 px-3 py-1.5 text-sm font-medium text-rose-50/90 hover:bg-white/10"
        >
          Try again
        </button>
      )}
    </div>
  );
}
