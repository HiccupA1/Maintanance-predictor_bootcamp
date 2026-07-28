import { Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from '../layouts/AppShell';
import { ConvertAlertPage } from '../features/alerts/ConvertAlertPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { WorkOrderDetailPage } from '../features/workOrders/WorkOrderDetailPage';
import { WorkOrderEditPage } from '../features/workOrders/WorkOrderEditPage';
import { WorkOrdersListPage } from '../features/workOrders/WorkOrdersListPage';

// PUBLIC_INTERFACE
export function AppRoutes() {
  /**
   * Declare the application routes.
   *
   * Routes:
   * - `/work-orders` — list
   * - `/work-orders/:id` — detail
   * - `/work-orders/:id/edit` — edit
   * - `/alerts/:alertId/convert` — convert alert to work order
   */
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/work-orders" replace />} />
        <Route path="/work-orders" element={<WorkOrdersListPage />} />
        <Route path="/work-orders/:id" element={<WorkOrderDetailPage />} />
        <Route path="/work-orders/:id/edit" element={<WorkOrderEditPage />} />
        <Route path="/alerts/:alertId/convert" element={<ConvertAlertPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
