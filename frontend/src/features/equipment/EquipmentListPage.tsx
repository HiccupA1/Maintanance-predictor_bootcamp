import { Link } from 'react-router-dom';

import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { SkeletonRows } from '../../components/ui/Spinner';
import { isAdminRole, useEquipmentList } from '../../hooks/useEquipment';
import { formatDateTime } from '../../utils/format';

function healthLabel(status?: string | null): string {
  if (!status) return 'Unknown';
  return status === 'AT_RISK' ? 'At Risk' : status.replaceAll('_', ' ');
}

// PUBLIC_INTERFACE
export function EquipmentListPage() {
  /** Render the Equipment table and its loading, error, empty, and success states. */
  const { data, loading, error, reload } = useEquipmentList();
  const admin = isAdminRole();

  return (
    <section aria-labelledby="equipment-heading" className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 id="equipment-heading" className="text-xl font-semibold text-slate-900">
            Equipment
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Monitor registered equipment and service history.
          </p>
        </div>
        {admin && (
          <Link to="/equipment/new">
            <Button>Add equipment</Button>
          </Link>
        )}
      </div>

      {loading && (
        <div className="card" data-testid="equipment-loading">
          <span className="sr-only" role="status">Loading equipment</span>
          <SkeletonRows rows={5} columns={7} />
        </div>
      )}

      {!loading && error && (
        <ErrorPanel title="Unable to load equipment" error={error} onRetry={reload} />
      )}

      {!loading && !error && data && data.items.length === 0 && (
        <EmptyState
          title="No equipment found"
          description="Equipment records will appear here once they are registered."
          action={admin ? <Link to="/equipment/new"><Button>Add equipment</Button></Link> : undefined}
        />
      )}

      {!loading && !error && data && data.items.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <caption className="sr-only">Registered equipment</caption>
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                {['Equipment ID', 'Name', 'Location', 'Type', 'Criticality', 'Health', 'Last service'].map((heading) => (
                  <th key={heading} scope="col" className="px-4 py-3">{heading}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((equipment) => (
                <tr key={equipment.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/equipment/${encodeURIComponent(equipment.equipment_id)}`}
                      className="font-mono text-brand-700 underline-offset-2 hover:underline"
                    >
                      {equipment.equipment_id}
                    </Link>
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-800">{equipment.name}</td>
                  <td className="px-4 py-3 text-slate-600">{equipment.location}</td>
                  <td className="px-4 py-3 text-slate-600">{equipment.type}</td>
                  <td className="px-4 py-3">{equipment.criticality}</td>
                  <td className="px-4 py-3">
                    <Badge>{healthLabel(equipment.health_status)}</Badge>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {formatDateTime(equipment.last_service_date)}
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
