import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../api/client';
import { renderRoute } from '../../test/utils';
import { AlertsListPage } from './AlertsListPage';

vi.mock('../../api/alerts', async () => {
  const actual = await vi.importActual<typeof import('../../api/alerts')>(
    '../../api/alerts',
  );
  return { ...actual, listAlerts: vi.fn() };
});

const { listAlerts } = await import('../../api/alerts');
const listMock = vi.mocked(listAlerts);

function renderList() {
  return renderRoute(<AlertsListPage />, {
    path: '/alerts',
    route: '/alerts',
  });
}

const alertFixture = {
  id: 'alert-1',
  equipment_id: 'equipment-1',
  equipment_name: 'Cooling Pump A',
  parameter_id: 'parameter-1',
  parameter_name: 'Coolant temperature',
  status: 'NEW',
  priority: 'HIGH',
  current_value: '98.2',
  breach_timestamp: '2026-07-01T10:00:00Z',
  min_threshold: null,
  max_threshold: 90,
  suggested_action: 'Inspect cooling system',
  why_priority: 'Above maximum threshold',
  issuer_name: 'sensor-service',
  machine_details: null,
  readings_snapshot: null,
  created_at: '2026-07-01T10:00:00Z',
  updated_at: '2026-07-01T10:00:00Z',
};

describe('AlertsListPage', () => {
  beforeEach(() => {
    listMock.mockReset();
  });

  it('shows loading state while alerts are loading', () => {
    listMock.mockReturnValue(new Promise(() => {}));
    renderList();

    expect(screen.getByTestId('alerts-loading')).toBeInTheDocument();
  });

  it('shows an empty state when the API returns no alerts', async () => {
    listMock.mockResolvedValue([]);
    renderList();

    expect(await screen.findByText('No alerts found')).toBeInTheDocument();
  });

  it('shows API errors with a retry action', async () => {
    listMock.mockRejectedValue(
      new ApiError('Alerts unavailable.', 503, 'service_unavailable'),
    );
    renderList();

    expect(await screen.findByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Alerts unavailable.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
  });

  it('renders alert triage fields and links to detail', async () => {
    listMock.mockResolvedValue([alertFixture]);
    renderList();

    expect(await screen.findByRole('link', { name: 'alert-1' })).toHaveAttribute(
      'href',
      '/alerts/alert-1',
    );
    expect(screen.getByText('NEW')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('Cooling Pump A')).toBeInTheDocument();
    expect(screen.getByText('Coolant temperature')).toBeInTheDocument();
    expect(screen.queryByText('equipment-1')).not.toBeInTheDocument();
    expect(screen.queryByText('parameter-1')).not.toBeInTheDocument();
    expect(screen.getByText('98.2')).toBeInTheDocument();
  });
});
