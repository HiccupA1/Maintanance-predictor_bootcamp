import { Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from '../layouts/AppShell';
import { ConvertAlertPage } from '../features/alerts/ConvertAlertPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { WorkOrderDetailPage } from '../features/workOrders/WorkOrderDetailPage';
import { WorkOrderEditPage } from '../features/workOrders/WorkOrderEditPage';
import { WorkOrdersListPage } from '../features/workOrders/WorkOrdersListPage';
import { EquipmentListPage } from '../features/equipment/EquipmentListPage';
import { EquipmentDetailPage } from '../features/equipment/EquipmentDetailPage';
import { EquipmentFormPage } from '../features/equipment/EquipmentFormPage';
import { ReadingsPage } from '../features/readings/ReadingsPage';

// PUBLIC_INTERFACE
export function AppRoutes() {
  /**
   * Declare the application routes.
   *
   * Routes:
   * - `/work-orders` — list
   * - `/work-orders/:id` — detail
   * - `/work-orders/:id/edit` — edit
   * - `/equipment` — equipment list
   * - `/readings` — manual readings capture and history
   * - `/alerts/:alertId/convert` — convert alert to work order
   */
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/work-orders" replace />} />
        <Route path="/work-orders" element={<WorkOrdersListPage />} />
        <Route path="/work-orders/:id" element={<WorkOrderDetailPage />} />
        <Route path="/work-orders/:id/edit" element={<WorkOrderEditPage />} />
        <Route path="/equipment" element={<EquipmentListPage />} />
        <Route path="/equipment/new" element={<EquipmentFormPage mode="create" />} />
        <Route path="/equipment/:id" element={<EquipmentDetailPage />} />
        <Route path="/equipment/:id/edit" element={<EquipmentFormPage mode="edit" />} />
        <Route path="/readings" element={<ReadingsPage />} />
        <Route path="/alerts/:alertId/convert" element={<ConvertAlertPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
