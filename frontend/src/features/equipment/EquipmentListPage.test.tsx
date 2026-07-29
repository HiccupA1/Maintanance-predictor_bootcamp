import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { EquipmentListPage } from './EquipmentListPage';

const useEquipmentList = vi.hoisted(() => vi.fn());

vi.mock('../../hooks/useEquipment', () => ({
  isAdminRole: () => false,
  useEquipmentList,
}));

describe('EquipmentListPage', () => {
  beforeEach(() => {
    useEquipmentList.mockReturnValue({
      loading: true,
      data: null,
      error: null,
      reload: vi.fn(),
    });
  });

  it('renders loading and then equipment rows', async () => {
    const state = {
      loading: false,
      error: null,
      reload: vi.fn(),
      data: {
        items: [{
          id: 'db-1',
          equipment_id: 'EQ-001',
          name: 'Compressor',
          location: 'Plant A',
          type: 'Rotary',
          criticality: 4,
          health_status: 'AT_RISK',
          last_service_date: '2026-07-01T10:00:00Z',
        }],
      },
    };

    const view = render(
      <MemoryRouter>
        <EquipmentListPage />
      </MemoryRouter>,
    );

    expect(screen.getByTestId('equipment-loading')).toBeInTheDocument();
    useEquipmentList.mockReturnValue(state);
    view.rerender(
      <MemoryRouter>
        <EquipmentListPage />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText('EQ-001')).toBeInTheDocument());
    expect(screen.getByText('Compressor')).toBeInTheDocument();
    expect(screen.getByText('At Risk')).toBeInTheDocument();
  });
});
