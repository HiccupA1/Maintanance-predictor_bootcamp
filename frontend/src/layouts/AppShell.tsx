import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';

import { Button } from '../components/ui/Button';
import { API_BASE_URL, AUTH_MODE } from '../config/env';
import { getSupabaseClient } from '../api/supabaseClient';
import { useBackendHealth } from '../hooks/useBackendHealth';
import { useCurrentUser } from '../hooks/useCurrentUser';
import { hasRole } from '../utils/rbac';

const HEALTH_LABELS: Record<string, { text: string; className: string }> = {
  checking: { text: 'Checking API…', className: 'health-checking' },
  ok: { text: 'API online', className: 'health-ok' },
  degraded: { text: 'Database degraded', className: 'health-degraded' },
  down: { text: 'API unreachable', className: 'health-down' },
};

function navClass({ isActive }: { isActive: boolean }): string {
  return [
    'rounded-lg px-3 py-2 text-sm font-semibold transition-all duration-200',
    isActive
      ? 'bg-white/20 text-white shadow-sm'
      : 'text-slate-300 hover:bg-white/10 hover:text-white',
  ].join(' ');
}

// PUBLIC_INTERFACE
export function AppShell() {
  /** Render authenticated navigation, service status, and the interactive workspace frame. */
  const health = useBackendHealth();
  const healthLabel = HEALTH_LABELS[health];
  const currentUser = useCurrentUser();
  const role = currentUser.user?.role;
  const isOperator = role === 'Operator';
  const [spotlight, setSpotlight] = useState({ x: 50, y: 20 });

  useEffect(() => {
    const handlePointerMove = (event: PointerEvent) => {
      setSpotlight({
        x: (event.clientX / window.innerWidth) * 100,
        y: Math.min((event.clientY / window.innerHeight) * 100, 100),
      });
    };
    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    return () => window.removeEventListener('pointermove', handlePointerMove);
  }, []);

  const signOut = async () => {
    try {
      await getSupabaseClient().auth.signOut();
    } finally {
      window.location.assign('/login');
    }
  };

  return (
    <div
      className="app-shell flex min-h-full flex-col"
      style={{
        '--spotlight-x': `${spotlight.x}%`,
        '--spotlight-y': `${spotlight.y}%`,
      } as React.CSSProperties}
    >
      <header className="app-header relative overflow-hidden border-b border-slate-800 bg-slate-950">
        <div className="pointer-events-none absolute inset-0 opacity-80 [background:radial-gradient(circle_at_var(--spotlight-x)_var(--spotlight-y),rgba(56,189,248,.2),transparent_32%)]" />
        <div className="relative mx-auto flex w-full max-w-7xl flex-wrap items-center gap-5 px-4 py-5 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="brand-mark ring-4 ring-brand-500/20" aria-hidden="true">MP</div>
            <div>
              <span className="block text-base font-bold tracking-tight text-white">
                Maintenance Intelligence
              </span>
              <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">
                Predictive maintenance control center
              </span>
            </div>
          </div>

          <nav aria-label="Primary" className="app-nav flex items-center gap-1">
            <NavLink to="/readings" className={navClass}>Readings</NavLink>
            {!isOperator && (
              <>
                <NavLink to="/work-orders" className={navClass}>Work Orders</NavLink>
                <NavLink to="/equipment" className={navClass}>Equipment</NavLink>
                <NavLink to="/alerts" className={navClass}>Alerts</NavLink>
              </>
            )}
            {hasRole(role, ['Admin']) && (
              <NavLink to="/admin/users" className={navClass}>Admin</NavLink>
            )}
          </nav>

          <div className="ml-auto flex items-center gap-3">
            {currentUser.user && (
              <div className="hidden items-center gap-3 md:flex">
                <div className="text-right text-xs text-slate-400">
                  <span className="block">Signed in as</span>
                  <span className="block font-semibold text-white">{currentUser.user.name}</span>
                </div>
                <span className="role-pill">{currentUser.user.role}</span>
              </div>
            )}
            <Button variant="secondary" className="border-white/20 bg-white/10 px-3 py-2 text-xs text-white hover:bg-white/20" onClick={signOut}>
              Sign out
            </Button>
            <span className={`health-pill ${healthLabel.className}`} title={`API base URL: ${API_BASE_URL}`}>
              {healthLabel.text}
            </span>
          </div>
        </div>
      </header>

      <div className="border-b border-brand-100 bg-gradient-to-r from-brand-50 via-white to-cyan-50">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-3 text-sm sm:px-6 lg:px-8">
          <p className="font-medium text-slate-700">
            {health === 'ok'
              ? 'Live operational data is available.'
              : 'Live data is still connecting—tables and inputs remain available with explicit status feedback.'}
          </p>
          <span className="hidden text-xs font-medium text-slate-500 md:inline">
            Supabase authentication · {AUTH_MODE}
          </span>
        </div>
      </div>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white py-4">
        <div className="mx-auto flex w-full max-w-7xl justify-between gap-4 px-4 text-xs text-slate-500 sm:px-6 lg:px-8">
          <span>Maintenance Intelligence</span>
          <span>Connected to <span className="font-mono">{API_BASE_URL}</span></span>
        </div>
      </footer>
    </div>
  );
}
