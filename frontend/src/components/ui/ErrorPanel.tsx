import { ApiError } from '../../api/client';

// PUBLIC_INTERFACE
export function ErrorPanel({
  title = 'Something went wrong',
  error,
  onRetry,
}: {
  title?: string;
  error: unknown;
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
   * @param error The caught error (ideally an `ApiError`).
   * @param onRetry Optional retry handler.
   */
  const apiError = error instanceof ApiError ? error : undefined;
  const message =
    apiError?.message ??
    (error instanceof Error && error.message
      ? error.message
      : 'An unexpected error occurred while contacting the server.');

  return (
    <div role="alert" className="card border-red-200 bg-red-50 p-4">
      <h2 className="text-sm font-semibold text-red-800">{title}</h2>
      <p className="mt-1 text-sm text-red-700">{message}</p>
      {apiError?.code && (
        <p className="mt-1 text-xs text-red-600">
          Code: <span className="font-mono">{apiError.code}</span>
          {apiError.status ? ` (HTTP ${apiError.status})` : ''}
        </p>
      )}
      {apiError?.problem?.errors && apiError.problem.errors.length > 0 && (
        <ul className="mt-2 list-inside list-disc text-xs text-red-700">
          {apiError.problem.errors.map((item, index) => (
            <li key={`${item.field ?? 'error'}-${index}`}>
              {item.field && (
                <span className="font-medium">{item.field}: </span>
              )}
              {item.message}
            </li>
          ))}
        </ul>
      )}
      {apiError?.problem?.correlation_id && (
        <p className="mt-2 text-xs text-red-500">
          Correlation id:{' '}
          <span className="font-mono">
            {apiError.problem.correlation_id}
          </span>
        </p>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100"
        >
          Try again
        </button>
      )}
    </div>
  );
}
