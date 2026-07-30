import { Link, useSearchParams } from 'react-router-dom';

import { DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE } from '../../config/env';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { PriorityBadge, StatusBadge } from '../../components/ui/Badge';
import { SkeletonRows } from '../../components/ui/Spinner';
import { Button } from '../../components/ui/Button';
import { clampPageSize } from '../../api/workOrders';
import { formatDateTime } from '../../utils/format';
import { useWorkOrderList } from '../../hooks/useWorkOrders';
import {
  PRIORITIES,
  WORK_ORDER_STATUSES,
  type Priority,
  type WorkOrderStatus,
} from '../../types/workOrders';

// PUBLIC_INTERFACE
export function WorkOrdersListPage() {
  /**
   * Work Orders list screen.
   *
   * Reads pagination and filters from the URL query string so views are
   * shareable, clamps `page_size` to the backend maximum (200), and renders
   * explicit loading, error, empty and success states.
   */
  const [searchParams, setSearchParams] = useSearchParams();

  const page = Math.max(Number(searchParams.get('page') ?? '1') || 1, 1);
  const pageSize = clampPageSize(
    Number(searchParams.get('page_size') ?? String(DEFAULT_PAGE_SIZE)),
  );
  const status = (searchParams.get('status') ?? '') as WorkOrderStatus | '';
  const priority = (searchParams.get('priority') ?? '') as Priority | '';

  const { data, loading, error, reload } = useWorkOrderList({
    page,
    page_size: pageSize,
    status,
    priority,
  });

  /** Merge query params, resetting to page 1 whenever filters change. */
  const updateParams = (next: Record<string, string>, resetPage = true) => {
    const params = new URLSearchParams(searchParams);
    for (const [key, value] of Object.entries(next)) {
      if (value) params.set(key, value);
      else params.delete(key);
    }
    if (resetPage) params.set('page', '1');
    setSearchParams(params);
  };

  const total = data?.total ?? 0;
  const totalPages = total > 0 ? Math.ceil(total / pageSize) : 1;

  return (
    <section aria-labelledby="work-orders-heading" className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 id="work-orders-heading" className="text-xl font-semibold text-slate-900">
          Work Orders
        </h1>
        {data && !loading && !error && (
          <p className="text-sm text-slate-600">
            {total} total · page {data.page} of {totalPages}
          </p>
        )}
      </div>

      <form
        className="card flex flex-wrap items-end gap-4 p-4"
        onSubmit={(event) => event.preventDefault()}
      >
        <div className="w-40">
          <label className="label" htmlFor="filter-status">
            Status
          </label>
          <select
            id="filter-status"
            className="input"
            value={status}
            onChange={(event) => updateParams({ status: event.target.value })}
          >
            <option value="">All</option>
            {WORK_ORDER_STATUSES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>

        <div className="w-40">
          <label className="label" htmlFor="filter-priority">
            Priority
          </label>
          <select
            id="filter-priority"
            className="input"
            value={priority}
            onChange={(event) => updateParams({ priority: event.target.value })}
          >
            <option value="">All</option>
            {PRIORITIES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>

        <div className="w-40">
          <label className="label" htmlFor="filter-page-size">
            Page size
          </label>
          <input
            id="filter-page-size"
            className="input"
            type="number"
            min={1}
            max={MAX_PAGE_SIZE}
            value={pageSize}
            onChange={(event) =>
              updateParams({
                page_size: String(clampPageSize(Number(event.target.value))),
              })
            }
            aria-describedby="page-size-hint"
          />
          <p id="page-size-hint" className="mt-1 text-xs text-slate-500">
            Maximum {MAX_PAGE_SIZE}.
          </p>
        </div>
      </form>

      {loading && (
        <div className="card" data-testid="work-orders-loading">
          <span className="sr-only" role="status">
            Loading work orders
          </span>
          <SkeletonRows rows={5} columns={6} />
        </div>
      )}

      {!loading && Boolean(error) && (
        <ErrorPanel title="Unable to load work orders" error={error} onRetry={reload} />
      )}

      {!loading && !error && data && data.items.length === 0 && (
        <EmptyState
          title="No work orders found"
          description="No work orders match the current filters. Convert an alert to create the first work order."
        />
      )}

      {!loading && !error && data && data.items.length > 0 && (
        <>
          <div className="card overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <caption className="sr-only">Work orders, newest first</caption>
              <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
                <tr>
                  <th scope="col" className="px-4 py-3">Work order</th>
                  <th scope="col" className="px-4 py-3">Equipment</th>
                  <th scope="col" className="px-4 py-3">Priority</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3">Due</th>
                  <th scope="col" className="px-4 py-3">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <Link
                        to={`/work-orders/${item.id}`}
                        className="font-mono text-brand-700 underline-offset-2 hover:underline"
                      >
                        {String(item.id)}
                      </Link>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-600">
                      {item.equipment_id}
                    </td>
                    <td className="px-4 py-3">
                      <PriorityBadge priority={item.priority} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {formatDateTime(item.due_at)}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {formatDateTime(item.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <nav
            aria-label="Pagination"
            className="flex flex-wrap items-center justify-between gap-3"
          >
            <p className="text-sm text-slate-600">
              Showing {(data.page - 1) * data.page_size + 1}–
              {Math.min(data.page * data.page_size, data.total)} of {data.total}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                disabled={data.page <= 1}
                onClick={() =>
                  updateParams({ page: String(Math.max(data.page - 1, 1)) }, false)
                }
              >
                Previous
              </Button>
              <span className="text-sm text-slate-600">
                Page {data.page} of {totalPages}
              </span>
              <Button
                variant="secondary"
                disabled={data.page >= totalPages}
                onClick={() => updateParams({ page: String(data.page + 1) }, false)}
              >
                Next
              </Button>
            </div>
          </nav>
        </>
      )}
    </section>
  );
}
