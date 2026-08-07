import type { ReactElement } from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import type { WorkOrder, WorkOrderSummary } from '../types/workOrders';

// PUBLIC_INTERFACE
export function renderRoute(
  element: ReactElement,
  { path, route }: { path: string; route: string },
) {
  /**
   * Render a page component inside a memory router at a specific route.
   *
   * @param element The page element under test.
   * @param path Route pattern (e.g. `/work-orders/:id`).
   * @param route Concrete URL to start at (e.g. `/work-orders/wo-1`).
   * @returns The Testing Library render result.
   */
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path={path} element={element} />
      </Routes>
    </MemoryRouter>,
  );
}

// PUBLIC_INTERFACE
export function makeSummary(overrides: Partial<WorkOrderSummary> = {}): WorkOrderSummary {
  /**
   * Build a work order summary fixture.
   *
   * @param overrides Fields to override on the default fixture.
   */
  return {
    id: 'wo-1',
    equipment_id: 'eq-1',
    equipment_name: 'Pump A',
    work_order_number: 1,
    title: 'Replace worn bearing',
    priority: 'HIGH',
    status: 'OPEN',
    created_at: '2026-07-01T10:00:00Z',
    ...overrides,
  };
}

// PUBLIC_INTERFACE
export function makeWorkOrder(overrides: Partial<WorkOrder> = {}): WorkOrder {
  /**
   * Build a full work order fixture.
   *
   * @param overrides Fields to override on the default fixture.
   */
  return {
    id: 'wo-1',
    equipment_id: 'eq-1',
    equipment_name: 'Pump A',
    work_order_number: 1,
    title: 'Replace worn bearing',
    description: 'Replace worn bearing',
    priority: 'HIGH',
    status: 'OPEN',
    created_at: '2026-07-01T10:00:00Z',
    updated_at: '2026-07-01T10:00:00Z',
    ...overrides,
  };
}
