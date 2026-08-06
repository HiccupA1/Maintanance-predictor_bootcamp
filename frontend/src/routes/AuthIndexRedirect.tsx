import { Navigate } from 'react-router-dom';

import { Spinner } from '../components/ui/Spinner';
import { ErrorPanel } from '../components/ui/ErrorPanel';
import { useAuthSession } from '../hooks/useAuthSession';
import { useCurrentUser } from '../hooks/useCurrentUser';
import { getLandingPathForRole } from '../utils/landing';

// PUBLIC_INTERFACE
export function AuthIndexRedirect() {
  /**
   * Route element for `/` that decides where to send the user:
   * - unauthenticated => `/login`
   * - authenticated => role landing path (derived from backend `/me`)
   */
  const auth = useAuthSession();
  const currentUser = useCurrentUser();

  if (auth.status === 'loading' || currentUser.isLoading) {
    return (
      <div className="card p-6">
        <Spinner label="Preparing workspace" />
      </div>
    );
  }

  if (auth.status === 'error') {
    return <ErrorPanel title="Authentication unavailable" error={auth.error} />;
  }

  if (auth.status === 'unauthenticated') {
    return <Navigate to="/login" replace />;
  }

  if (currentUser.error) {
    // If the backend profile endpoint is unavailable, do not strand the user on
    // a blocking error screen at `/`. Let them into the shell and allow pages
    // to display their own API errors. `/readings` is the least restrictive page.
    return <Navigate to="/readings" replace />;
  }

  return <Navigate to={getLandingPathForRole(currentUser.user?.role)} replace />;
}
