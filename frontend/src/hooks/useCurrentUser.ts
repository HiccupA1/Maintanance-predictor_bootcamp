import { useEffect, useState } from 'react';

import { getMe, type CurrentUser } from '../api/auth';
import { useAuthSession } from './useAuthSession';

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
  /** Fetch the current user when the consuming component mounts. */
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const auth = useAuthSession();

  useEffect(() => {
    if (auth.status === 'unauthenticated') {
      setUser(null);
      setError(null);
      setIsLoading(false);
      return;
    }

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
