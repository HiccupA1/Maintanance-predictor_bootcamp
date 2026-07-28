import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../api/client';
import { WorkOrderDetailPage } from './WorkOrderDetailPage';
import { makeWorkOrder, renderRoute } from '../../test/utils';

vi.mock('../../api/workOrders', async () => {
  const actual = await vi.importActual<typeof import('../../api/workOrders')>(
    '../../api/workOrders',
  );
  return { ...actual, getWorkOrder: vi.fn() };
});

const { getWorkOrder } = await import('../../api/workOrders');
const getMock = vi.mocked(getWorkOrder);

/** Render the detail page for a given work order id. */
function renderDetail(id = 'wo-1') {
  return renderRoute(<WorkOrderDetailPage />, {
    path: '/work-orders/:id',
    route: `/work-orders/${id}`,
  });
}

describe('WorkOrderDetailPage', () => {
  beforeEach(() => {
    getMock.mockReset();
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
        parts: [{ id: 'p-1', part_name: 'Bearing 6204', used: true, notes: 'Front side' }],
      }),
    );

    renderDetail();

    expect(await screen.findByText('Replace worn bearing')).toBeInTheDocument();
    expect(screen.getByText('OPEN')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('Bearing 6204')).toBeInTheDocument();
    expect(screen.getByText('Used')).toBeInTheDocument();
  });
});
