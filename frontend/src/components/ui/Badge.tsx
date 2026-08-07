import type { ReactNode } from 'react';
import type { Priority, WorkOrderStatus } from '../../types/workOrders';

const PRIORITY_STYLES: Record<Priority, string> = {
  CRITICAL:
    'border-rose-300/25 bg-rose-400/15 text-rose-50/90 ring-1 ring-rose-200/20',
  HIGH:
    'border-amber-300/25 bg-amber-400/15 text-amber-50/90 ring-1 ring-amber-200/20',
  MEDIUM:
    'border-sky-300/25 bg-sky-400/15 text-sky-50/90 ring-1 ring-sky-200/20',
};

const STATUS_STYLES: Record<WorkOrderStatus, string> = {
  OPEN:
    'border-emerald-300/25 bg-emerald-400/15 text-emerald-50/90 ring-1 ring-emerald-200/20',
  CLOSED:
    'border-white/15 bg-white/6 text-white/70 ring-1 ring-white/10',
};

// PUBLIC_INTERFACE
export function Badge({ children }: { children: ReactNode }) {
  /** Render a neutral inline badge for generic status or health labels. */
  return (
    <span className="inline-flex items-center rounded-full border border-white/15 bg-white/5 px-2.5 py-1 text-xs font-semibold text-white/75 ring-1 ring-white/10">
      {children}
    </span>
  );
}

// PUBLIC_INTERFACE
export function PriorityBadge({ priority }: { priority: Priority }) {
  /**
   * Display a work order priority as a colour-coded badge.
   *
   * @param priority Backend priority value (CRITICAL, HIGH, MEDIUM).
   */
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold backdrop-blur ${PRIORITY_STYLES[priority]}`}
    >
      {priority}
    </span>
  );
}

// PUBLIC_INTERFACE
export function StatusBadge({ status }: { status: WorkOrderStatus }) {
  /**
   * Display a work order status as a colour-coded badge.
   *
   * @param status Backend status value (OPEN, CLOSED).
   */
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold backdrop-blur ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}
