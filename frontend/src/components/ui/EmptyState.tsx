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
      <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
      {description && <p className="mt-1 text-sm text-slate-600">{description}</p>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}
