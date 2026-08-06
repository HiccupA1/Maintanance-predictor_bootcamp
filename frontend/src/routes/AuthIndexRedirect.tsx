import { Navigate } from 'react-router-dom';

import { Spinner } from '../components/ui/Spinner';
import { ErrorPanel } from '../components/ui/ErrorPanel';
import { useAuthSession } from '../hooks/useAuthSession';
import { useCurrentUser } from '../hooks/useCurrentUser';
import { getLandingPathForRole } from '../utils/landing';
import { BYPASS_AUTH } from '../config/env';

// PUBLIC_INTERFACE
export function AuthIndexRedirect() {
  /**
   * Route element for `/` that decides where to send the user:
   * - unauthenticated => `/login`
   * - authenticated => role landing path (derived from backend `/me`)
   */
  if (BYPASS_AUTH) {
    // TEMPORARY / DEV-ONLY:
    // Route straight into the app shell for UI testing without login/profile fetch.
    return <Navigate to="/readings" replace />;
  }

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

  // Auth is settled, but the backend identity/role lookup returned no user.
  // This most commonly happens when:
  // - The Supabase session exists but the API does not receive/accept the Bearer token (CORS/proxy stripping headers).
  // - The backend is pointed at a different Supabase project / JWT settings than the frontend.
  // - A transient race returned 401 and was swallowed upstream.
  // Do NOT redirect again here; that creates an infinite loop between `/` and guarded routes.
  if (!currentUser.user) {
    return (
      <ErrorPanel
        title="Signed in, but your profile could not be loaded"
        error={
          new Error(
            [
              'You appear to be authenticated with Supabase, but the backend did not return your /v1/me profile.',
              '',
              'Most common causes:',
              '- VITE_API_BASE_URL is wrong (points to a server that is not configured for this Supabase project)',
              '- CORS/proxy is blocking the Authorization header (Bearer token)',
              '- Backend JWT verification is misconfigured for the Supabase project used by the frontend',
              '',
              'Next steps:',
              '- Open DevTools → Network and inspect GET /v1/me (status code + response)',
              '- Confirm VITE_SUPABASE_URL matches the Supabase project the backend expects',
              '- Confirm VITE_API_BASE_URL points to the intended backend instance',
            ].join('\n'),
          )
        }
        hint="This screen prevents an infinite redirect loop while you verify backend connectivity and token validation."
      />
    );
  }

  return <Navigate to={getLandingPathForRole(currentUser.user?.role)} replace />;
}
