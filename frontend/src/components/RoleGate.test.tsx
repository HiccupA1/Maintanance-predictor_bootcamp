import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { RoleGate } from './RoleGate';

const useCurrentUserMock = vi.hoisted(() => vi.fn());

vi.mock('../hooks/useCurrentUser', () => ({
  useCurrentUser: useCurrentUserMock,
}));

describe('RoleGate', () => {
  it('renders children for an allowed role', () => {
    useCurrentUserMock.mockReturnValue({
      user: { user_id: 'u-1', name: 'Admin User', role: 'Admin' },
      isLoading: false,
      error: null,
    });

    render(
      <RoleGate allowedRoles={['Admin']}>
        <span>Protected action</span>
      </RoleGate>,
    );

    expect(screen.getByText('Protected action')).toBeInTheDocument();
  });

  it('renders the fallback when the role is not allowed', () => {
    useCurrentUserMock.mockReturnValue({
      user: { user_id: 'u-2', name: 'Operator User', role: 'Operator' },
      isLoading: false,
      error: null,
    });

    render(
      <RoleGate allowedRoles={['Admin']} fallback={<span>Not allowed</span>}>
        <span>Protected action</span>
      </RoleGate>,
    );

    expect(screen.queryByText('Protected action')).not.toBeInTheDocument();
    expect(screen.getByText('Not allowed')).toBeInTheDocument();
  });
});
