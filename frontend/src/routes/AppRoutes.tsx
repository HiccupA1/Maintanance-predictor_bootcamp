import { Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from '../layouts/AppShell';
import { LoginPage } from '../pages/LoginPage';
import { AlertsListPage } from '../features/alerts/AlertsListPage';
import { AlertDetailPage } from '../features/alerts/AlertDetailPage';
import { ConvertAlertPage } from '../features/alerts/ConvertAlertPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { WorkOrderDetailPage } from '../features/workOrders/WorkOrderDetailPage';
import { WorkOrderEditPage } from '../features/workOrders/WorkOrderEditPage';
import { WorkOrdersListPage } from '../features/workOrders/WorkOrdersListPage';
import { EquipmentListPage } from '../features/equipment/EquipmentListPage';
import { EquipmentDetailPage } from '../features/equipment/EquipmentDetailPage';
import { EquipmentFormPage } from '../features/equipment/EquipmentFormPage';
import { ReadingsPage } from '../features/readings/ReadingsPage';
import { RequireAuth } from './RequireAuth';
import { AuthIndexRedirect } from './AuthIndexRedirect';
import { AdminUsersPage } from '../features/admin/AdminUsersPage';

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
   * - `/alerts` — alerts list
   * - `/alerts/:alertId` — alert detail
   * - `/alerts/:alertId/convert` — convert alert to work order
   */
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<AuthIndexRedirect />} />
        <Route path="/work-orders" element={<WorkOrdersListPage />} />
        <Route path="/work-orders/:id" element={<WorkOrderDetailPage />} />
        <Route path="/work-orders/:id/edit" element={<WorkOrderEditPage />} />
        <Route path="/equipment" element={<EquipmentListPage />} />
        <Route path="/equipment/new" element={<EquipmentFormPage mode="create" />} />
        <Route path="/equipment/:id" element={<EquipmentDetailPage />} />
        <Route path="/equipment/:id/edit" element={<EquipmentFormPage mode="edit" />} />
        <Route path="/readings" element={<ReadingsPage />} />
        <Route path="/alerts" element={<AlertsListPage />} />
        <Route path="/alerts/:alertId" element={<AlertDetailPage />} />
        <Route path="/alerts/:alertId/convert" element={<ConvertAlertPage />} />

        <Route path="/admin/users" element={<AdminUsersPage />} />

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
