import { Route, Routes } from 'react-router-dom';

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
import { RequireRole } from './RequireRole';
import { AdminUsersPage } from '../features/admin/AdminUsersPage';

// PUBLIC_INTERFACE
export function AppRoutes() {
  /**
   * Declare the application routes and enforce role-specific access.
   *
   * Operators can use only the readings intake route. Other authenticated
   * roles receive access to the operational screens appropriate to them.
   */
  const operationalRoles = ['Admin', 'PlantManager', 'MaintenanceEngineer'] as const;
  const managementRoles = ['Admin', 'PlantManager'] as const;

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
        <Route
          path="/readings"
          element={
            <RequireRole
              allowedRoles={[
                'Admin',
                'PlantManager',
                'Operator',
                'MaintenanceEngineer',
              ]}
            >
              <ReadingsPage />
            </RequireRole>
          }
        />

        <Route
          path="/work-orders"
          element={
            <RequireRole allowedRoles={operationalRoles}>
              <WorkOrdersListPage />
            </RequireRole>
          }
        />
        <Route
          path="/work-orders/:id"
          element={
            <RequireRole allowedRoles={operationalRoles}>
              <WorkOrderDetailPage />
            </RequireRole>
          }
        />
        <Route
          path="/work-orders/:id/edit"
          element={
            <RequireRole allowedRoles={operationalRoles}>
              <WorkOrderEditPage />
            </RequireRole>
          }
        />

        <Route
          path="/equipment"
          element={
            <RequireRole allowedRoles={operationalRoles}>
              <EquipmentListPage />
            </RequireRole>
          }
        />
        <Route
          path="/equipment/new"
          element={
            <RequireRole allowedRoles={managementRoles}>
              <EquipmentFormPage mode="create" />
            </RequireRole>
          }
        />
        <Route
          path="/equipment/:id"
          element={
            <RequireRole allowedRoles={operationalRoles}>
              <EquipmentDetailPage />
            </RequireRole>
          }
        />
        <Route
          path="/equipment/:id/edit"
          element={
            <RequireRole allowedRoles={managementRoles}>
              <EquipmentFormPage mode="edit" />
            </RequireRole>
          }
        />

        <Route
          path="/alerts"
          element={
            <RequireRole allowedRoles={operationalRoles}>
              <AlertsListPage />
            </RequireRole>
          }
        />
        <Route
          path="/alerts/:alertId"
          element={
            <RequireRole allowedRoles={operationalRoles}>
              <AlertDetailPage />
            </RequireRole>
          }
        />
        <Route
          path="/alerts/:alertId/convert"
          element={
            <RequireRole allowedRoles={operationalRoles}>
              <ConvertAlertPage />
            </RequireRole>
          }
        />

        <Route
          path="/admin/users"
          element={
            <RequireRole allowedRoles={['Admin']}>
              <AdminUsersPage />
            </RequireRole>
          }
        />

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
