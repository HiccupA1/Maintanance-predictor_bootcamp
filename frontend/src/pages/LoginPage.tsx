import { useMemo, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';

import { Button } from '../components/ui/Button';
import { ErrorPanel } from '../components/ui/ErrorPanel';
import { Spinner } from '../components/ui/Spinner';
import { getSupabaseClient } from '../api/supabaseClient';
import { AUTH_MODE } from '../config/env';
import { useAuthSession } from '../hooks/useAuthSession';

function readNextPath(raw: string | null): string | null {
  if (!raw) return null;
  // Only allow internal paths to avoid open redirects.
  if (!raw.startsWith('/')) return null;
  if (raw.startsWith('//')) return null;
  return raw;
}

// PUBLIC_INTERFACE
export function LoginPage() {
  /**
   * Supabase-backed login screen (email/password).
   *
   * In `dev_shim` mode we don't require Supabase, so this page simply provides
   * a "Continue" action that routes into the app.
   */
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

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (AUTH_MODE === 'dev_shim') {
      navigate(next, { replace: true });
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const client = getSupabaseClient();
      const { error: signInError } = await client.auth.signInWithPassword({
        email: email.trim(),
        password,
      });
      if (signInError) {
        setError(signInError);
        setIsSubmitting(false);
        return;
      }
      navigate(next, { replace: true });
    } catch (err: unknown) {
      setError(err);
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
        {status === 'loading' && AUTH_MODE === 'supabase' ? (
          <div className="flex justify-center py-8">
            <Spinner label="Checking session" />
          </div>
        ) : (
          <form className="space-y-4" onSubmit={submit}>
            {error && <ErrorPanel title="Unable to sign in" error={error} />}

            <div>
              <label className="text-sm font-medium text-slate-700" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required={AUTH_MODE === 'supabase'}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                placeholder="name@company.com"
                disabled={isSubmitting || AUTH_MODE === 'dev_shim'}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required={AUTH_MODE === 'supabase'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                placeholder={AUTH_MODE === 'dev_shim' ? 'Not required in dev mode' : '••••••••'}
                disabled={isSubmitting || AUTH_MODE === 'dev_shim'}
              />
            </div>

            <Button type="submit" className="w-full" loading={isSubmitting}>
              {AUTH_MODE === 'dev_shim' ? 'Continue (dev mode)' : 'Sign in'}
            </Button>

            {AUTH_MODE === 'supabase' && (
              <div className="rounded-md border border-brand-100 bg-brand-50 p-3 text-xs text-brand-900">
                <p className="font-semibold">Initial administrator</p>
                <p className="mt-1">
                  Provision <span className="font-mono">bsankara1609@gmail.com</span> in
                  Supabase Auth, then assign the Admin role from the Admin UI.
                </p>
                <p className="mt-1 text-brand-700">
                  The administrator password must be configured in Supabase Auth and
                  is never stored in frontend code.
                </p>
              </div>
            )}
          </form>
        )}
      </section>
    </div>
  );
}
