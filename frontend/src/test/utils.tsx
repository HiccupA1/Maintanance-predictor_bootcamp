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
    alert_id: 'al-1',
    equipment_id: 'eq-1',
    equipment_name: 'Pump A',
    work_order_number: 1,
    priority: 'HIGH',
    status: 'OPEN',
    due_at: null,
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
    alert_id: 'al-1',
    equipment_id: 'eq-1',
    equipment_name: 'Pump A',
    work_order_number: 1,
    description: 'Replace worn bearing',
    priority: 'HIGH',
    status: 'OPEN',
    issuer_name: 'Priya Nair',
    due_at: null,
    machine_details: null,
    readings_snapshot: null,
    resolution_notes: null,
    root_cause: null,
    closed_at: null,
    created_at: '2026-07-01T10:00:00Z',
    updated_at: '2026-07-01T10:00:00Z',
    parts: [],
    ...overrides,
  };
}
