// PUBLIC_INTERFACE
export type Role =
  | 'Admin'
  | 'PlantManager'
  | 'Operator'
  | 'MaintenanceEngineer';
/** Roles supported by the MVP development RBAC shim. */

// PUBLIC_INTERFACE
export type AppPage =
  | 'readings'
  | 'work-orders'
  | 'equipment'
  | 'alerts'
  | 'admin';
/** Top-level application pages controlled by the PRD role matrix. */

const PAGE_ACCESS: Record<AppPage, readonly Role[]> = {
  readings: ['Operator'],
  'work-orders': ['Admin', 'PlantManager', 'MaintenanceEngineer'],
  equipment: ['Admin', 'PlantManager', 'MaintenanceEngineer'],
  alerts: ['Admin', 'PlantManager', 'MaintenanceEngineer'],
  admin: ['Admin'],
};

// PUBLIC_INTERFACE
export function hasRole(
  userRole: Role | string | null | undefined,
  allowedRoles: readonly Role[],
): boolean {
  /**
   * Check whether a user role is included in an allowed-role list.
   *
   * @param userRole Effective role from the current-user response.
   * @param allowedRoles Roles permitted to perform the action.
   * @returns True when the role is explicitly allowed.
   */
  return Boolean(userRole && allowedRoles.includes(userRole as Role));
}

// PUBLIC_INTERFACE
export function canAccessPage(
  userRole: Role | string | null | undefined,
  page: AppPage,
): boolean {
  /**
   * Determine whether a role may see and use a top-level application page.
   *
   * @param userRole Effective role returned by the backend.
   * @param page Top-level page being evaluated.
   * @returns True only when the role is explicitly permitted.
   */
  return hasRole(userRole, PAGE_ACCESS[page]);
}
