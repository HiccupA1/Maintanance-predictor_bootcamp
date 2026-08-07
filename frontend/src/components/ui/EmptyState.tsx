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
    <div className="card relative overflow-hidden p-8 text-center">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-70 [background:radial-gradient(circle_at_50%_0%,rgba(124,58,237,.22),transparent_55%)]"
      />
      <div
        aria-hidden="true"
        className="relative mx-auto mb-4 grid h-12 w-12 place-items-center rounded-2xl border border-white/10 bg-white/5 text-sm font-extrabold text-white/80 shadow-[0_20px_60px_rgba(0,0,0,.35)]"
      >
        ✦
      </div>
      <h2 className="relative text-base font-semibold text-white">{title}</h2>
      {description && (
        <p className="relative mt-1 text-sm text-white/70">{description}</p>
      )}
      {action && <div className="relative mt-5 flex justify-center">{action}</div>}
    </div>
  );
}
