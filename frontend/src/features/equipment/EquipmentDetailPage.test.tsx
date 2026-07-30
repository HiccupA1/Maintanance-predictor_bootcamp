import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { EquipmentDetailPage } from './EquipmentDetailPage';

const useEquipment = vi.hoisted(() => vi.fn());
const useCurrentUser = vi.hoisted(() => vi.fn());
const listParameters = vi.hoisted(() => vi.fn());

vi.mock('../../hooks/useEquipment', () => ({
  isAdminRole: () => false,
  useEquipment,
}));

vi.mock('../../hooks/useCurrentUser', () => ({
  useCurrentUser,
}));

vi.mock('../../api/parameters', async () => {
  const actual = await vi.importActual<typeof import('../../api/parameters')>(
    '../../api/parameters',
  );
  return {
    ...actual,
    listParameters,
  };
});

describe('EquipmentDetailPage parameters', () => {
  beforeEach(() => {
    useEquipment.mockReturnValue({
      loading: false,
      error: null,
      reload: vi.fn(),
      data: {
        id: 'db-1',
        equipment_id: 'EQ-001',
        name: 'Compressor',
        location: 'Plant A',
        type: 'Rotary',
        criticality: 4,
        updated_at: '2026-07-01T10:00:00Z',
      },
    });
    useCurrentUser.mockReturnValue({
      user: { user_id: 'u-1', name: 'Operator', role: 'Operator' },
      isLoading: false,
      error: null,
    });
    listParameters.mockResolvedValue([]);
  });

  it('renders the parameter empty state', async () => {
    render(
      <MemoryRouter>
        <EquipmentDetailPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('parameters-empty')).toBeInTheDocument();
    });

    expect(screen.queryByRole('button', { name: 'Add parameter' })).not.toBeInTheDocument();
  });
});
