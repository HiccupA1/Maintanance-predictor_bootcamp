import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../api/client';
import { WorkOrdersListPage } from './WorkOrdersListPage';
import { makeSummary, renderRoute } from '../../test/utils';

// Mock the API module so no real network calls happen in tests.
vi.mock('../../api/workOrders', async () => {
  const actual = await vi.importActual<typeof import('../../api/workOrders')>(
    '../../api/workOrders',
  );
  return { ...actual, listWorkOrders: vi.fn() };
});

const { listWorkOrders } = await import('../../api/workOrders');
const listMock = vi.mocked(listWorkOrders);

/** Render the list page at its route. */
function renderList() {
  return renderRoute(<WorkOrdersListPage />, {
    path: '/work-orders',
    route: '/work-orders',
  });
}

describe('WorkOrdersListPage', () => {
  beforeEach(() => {
    listMock.mockReset();
  });

  it('shows a loading state while the request is in flight', () => {
    listMock.mockReturnValue(new Promise(() => {}));
    renderList();
    expect(screen.getByTestId('work-orders-loading')).toBeInTheDocument();
  });

  it('shows an empty state when no work orders are returned', async () => {
    listMock.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 });
    renderList();
    expect(await screen.findByText('No work orders found')).toBeInTheDocument();
  });

  it('shows non-field Problem JSON errors and the correlation id', async () => {
    listMock.mockRejectedValue(
      new ApiError(
        'created_from must not be after created_to.',
        422,
        'invalid_request',
        {
          status: 422,
          title: 'Invalid request',
          code: 'invalid_request',
          correlation_id: 'corr-123',
          errors: [
            {
              message: 'created_from must not be after created_to.',
            },
          ],
        },
      ),
    );
    renderList();

    expect(await screen.findByRole('alert')).toBeInTheDocument();
    expect(
      screen.getAllByText('created_from must not be after created_to.'),
    ).not.toHaveLength(0);
    expect(screen.getByText(/invalid_request/)).toBeInTheDocument();
    expect(screen.getByText(/corr-123/)).toBeInTheDocument();
  });

  it('renders rows and pagination totals on success', async () => {
    listMock.mockResolvedValue({
      items: [
        makeSummary({ id: 'wo-1', priority: 'CRITICAL' }),
        makeSummary({ id: 'wo-2', status: 'CLOSED' }),
      ],
      total: 2,
      page: 1,
      page_size: 20,
    });

    renderList();

    expect(await screen.findByRole('link', { name: 'wo-1' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'wo-2' })).toBeInTheDocument();
    expect(screen.getAllByText('CRITICAL')).not.toHaveLength(0);
    await waitFor(() =>
      expect(screen.getByText(/2 total · page 1 of 1/)).toBeInTheDocument(),
    );
  });
});
