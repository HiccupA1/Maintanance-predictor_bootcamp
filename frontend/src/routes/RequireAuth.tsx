import { Navigate, useLocation } from 'react-router-dom';

import { Spinner } from '../components/ui/Spinner';
import { ErrorPanel } from '../components/ui/ErrorPanel';
import { useAuthSession } from '../hooks/useAuthSession';

// PUBLIC_INTERFACE
export function RequireAuth({ children }: { children: React.ReactNode }) {
  /**
   * Guard for routes that require an authenticated session.
   *
   * Redirects to `/login` with a `next` path so the user returns after sign-in.
   */
  const location = useLocation();
  const { status, error } = useAuthSession();

  if (status === 'loading') {
    return (
      <div className="card p-6">
        <Spinner label="Loading session" />
      </div>
    );
  }

  if (status === 'error') {
    return <ErrorPanel title="Authentication unavailable" error={error} />;
  }

  if (status === 'unauthenticated') {
    const next = `${location.pathname}${location.search}${location.hash}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace state={{ from: next }} />;
  }

  return <>{children}</>;
}
