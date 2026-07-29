import type { ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';

import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { SkeletonRows } from '../../components/ui/Spinner';
import { ApiError } from '../../api/client';
import { isAdminRole, useEquipment } from '../../hooks/useEquipment';
import { formatDateTime } from '../../utils/format';

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm text-slate-800">{children}</dd>
    </div>
  );
}

// PUBLIC_INTERFACE
export function EquipmentDetailPage() {
  /** Render read-only Equipment metadata and the MVP parameters summary. */
  const { id } = useParams<{ id: string }>();
  const { data, loading, error, reload } = useEquipment(id);

  if (loading) {
    return (
      <div className="card" data-testid="equipment-detail-loading">
        <span className="sr-only" role="status">Loading equipment</span>
        <SkeletonRows rows={5} columns={2} />
      </div>
    );
  }

  if (error) {
    const notFound = error instanceof ApiError && error.isNotFound;
    return notFound ? (
      <EmptyState
        title="Equipment not found"
        description="This equipment record does not exist or may have been removed."
        action={<Link to="/equipment"><Button>Back to equipment</Button></Link>}
      />
    ) : (
      <ErrorPanel title="Unable to load equipment" error={error} onRetry={reload} />
    );
  }

  if (!data) {
    return <EmptyState title="No equipment data" description="The server returned no equipment data." />;
  }

  return (
    <section aria-labelledby="equipment-detail-heading" className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 id="equipment-detail-heading" className="text-xl font-semibold text-slate-900">
            {data.name}
          </h1>
          <p className="mt-1 font-mono text-xs text-slate-500">{data.equipment_id}</p>
        </div>
        {isAdminRole() && (
          <Link to={`/equipment/${encodeURIComponent(data.equipment_id)}/edit`}>
            <Button>Edit equipment</Button>
          </Link>
        )}
      </div>

      <div className="card p-4">
        <h2 className="text-sm font-semibold text-slate-800">Equipment metadata</h2>
        <dl className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Equipment ID"><span className="font-mono">{data.equipment_id}</span></Field>
          <Field label="Name">{data.name}</Field>
          <Field label="Location">{data.location}</Field>
          <Field label="Type">{data.type}</Field>
          <Field label="Criticality">{data.criticality} / 5</Field>
          <Field label="Health"><Badge>{data.health_status === 'AT_RISK' ? 'At Risk' : data.health_status || 'Unknown'}</Badge></Field>
          <Field label="Last service">{formatDateTime(data.last_service_date)}</Field>
          <Field label="Updated">{formatDateTime(data.updated_at)}</Field>
        </dl>
      </div>

      <div className="card p-4">
        <h2 className="text-sm font-semibold text-slate-800">Parameters summary</h2>
        {data.parameters && Object.keys(data.parameters).length > 0 ? (
          <dl className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
            {Object.entries(data.parameters).map(([key, value]) => (
              <Field key={key} label={key}>{String(value)}</Field>
            ))}
          </dl>
        ) : (
          <p className="mt-2 text-sm text-slate-600">
            No parameter readings are available yet. Parameter management is planned for a later module.
          </p>
        )}
      </div>

      <Link to="/equipment" className="text-sm text-brand-700 hover:underline">← Back to equipment</Link>
    </section>
  );
}
