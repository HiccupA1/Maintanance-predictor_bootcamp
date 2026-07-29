import { Link } from 'react-router-dom';

import { Badge } from '../../components/ui/Badge';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { SkeletonRows } from '../../components/ui/Spinner';
import { formatDateTime } from '../../utils/format';
import { useAlertList } from '../../hooks/useAlerts';

// PUBLIC_INTERFACE
export function AlertsListPage() {
  /**
   * Render the alert triage list.
   *
   * Displays status, priority, equipment, parameter, breach timestamp, and
   * current value while handling loading, error, empty, and success states.
   */
  const { data, loading, error, reload } = useAlertList();

  return (
    <section aria-labelledby="alerts-heading" className="space-y-4">
      <div>
        <h1 id="alerts-heading" className="text-xl font-semibold text-slate-900">
          Alerts
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Review threshold breaches and open an alert for full triage details.
        </p>
      </div>

      {loading && (
        <div className="card" data-testid="alerts-loading">
          <span className="sr-only" role="status">
            Loading alerts
          </span>
          <SkeletonRows rows={5} columns={6} />
        </div>
      )}

      {!loading && error && (
        <ErrorPanel
          title="Unable to load alerts"
          error={error}
          onRetry={reload}
        />
      )}

      {!loading && !error && data && data.length === 0 && (
        <EmptyState
          title="No alerts found"
          description="There are no threshold breach alerts to review."
        />
      )}

      {!loading && !error && data && data.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <caption className="sr-only">Alerts, newest first</caption>
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th scope="col" className="px-4 py-3">Alert</th>
                <th scope="col" className="px-4 py-3">Status</th>
                <th scope="col" className="px-4 py-3">Priority</th>
                <th scope="col" className="px-4 py-3">Equipment</th>
                <th scope="col" className="px-4 py-3">Parameter</th>
                <th scope="col" className="px-4 py-3">Breach timestamp</th>
                <th scope="col" className="px-4 py-3">Current value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((alert) => (
                <tr key={alert.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/alerts/${alert.id}`}
                      className="font-mono text-brand-700 underline-offset-2 hover:underline"
                    >
                      {String(alert.id)}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <Badge>{String(alert.status)}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge>{String(alert.priority)}</Badge>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-600">
                    {String(alert.equipment_id)}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {String(alert.parameter_name || alert.parameter_id || '—')}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {formatDateTime(alert.breach_timestamp)}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {String(alert.current_value || '—')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
