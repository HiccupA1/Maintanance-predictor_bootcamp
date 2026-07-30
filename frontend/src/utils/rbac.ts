// PUBLIC_INTERFACE
export type Role =
  | 'Admin'
  | 'PlantManager'
  | 'Operator'
  | 'MaintenanceEngineer';
/** Roles supported by the MVP development RBAC shim. */

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
