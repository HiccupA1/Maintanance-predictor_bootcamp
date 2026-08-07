import type { ReactNode } from 'react';

// PUBLIC_INTERFACE
export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  /**
   * Render an empty/no-results state.
   *
   * @param title Short headline, e.g. "No work orders yet".
   * @param description Optional guidance explaining what to do next.
   * @param action Optional call-to-action node.
   */
  return (
    <div className="card p-8 text-center">
      <div
        aria-hidden="true"
        className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-sm font-bold text-slate-500"
      >
        —
      </div>
      <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      {description && <p className="mt-1 text-sm text-slate-600">{description}</p>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}
