import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { AppRoutes } from './AppRoutes';

describe('AppRoutes', () => {
  it('renders the NotFound page for unknown routes', async () => {
    render(
      <MemoryRouter initialEntries={['/does-not-exist']}>
        <AppRoutes />
      </MemoryRouter>,
    );

    // NotFoundPage is already present in the app; we assert on a generic,
    // user-visible signal rather than internal route structure.
    expect(
      await screen.findByRole('heading', { name: /not found/i }),
    ).toBeInTheDocument();
  });

  it('redirects the index route to /work-orders', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppRoutes />
      </MemoryRouter>,
    );

    // WorkOrdersListPage includes a prominent heading; this keeps the test
    // resilient while validating the index redirect.
    expect(
      await screen.findByRole('heading', { name: /work orders/i }),
    ).toBeInTheDocument();
  });

  it('renders a known feature route', async () => {
    render(
      <MemoryRouter initialEntries={['/equipment']}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole('heading', { name: /equipment/i }),
    ).toBeInTheDocument();
  });

  it('does not crash when API hooks run under the shell', async () => {
    // Some pages run data hooks immediately; this test is a sanity check that
    // routing + shell composition works in the test environment.
    // (Network calls are mocked at the fetch layer by individual feature tests.)
    render(
      <MemoryRouter initialEntries={['/alerts']}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: /alerts/i })).toBeTruthy();
  });
});
