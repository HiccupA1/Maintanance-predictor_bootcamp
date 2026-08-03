import { useEffect, useMemo, useState } from 'react';
import type { Session, User } from '@supabase/supabase-js';

import { getSupabaseClient } from '../api/supabaseClient';
import { AUTH_MODE } from '../config/env';

type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated' | 'error';

// PUBLIC_INTERFACE
export interface AuthSessionState {
  status: AuthStatus;
  session: Session | null;
  user: User | null;
  error: unknown;
}
/** State returned by {@link useAuthSession}. */

// PUBLIC_INTERFACE
export function useAuthSession(): AuthSessionState {
  /**
   * Track the current Supabase Auth session.
   *
   * In `dev_shim` mode we consider the user authenticated and let the existing
   * `/me` dev identity shim continue to drive RBAC (to avoid disrupting local workflows).
   */
  const [status, setStatus] = useState<AuthStatus>(
    AUTH_MODE === 'dev_shim' ? 'authenticated' : 'loading',
  );
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    if (AUTH_MODE === 'dev_shim') {
      setStatus('authenticated');
      setSession(null);
      setError(null);
      return;
    }

    let mounted = true;

    const client = getSupabaseClient();

    void client.auth
      .getSession()
      .then(({ data, error: sessionError }) => {
        if (!mounted) return;
        if (sessionError) {
          setStatus('error');
          setError(sessionError);
          setSession(null);
          return;
        }
        setSession(data.session ?? null);
        setError(null);
        setStatus(data.session ? 'authenticated' : 'unauthenticated');
      })
      .catch((err: unknown) => {
        if (!mounted) return;
        setStatus('error');
        setError(err);
        setSession(null);
      });

    const { data } = client.auth.onAuthStateChange((_event, nextSession) => {
      if (!mounted) return;
      setSession(nextSession);
      setError(null);
      setStatus(nextSession ? 'authenticated' : 'unauthenticated');
    });

    return () => {
      mounted = false;
      data.subscription.unsubscribe();
    };
  }, []);

  const user = useMemo(() => session?.user ?? null, [session]);

  return { status, session, user, error };
}
