import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
        parts: [
          {
            id: 'p-1',
            part_name: 'Bearing 6204',
            used: true,
            notes: 'Front side',
          },
        ],
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
    expect(screen.getByDisplayValue('Bearing 6204')).toBeInTheDocument();
    expect(screen.getByText('Used')).toBeInTheDocument();
  });

  it('blocks closure when required fields and parts are missing', async () => {
    getMock.mockResolvedValue(makeWorkOrder());
    const user = userEvent.setup();

    renderDetail();

    expect(
      await screen.findByRole('heading', { name: 'Close work order' }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Close work order' }));

    expect(
      screen.getByText('Resolution notes are required before closing.'),
    ).toBeInTheDocument();
    expect(updateMock).not.toHaveBeenCalled();

    await user.type(
      screen.getByLabelText('Resolution notes'),
      'Bearing replaced',
    );
    await user.type(screen.getByLabelText('Root cause'), 'Bearing wear');
    await user.click(screen.getByRole('button', { name: 'Close work order' }));

    expect(
      screen.getByText(/At least one spare-part line is required/),
    ).toBeInTheDocument();
    expect(updateMock).not.toHaveBeenCalled();
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

  it('submits closure and refetches the closed work order', async () => {
    const openOrder = makeWorkOrder();
    const closedOrder = makeWorkOrder({
      status: 'CLOSED',
      resolution_notes: 'Bearing replaced',
      root_cause: 'Bearing wear',
      closed_at: '2026-07-29T12:00:00Z',
      parts: [
        {
          id: 'p-1',
          part_name: 'N/A',
          used: false,
          notes: null,
        },
      ],
    });

    getMock
      .mockResolvedValueOnce(openOrder)
      .mockResolvedValueOnce(closedOrder);
    updateMock.mockResolvedValue(closedOrder);

    const user = userEvent.setup();
    renderDetail();

    expect(
      await screen.findByRole('heading', { name: 'Close work order' }),
    ).toBeInTheDocument();
    await user.type(
      screen.getByLabelText('Resolution notes'),
      'Bearing replaced',
    );
    await user.type(screen.getByLabelText('Root cause'), 'Bearing wear');
    await user.click(screen.getByRole('button', { name: 'Add part line' }));
    await user.type(screen.getByLabelText('Part name 1'), 'N/A');
    await user.click(screen.getByRole('button', { name: 'Close work order' }));

    await waitFor(() => {
      expect(updateMock).toHaveBeenCalledWith('wo-1', {
        status: 'CLOSED',
        resolution_notes: 'Bearing replaced',
        root_cause: 'Bearing wear',
        parts: [{ part_name: 'N/A', used: true, notes: null }],
      });
    });

    expect(await screen.findByTestId('closure-summary')).toBeInTheDocument();
    expect(getMock).toHaveBeenCalledTimes(2);
    expect(
      screen.getByText('Work order closed successfully.'),
    ).toBeInTheDocument();
  });
});
