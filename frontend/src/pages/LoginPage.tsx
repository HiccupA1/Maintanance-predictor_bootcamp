import { useMemo, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';

import { Button } from '../components/ui/Button';
import { ErrorPanel } from '../components/ui/ErrorPanel';
import { Spinner } from '../components/ui/Spinner';
import { getSupabaseClient, SupabaseConfigError } from '../api/supabaseClient';
import { useAuthSession } from '../hooks/useAuthSession';

function readNextPath(raw: string | null): string | null {
  if (!raw || !raw.startsWith('/') || raw.startsWith('//')) return null;
  return raw;
}

async function waitForSupabaseSession(options?: {
  timeoutMs?: number;
  pollIntervalMs?: number;
}): Promise<boolean> {
  const timeoutMs = options?.timeoutMs ?? 1500;
  const pollIntervalMs = options?.pollIntervalMs ?? 150;
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeoutMs) {
    const { data, error } = await getSupabaseClient().auth.getSession();
    if (error) throw error;
    if (data.session) return true;
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
  }

  return false;
}

function storageLikelyBlocked(): boolean {
  try {
    const key = '__mp_storage_test__';
    window.localStorage.setItem(key, '1');
    window.localStorage.removeItem(key);
    return false;
  } catch {
    return true;
  }
}

// PUBLIC_INTERFACE
export function LoginPage() {
  /** Render the Supabase email/password sign-in screen and bootstrap guidance. */
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const next = useMemo(() => {
    const fromState = (location.state as { from?: string } | null)?.from ?? null;
    return readNextPath(fromState) ?? readNextPath(params.get('next')) ?? '/';
  }, [location.state, params]);

  const { status } = useAuthSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const supabaseConfigError = useMemo(() => {
    try {
      // Force early initialization so we can show a clear configuration error
      // before the user hits "Sign in" and sees a generic fetch failure.
      getSupabaseClient();
      return null;
    } catch (err: unknown) {
      return err instanceof SupabaseConfigError ? err : null;
    }
  }, []);

  function normalizeAuthError(err: unknown): unknown {
    // Supabase fetch failures often surface as TypeError with messages like:
    // - "Failed to fetch" (Chromium)
    // - "NetworkError when attempting to fetch resource." (Firefox)
    // - "fetch failed" / "Network request failed" (some runtimes)
    // Provide a more actionable message so misconfig / CORS issues can be resolved quickly.
    const message =
      err instanceof Error ? err.message : typeof err === 'string' ? err : '';
    const looksLikeFetchFailure =
      err instanceof TypeError &&
      /failed to fetch|networkerror|network request failed|fetch failed|load failed/i.test(
        message,
      );
    const looksLikeCorsHint =
      /cors|access-control-allow-origin|cross-origin/i.test(message);

    if (looksLikeFetchFailure || looksLikeCorsHint) {
      return new Error(
        [
          'Network error contacting Supabase.',
          'Check:',
          '- VITE_SUPABASE_URL is correct (https://<project-ref>.supabase.co)',
          '- VITE_SUPABASE_ANON_KEY is correct for that project',
          '- Browser is not blocking mixed content (http page calling https or vice versa)',
          '- Supabase Dashboard → Authentication → URL Configuration allows your site URL (for hosted environments)',
        ].join('\n'),
      );
    }
    return err;
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (supabaseConfigError) {
      setError(supabaseConfigError);
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const { data, error: signInError } =
        await getSupabaseClient().auth.signInWithPassword({
          email: email.trim(),
          password,
        });

      if (signInError) {
        setError(normalizeAuthError(signInError));
        return;
      }

      // Supabase can occasionally return `session: null` momentarily even though
      // the credentials are valid and the auth state will update shortly after.
      // To avoid a "successful login that doesn't log in", wait briefly for the
      // session to be observable before navigating into protected routes.
      const hasSession = Boolean(data.session) || (await waitForSupabaseSession());
      if (!hasSession) {
        const blocked = storageLikelyBlocked();
        setError(
          new Error(
            [
              'Signed in successfully, but the session could not be established.',
              '',
              blocked
                ? 'Your browser appears to be blocking local storage/cookies, which prevents Supabase from persisting the session.'
                : 'This can happen if storage/cookies are blocked, the browser is in private mode, or the environment restricts persistence.',
              '',
              'Try:',
              '- Disable private browsing / allow cookies for this site',
              '- Turn off strict tracking protection for this domain',
              '- If embedded, allow third-party cookies/storage',
              '- Hard refresh and sign in again',
            ].join('\n'),
          ),
        );
        return;
      }

      navigate(next, { replace: true });
    } catch (err: unknown) {
      setError(normalizeAuthError(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-md flex-col gap-6 pt-8">
      <header className="text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-xl font-bold text-white shadow-card">
          MP
        </div>
        <p className="text-xs font-semibold uppercase tracking-widest text-brand-600">
          Maintenance intelligence
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">Welcome back</h1>
        <p className="mt-1 text-sm text-slate-600">
          Use your authorized plant account to access work orders and alerts.
        </p>
      </header>

      <section className="card p-6 shadow-card">
        {status === 'loading' ? (
          <div className="flex justify-center py-8">
            <Spinner label="Checking session" />
          </div>
        ) : (
          <form className="space-y-4" onSubmit={submit}>
            {(supabaseConfigError || error) && (
              <ErrorPanel
                title={
                  supabaseConfigError
                    ? 'Supabase is not configured'
                    : 'Unable to sign in'
                }
                error={supabaseConfigError ?? error}
              />
            )}

            <div>
              <label className="label" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                className="input"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="name@company.com"
                disabled={isSubmitting}
              />
            </div>

            <div>
              <label className="label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                className="input"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                disabled={isSubmitting}
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              loading={isSubmitting}
              disabled={isSubmitting || Boolean(supabaseConfigError)}
            >
              Sign in
            </Button>

            <div className="rounded-xl border border-brand-100 bg-brand-50 p-4 text-xs leading-5 text-brand-950">
              <p className="font-semibold">Initial administrator bootstrap</p>
              <ol className="mt-2 list-decimal space-y-1 pl-5">
                <li>
                  Run the migration with <code>supabase db push</code>.
                </li>
                <li>In Supabase Dashboard, open Authentication → Users.</li>
                <li>
                  Create or invite <code>bsankara1609@gmail.com</code> and set its
                  password there.
                </li>
                <li>Sign in here with that email and password.</li>
                <li>
                  The migration creates or promotes that user’s profile to{' '}
                  <strong>Admin</strong>.
                </li>
                <li>Open Admin → Users to confirm roles and manage additional accounts.</li>
              </ol>
              <p className="mt-3 text-brand-800">
                Passwords and service-role keys are never stored in frontend code.
              </p>
            </div>
          </form>
        )}
      </section>
    </div>
  );
}
