import { useEffect, useState } from 'react';

import { getMe, type CurrentUser } from '../api/auth';
import { useAuthSession } from './useAuthSession';
import { ApiError } from '../api/client';

/** Ignore errors caused by an intentional request abort. */
function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

// PUBLIC_INTERFACE
export interface CurrentUserState {
  user: CurrentUser | null;
  isLoading: boolean;
  error: unknown;
}
/** State returned while loading the current user. */

// PUBLIC_INTERFACE
export function useCurrentUser(): CurrentUserState {
  /**
   * Fetch the current user once when the consuming component mounts.
   *
   * @returns The cached component-local user, loading state, and request error.
   */
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const auth = useAuthSession();

  useEffect(() => {
    // When unauthenticated, short-circuit: consumers can decide whether to redirect.
    if (auth.status === 'unauthenticated') {
      setUser(null);
      setError(null);
      setIsLoading(false);
      return;
    }

    // In Supabase mode, wait until auth settles before calling /me.
    if (auth.status === 'loading') {
      setIsLoading(true);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;

    void getMe(controller.signal)
      .then((currentUser) => {
        if (cancelled) return;
        setUser(currentUser);
        setError(null);
        setIsLoading(false);
      })
      .catch((requestError: unknown) => {
        if (cancelled || isAbort(requestError)) return;
        // Treat auth failures as "no user" instead of surfacing as an app error panel everywhere.
        if (requestError instanceof ApiError && requestError.status === 401) {
          setUser(null);
          setError(null);
          setIsLoading(false);
          return;
        }
        setUser(null);
        setError(requestError);
        setIsLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [auth.status]);

  return { user, isLoading, error };
}
