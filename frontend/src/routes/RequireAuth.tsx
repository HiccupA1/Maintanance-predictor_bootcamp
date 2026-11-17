import { Navigate, useLocation } from 'react-router-dom';

import { Spinner } from '../components/ui/Spinner';
import { ErrorPanel } from '../components/ui/ErrorPanel';
import { useAuthSession } from '../hooks/useAuthSession';
import { BYPASS_AUTH } from '../config/env';

// PUBLIC_INTERFACE
export function RequireAuth({ children }: { children: React.ReactNode }) {
  /**
   * Guard for routes that require an authenticated session.
   *
   * Redirects to `/login` with a `next` path so the user returns after sign-in.
   */
  if (BYPASS_AUTH) {
    // TEMPORARY / DEV-ONLY:
    // Allows working on landing pages + table-driven UI without being blocked by auth.
    // Revert by setting `VITE_BYPASS_AUTH=false` (or removing it) and restoring normal login flow.
    return <>{children}</>;
  }

  // eslint-disable-next-line react-hooks/rules-of-hooks -- D11: hook after BYPASS_AUTH early return (build-time constant)
  const location = useLocation();
  // eslint-disable-next-line react-hooks/rules-of-hooks -- D11: hook after BYPASS_AUTH early return (build-time constant)
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
