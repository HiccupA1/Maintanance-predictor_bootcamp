import {
  getLandingPathForRole as getRbacLandingPath,
  type Role,
} from './rbac';

// PUBLIC_INTERFACE
export function getLandingPathForRole(role: Role): string {
  /**
   * Return the default landing route for a given application role.
   *
   * @param role Application role returned by the backend `/me` endpoint.
   * @returns Route path to navigate to after login.
   */
  return getRbacLandingPath(role);
}
