import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../api/client';
import { getWorkOrder, updateWorkOrder } from '../../api/workOrders';
import { useCurrentUser } from '../../hooks/useCurrentUser';
import { makeWorkOrder, renderRoute } from '../../test/utils';
import { WorkOrderDetailPage } from './WorkOrderDetailPage';

vi.mock('../../api/workOrders', async () => {
  const actual = await vi.importActual<typeof import('../../api/workOrders')>(
    '../../api/workOrders',
  );
  return { ...actual, getWorkOrder: vi.fn(), updateWorkOrder: vi.fn() };
});

vi.mock('../../hooks/useCurrentUser', () => ({
  useCurrentUser: vi.fn(),
}));

const getMock = vi.mocked(getWorkOrder);
const updateMock = vi.mocked(updateWorkOrder);
const currentUserMock = vi.mocked(useCurrentUser);

function renderDetail(id = 'wo-1') {
  return renderRoute(<WorkOrderDetailPage />, {
    path: '/work-orders/:id',
    route: `/work-orders/${id}`,
  });
}

describe('WorkOrderDetailPage', () => {
  beforeEach(() => {
    getMock.mockReset();
    updateMock.mockReset();
    currentUserMock.mockReturnValue({
      user: {
        user_id: 'user-1',
        name: 'Engineer',
        role: 'MaintenanceEngineer',
      },
      isLoading: false,
      error: null,
    });
  });

  it('shows a not-found empty state when the backend returns work_order_not_found', async () => {
    getMock.mockRejectedValue(
      new ApiError('Work order not found.', 404, 'work_order_not_found'),
    );

    renderDetail('missing');

    expect(await screen.findByText('Work order not found')).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'Back to work orders' }),
    ).toBeInTheDocument();
  });

  it('renders work order details and spare parts on success', async () => {
    getMock.mockResolvedValue(
      makeWorkOrder({
        description: 'Replace worn bearing',
        work_order_number: 3,
        equipment_name: 'Cooling Pump',
      }),
    );

    renderDetail();

    expect(
      await screen.findByText('Replace worn bearing'),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Work order 3' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Cooling Pump')).toBeInTheDocument();
    expect(screen.getByText('OPEN')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });

  it('hides closure controls (legacy) from the page', async () => {
    getMock.mockResolvedValue(makeWorkOrder());
    renderDetail();

    await waitFor(() => {
      expect(getMock).toHaveBeenCalledTimes(1);
    });

    // Live Supabase schema reconciliation removed closure metadata + spare parts
    // from work_orders, so the UI should not render legacy closure controls.
    expect(
      screen.queryByRole('heading', { name: 'Close work order' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Close work order' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId('spare-parts-checklist'),
    ).not.toBeInTheDocument();
  });

  it('hides closure controls from non-Maintenance Engineers', async () => {
    currentUserMock.mockReturnValue({
      user: { user_id: 'user-2', name: 'Operator', role: 'Operator' },
      isLoading: false,
      error: null,
    });
    getMock.mockResolvedValue(makeWorkOrder());

    renderDetail();

    expect(
      await screen.findByText('Replace worn bearing'),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Close work order' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId('spare-parts-checklist'),
    ).not.toBeInTheDocument();
  });

  it('does not render legacy closure flow (schema no longer supports it)', async () => {
    getMock.mockResolvedValue(makeWorkOrder());

    renderDetail();

    await waitFor(() => {
      expect(getMock).toHaveBeenCalledTimes(1);
    });

    expect(
      screen.queryByRole('heading', { name: 'Close work order' }),
    ).not.toBeInTheDocument();
    expect(updateMock).not.toHaveBeenCalled();
  });
});
