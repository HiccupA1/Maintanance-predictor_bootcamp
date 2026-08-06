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
   * The auth-state listener is registered before the initial session lookup so
   * a sign-in event cannot be missed while getSession is resolving.
   */
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    // AUTH_MODE is supabase-only; keep the guard in case runtime configuration
    // is expanded in the future.
    if (AUTH_MODE !== 'supabase') {
      setStatus('error');
      setSession(null);
      setError(new Error(`Unsupported auth mode: ${String(AUTH_MODE)}`));
      return;
    }

    let mounted = true;
    let subscription: { unsubscribe: () => void } | null = null;
    let sawSignedInEvent = false;

    try {
      const client = getSupabaseClient();

      // Register the listener first so authentication events are not missed
      // while the persisted session is being loaded.
      const { data } = client.auth.onAuthStateChange((_event, nextSession) => {
        if (!mounted) return;
        if (_event === 'SIGNED_IN') {
          sawSignedInEvent = true;
        }
        setSession(nextSession);
        setError(null);
        setStatus(nextSession ? 'authenticated' : 'unauthenticated');
      });
      subscription = data.subscription;

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
          // If we saw a SIGNED_IN event but still cannot read a session, it
          // strongly suggests session persistence is blocked (storage/cookies)
          // or the runtime is preventing Supabase from restoring auth state.
          if (!data.session && sawSignedInEvent) {
            setStatus('error');
            setSession(null);
            setError(
              new Error(
                [
                  'Signed in, but no session could be restored.',
                  '',
                  'This typically happens when the browser blocks storage/cookies (private browsing, strict tracking protection) or when the app is embedded / running with restricted storage.',
                  '',
                  'Try:',
                  '- Disable private browsing / allow cookies for this site',
                  '- Ensure third-party cookies/storage are allowed (if embedded)',
                  '- Try another browser profile to confirm',
                ].join('\n'),
              ),
            );
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
    } catch (err: unknown) {
      if (mounted) {
        setStatus('error');
        setError(err);
        setSession(null);
      }
    }

    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, []);

  const user = useMemo(() => session?.user ?? null, [session]);

  return { status, session, user, error };
}
