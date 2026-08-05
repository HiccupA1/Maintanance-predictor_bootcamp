import { useMemo, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';

import { Button } from '../components/ui/Button';
import { ErrorPanel } from '../components/ui/ErrorPanel';
import { Spinner } from '../components/ui/Spinner';
import { getSupabaseClient } from '../api/supabaseClient';
import { useAuthSession } from '../hooks/useAuthSession';

function readNextPath(raw: string | null): string | null {
  if (!raw || !raw.startsWith('/') || raw.startsWith('//')) return null;
  return raw;
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

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const { data, error: signInError } =
        await getSupabaseClient().auth.signInWithPassword({
          email: email.trim(),
          password,
        });

      if (signInError) {
        setError(signInError);
        return;
      }

      // Protected routes require a real session. Do not navigate merely
      // because the password request resolved without one.
      if (!data.session) {
        setError(
          new Error(
            'Sign-in completed without an active session. Please try again.',
          ),
        );
        return;
      }

      navigate(next, { replace: true });
    } catch (err: unknown) {
      setError(err);
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
            {error && <ErrorPanel title="Unable to sign in" error={error} />}

            <div>
              <label className="label" htmlFor="email">Email</label>
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
              <label className="label" htmlFor="password">Password</label>
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

            <Button type="submit" className="w-full" loading={isSubmitting}>
              Sign in
            </Button>

            <div className="rounded-xl border border-brand-100 bg-brand-50 p-4 text-xs leading-5 text-brand-950">
              <p className="font-semibold">Initial administrator bootstrap</p>
              <ol className="mt-2 list-decimal space-y-1 pl-5">
                <li>Run the migration with <code>supabase db push</code>.</li>
                <li>In Supabase Dashboard, open Authentication → Users.</li>
                <li>Create or invite <code>bsankara1609@gmail.com</code> and set its password there.</li>
                <li>Sign in here with that email and password.</li>
                <li>The migration creates or promotes that user’s profile to <strong>Admin</strong>.</li>
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
