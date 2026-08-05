// PUBLIC_INTERFACE
export type Role =
  | 'Admin'
  | 'PlantManager'
  | 'Operator'
  | 'MaintenanceEngineer';
/** Roles supported by the MVP development RBAC shim. */

const ROLE_BY_NORMALIZED_VALUE: Record<string, Role> = {
  admin: 'Admin',
  plantmanager: 'PlantManager',
  operator: 'Operator',
  maintenanceengineer: 'MaintenanceEngineer',
};

// PUBLIC_INTERFACE
export function normalizeRole(
  userRole: Role | string | null | undefined,
): Role | null {
  /** Normalize a backend role into the frontend's canonical role vocabulary. */
  if (typeof userRole !== 'string') return null;
  return ROLE_BY_NORMALIZED_VALUE[userRole.trim().toLowerCase()] ?? null;
}

// PUBLIC_INTERFACE
export type AppPage =
  | 'readings'
  | 'work-orders'
  | 'equipment'
  | 'alerts'
  | 'admin';
/** Top-level application pages controlled by the PRD role matrix. */

const PAGE_ACCESS: Record<AppPage, readonly Role[]> = {
  // All personas may review readings; the Readings page separately gates
  // capture and correction controls to Operators.
  readings: ['Admin', 'PlantManager', 'Operator', 'MaintenanceEngineer'],
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
  const normalizedRole = normalizeRole(userRole);
  return Boolean(normalizedRole && allowedRoles.includes(normalizedRole));
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

const PAGE_PATHS: Record<AppPage, string> = {
  readings: '/readings',
  'work-orders': '/work-orders',
  equipment: '/equipment',
  alerts: '/alerts',
  admin: '/admin/users',
};

// PUBLIC_INTERFACE
export function getLandingPathForRole(
  userRole: Role | string | null | undefined,
): string {
  /** Return the first top-level route explicitly allowed for the supplied role. */
  if (!normalizeRole(userRole)) return '/login';

  const page = (Object.keys(PAGE_ACCESS) as AppPage[]).find((candidate) =>
    canAccessPage(userRole, candidate),
  );
  return page ? PAGE_PATHS[page] : '/login';
}
