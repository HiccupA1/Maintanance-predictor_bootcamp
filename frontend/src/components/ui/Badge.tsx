import type { ReactNode } from 'react';
import type { Priority, WorkOrderStatus } from '../../types/workOrders';

const PRIORITY_STYLES: Record<Priority, string> = {
  CRITICAL: 'bg-red-50 text-red-800 border-red-200',
  HIGH: 'bg-amber-50 text-amber-800 border-amber-200',
  MEDIUM: 'bg-blue-50 text-blue-800 border-blue-200',
};

const STATUS_STYLES: Record<WorkOrderStatus, string> = {
  OPEN: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  CLOSED: 'bg-slate-100 text-slate-700 border-slate-200',
};

// PUBLIC_INTERFACE
export function Badge({ children }: { children: ReactNode }) {
  /** Render a neutral inline badge for generic status or health labels. */
  return (
    <span className="inline-flex items-center rounded-md border border-slate-200 bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
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
      className={`inline-flex items-center rounded-md border px-2 py-1 text-xs font-semibold ${PRIORITY_STYLES[priority]}`}
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
      className={`inline-flex items-center rounded-md border px-2 py-1 text-xs font-semibold ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}
