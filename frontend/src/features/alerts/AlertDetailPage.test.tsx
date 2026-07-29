import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../api/client';
import { renderRoute } from '../../test/utils';
import { AlertDetailPage } from './AlertDetailPage';

vi.mock('../../api/alerts', async () => {
  const actual = await vi.importActual<typeof import('../../api/alerts')>(
    '../../api/alerts',
  );
  return { ...actual, getAlert: vi.fn() };
});

vi.mock('../../hooks/useCurrentUser', () => ({
  useCurrentUser: vi.fn(),
}));

const { getAlert } = await import('../../api/alerts');
const { useCurrentUser } = await import('../../hooks/useCurrentUser');
const getMock = vi.mocked(getAlert);
const userMock = vi.mocked(useCurrentUser);

const alertFixture = {
  id: 'alert-1',
  equipment_id: 'equipment-1',
  parameter_id: 'parameter-1',
  status: 'ACKNOWLEDGED',
  priority: 'CRITICAL',
  current_value: '101.5',
  breach_timestamp: '2026-07-01T10:00:00Z',
  min_threshold: null,
  max_threshold: 90,
  suggested_action: 'Stop equipment and inspect bearing.',
  why_priority: 'Critical overspeed breach',
  issuer_name: 'sensor-service',
  machine_details: { line: 'A', motor: 'M-1' },
  readings_snapshot: { value: '101.5', unit: 'rpm' },
  created_at: '2026-07-01T10:00:00Z',
  updated_at: '2026-07-01T10:01:00Z',
};

function renderDetail(id = 'alert-1') {
  return renderRoute(<AlertDetailPage />, {
    path: '/alerts/:alertId',
    route: `/alerts/${id}`,
  });
}

describe('AlertDetailPage', () => {
  beforeEach(() => {
    getMock.mockReset();
    userMock.mockReturnValue({
      user: { user_id: 'pm-1', name: 'Plant Manager', role: 'PlantManager' },
      isLoading: false,
      error: null,
    });
  });

  it('shows a not-found empty state', async () => {
    getMock.mockRejectedValue(
      new ApiError('Alert not found.', 404, 'alert_not_found'),
    );
    renderDetail('missing');

    expect(await screen.findByText('Alert not found')).toBeInTheDocument();
  });

  it('renders full alert details and PlantManager conversion link', async () => {
    getMock.mockResolvedValue(alertFixture);
    renderDetail();

    expect(await screen.findByText('Stop equipment and inspect bearing.')).toBeInTheDocument();
    expect(screen.getByText('Critical overspeed breach')).toBeInTheDocument();
    expect(screen.getByText('101.5')).toBeInTheDocument();
    expect(screen.getByText(/"line": "A"/)).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'Convert to Work Order' }),
    ).toHaveAttribute('href', '/alerts/alert-1/convert');
  });

  it('does not render conversion for non-PlantManager users', async () => {
    userMock.mockReturnValue({
      user: { user_id: 'op-1', name: 'Operator', role: 'Operator' },
      isLoading: false,
      error: null,
    });
    getMock.mockResolvedValue(alertFixture);
    renderDetail();

    expect(await screen.findByText('Alert detail')).toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Convert to Work Order' }),
    ).not.toBeInTheDocument();
  });
});
