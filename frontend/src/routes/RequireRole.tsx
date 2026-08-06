import { Navigate, useLocation } from 'react-router-dom';

import { Spinner } from '../components/ui/Spinner';
import { ErrorPanel } from '../components/ui/ErrorPanel';
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
  const { user, isLoading, error } = useCurrentUser();

  if (isLoading) {
    return (
      <div className="card flex justify-center p-10">
        <Spinner label="Checking permissions" />
      </div>
    );
  }

  // If we can't resolve the current user (e.g., /v1/me is failing due to API
  // base URL, CORS, or backend downtime), do not redirect back to /login.
  // Redirecting when user is null creates a loop where authenticated users
  // can never land on any page.
  if (error) {
    return (
      <ErrorPanel
        title="Unable to confirm your access"
        error={error}
        hint="We could not load your profile/role from the backend (/v1/me). Check API connectivity and CORS settings."
      />
    );
  }

  if (!user) {
    return (
      <div className="card flex justify-center p-10">
        <Spinner label="Loading your profile" />
      </div>
    );
  }

  if (!allowedRoles.includes(user.role)) {
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
