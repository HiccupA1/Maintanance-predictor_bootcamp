import type { ReactNode } from 'react';

import { useCurrentUser } from '../hooks/useCurrentUser';
import { hasRole, type Role } from '../utils/rbac';

// PUBLIC_INTERFACE
export function RoleGate({
  allowedRoles,
  children,
  fallback = null,
}: {
  allowedRoles: readonly Role[];
  children: ReactNode;
  fallback?: ReactNode;
}) {
  /**
   * Render children only after the current user's role is authorized.
   *
   * Loading and failed-user states render the fallback. Consumers that need
   * to display request failures can use `useCurrentUser` directly and render
   * `ErrorPanel` on the affected page.
   *
   * @param allowedRoles Roles permitted to see the protected content.
   * @param children Content shown to an authorized user.
   * @param fallback Optional content shown while loading, on error, or when denied.
   */
  const { user, isLoading } = useCurrentUser();

  if (isLoading || !user || !hasRole(user.role, allowedRoles)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
