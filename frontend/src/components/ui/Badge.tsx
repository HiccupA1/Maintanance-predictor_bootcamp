import type { Priority, WorkOrderStatus } from '../../types/workOrders';

const PRIORITY_STYLES: Record<Priority, string> = {
  CRITICAL: 'bg-red-100 text-red-800 border-red-200',
  HIGH: 'bg-amber-100 text-amber-800 border-amber-200',
  MEDIUM: 'bg-sky-100 text-sky-800 border-sky-200',
};

const STATUS_STYLES: Record<WorkOrderStatus, string> = {
  OPEN: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  CLOSED: 'bg-slate-100 text-slate-700 border-slate-200',
};

// PUBLIC_INTERFACE
export function PriorityBadge({ priority }: { priority: Priority }) {
  /**
   * Display a work order priority as a colour-coded badge.
   *
   * @param priority Backend priority value (CRITICAL, HIGH, MEDIUM).
   */
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${PRIORITY_STYLES[priority]}`}
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
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}
