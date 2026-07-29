import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError, type Problem } from '../../api/client';
import { useAlert } from '../../hooks/useAlerts';
import { useCurrentUser } from '../../hooks/useCurrentUser';
import { useConvertAlertToWorkOrder } from '../../hooks/useWorkOrders';
import { ConvertAlertPage } from './ConvertAlertPage';

vi.mock('../../hooks/useAlerts', () => ({
  useAlert: vi.fn(),
}));

vi.mock('../../hooks/useCurrentUser', () => ({
  useCurrentUser: vi.fn(),
}));

vi.mock('../../hooks/useWorkOrders', () => ({
  useConvertAlertToWorkOrder: vi.fn(),
}));

const alertMock = vi.mocked(useAlert);
const userMock = vi.mocked(useCurrentUser);
const convertMock = vi.mocked(useConvertAlertToWorkOrder);

const alertFixture = {
  id: 'alert-1',
  equipment_id: 'equipment-1',
  parameter_id: 'parameter-1',
  parameter_name: 'Bearing speed',
  status: 'ACKNOWLEDGED',
  priority: 'HIGH',
  current_value: '101.5',
  breach_timestamp: '2026-07-01T10:00:00Z',
  min_threshold: null,
  max_threshold: 90,
  suggested_action: null,
  why_priority: null,
  issuer_name: 'sensor-service',
  machine_details: null,
  readings_snapshot: null,
  created_at: '2026-07-01T10:00:00Z',
  updated_at: '2026-07-01T10:01:00Z',
};

function renderConvert() {
  return render(
    <MemoryRouter initialEntries={['/alerts/alert-1/convert']}>
      <Routes>
        <Route path="/alerts/:alertId/convert" element={<ConvertAlertPage />} />
        <Route path="/work-orders/wo-1" element={<div>Work order detail</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ConvertAlertPage', () => {
  beforeEach(() => {
    alertMock.mockReturnValue({
      data: alertFixture,
      loading: false,
      error: null,
      reload: vi.fn(),
    });
    userMock.mockReturnValue({
      user: { user_id: 'pm-1', name: 'Plant Manager', role: 'PlantManager' },
      isLoading: false,
      error: null,
    });
  });

  it('navigates to the created work-order detail after successful conversion', async () => {
    const submitMock = vi.fn().mockResolvedValue({
      id: 'wo-1',
      alert_id: 'alert-1',
      equipment_id: 'equipment-1',
      description: 'Inspect bearing',
      priority: 'HIGH',
      status: 'OPEN',
      created_at: '2026-07-01T10:00:00Z',
      updated_at: '2026-07-01T10:00:00Z',
      parts: [],
    });

    convertMock.mockReturnValue({
      submit: submitMock,
      submitting: false,
      error: null,
      reset: vi.fn(),
    });

    const user = userEvent.setup();
    renderConvert();

    await user.type(screen.getByLabelText('Description'), 'Inspect bearing');
    await user.click(screen.getByRole('button', { name: 'Create work order' }));

    expect(submitMock).toHaveBeenCalledWith(
      'alert-1',
      expect.objectContaining({
        description: 'Inspect bearing',
        priority: 'HIGH',
        parts: [],
      }),
    );
    expect(await screen.findByText('Work order detail')).toBeInTheDocument();
  });

  it('shows the exact duplicate message and links to an existing work order', () => {
    const problem = {
      status: 409,
      code: 'duplicate_work_order',
      work_order_id: 'wo-existing',
    } as Problem & { work_order_id: string };

    convertMock.mockReturnValue({
      submit: vi.fn().mockResolvedValue(null),
      submitting: false,
      error: new ApiError('Duplicate', 409, 'duplicate_work_order', problem),
      reset: vi.fn(),
    });

    renderConvert();

    expect(
      screen.getByText('Work order already exists for this alert'),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'View existing work order' }),
    ).toHaveAttribute('href', '/work-orders/wo-existing');
    expect(
      screen.getByRole('button', { name: 'Create work order' }),
    ).toBeDisabled();
  });
});
