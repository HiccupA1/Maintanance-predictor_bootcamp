import type { Role } from './rbac';

const ROLE_LANDING: Record<Role, string> = {
  Admin: '/equipment',
  PlantManager: '/work-orders',
  Operator: '/readings',
  MaintenanceEngineer: '/alerts',
};

// PUBLIC_INTERFACE
export function getLandingPathForRole(role: Role): string {
  /**
   * Return the default landing route for a given application role.
   *
   * @param role Application role returned by the backend `/me` endpoint.
   * @returns Route path to navigate to after login.
   */
  return ROLE_LANDING[role] ?? '/work-orders';
}
