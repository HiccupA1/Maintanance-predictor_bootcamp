/** Loading indicators: inline spinner and table/card skeletons. */

// PUBLIC_INTERFACE
export function Spinner({ label = 'Loading' }: { label?: string }) {
  /**
   * Accessible inline spinner.
   *
   * @param label Accessible label announced to assistive technology.
   */
  return (
    <span role="status" aria-live="polite" className="inline-flex items-center gap-2">
      <span
        aria-hidden="true"
        className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600"
      />
      <span className="text-sm text-slate-600">{label}…</span>
    </span>
  );
}

// PUBLIC_INTERFACE
export function SkeletonRows({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  /**
   * Placeholder skeleton used while list data is loading.
   *
   * @param rows Number of skeleton rows to render.
   * @param columns Number of skeleton cells per row.
   */
  return (
    <div aria-hidden="true" className="animate-pulse space-y-2 p-4">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-3">
          {Array.from({ length: columns }).map((__, colIndex) => (
            <div key={colIndex} className="h-4 flex-1 rounded bg-slate-200" />
          ))}
        </div>
      ))}
    </div>
  );
}
