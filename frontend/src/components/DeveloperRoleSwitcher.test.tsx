import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

import { DeveloperRoleSwitcher } from './DeveloperRoleSwitcher';

describe('DeveloperRoleSwitcher', () => {
  it('renders in Vite development mode', () => {
    vi.stubEnv('DEV', true);

    render(<DeveloperRoleSwitcher />);

    expect(
      screen.getByRole('region', { name: /development persona switcher/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/dev persona/i)).toBeInTheDocument();
  });

  it('is hidden in production mode', () => {
    vi.stubEnv('DEV', false);

    render(<DeveloperRoleSwitcher />);

    expect(
      screen.queryByRole('region', { name: /development persona switcher/i }),
    ).not.toBeInTheDocument();
  });
});
