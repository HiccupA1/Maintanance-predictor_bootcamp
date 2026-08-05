import { Navigate, useLocation } from 'react-router-dom';

import { Spinner } from '../components/ui/Spinner';
import { useCurrentUser } from '../hooks/useCurrentUser';
import { getLandingPathForRole, type Role } from '../utils/rbac';

// PUBLIC_INTERFACE
export function RequireRole({
  allowedRoles,
  children,
}: {
  allowedRoles: readonly Role[];
  children: React.ReactNode;
}) {
  /**
   * Restrict a route to users with one of the supplied roles.
   *
   * Unauthorized users are redirected to the first top-level page allowed for
   * their resolved role rather than to a hard-coded route.
   */
  const location = useLocation();
  const { user, isLoading } = useCurrentUser();

  if (isLoading) {
    return (
      <div className="card flex justify-center p-10">
        <Spinner label="Checking permissions" />
      </div>
    );
  }

  if (!user || !allowedRoles.includes(user.role)) {
    return (
      <Navigate
        to={getLandingPathForRole(user?.role)}
        replace
        state={{ from: location.pathname }}
      />
    );
  }

  return <>{children}</>;
}
