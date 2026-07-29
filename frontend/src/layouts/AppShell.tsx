import { NavLink, Outlet } from 'react-router-dom';

import { API_BASE_URL } from '../config/env';
import { useBackendHealth } from '../hooks/useBackendHealth';

const HEALTH_LABELS: Record<string, { text: string; className: string }> = {
  checking: { text: 'Checking API…', className: 'bg-slate-100 text-slate-600' },
  ok: { text: 'API online', className: 'bg-emerald-100 text-emerald-800' },
  degraded: { text: 'API degraded', className: 'bg-amber-100 text-amber-800' },
  down: { text: 'API unreachable', className: 'bg-red-100 text-red-800' },
};

/** Nav link styling helper. */
function navClass({ isActive }: { isActive: boolean }): string {
  return [
    'rounded-md px-3 py-2 text-sm font-medium',
    isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100',
  ].join(' ');
}

// PUBLIC_INTERFACE
export function AppShell() {
  /**
   * Application shell providing the header, primary navigation, backend
   * health indicator, and the routed page outlet.
   */
  const health = useBackendHealth();
  const healthLabel = HEALTH_LABELS[health];

  return (
    <div className="flex min-h-full flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-4 py-3">
          <span className="text-base font-semibold text-slate-900">
            Maintenance Work Orders
          </span>
          <nav aria-label="Primary" className="flex items-center gap-1">
            <NavLink to="/work-orders" className={navClass}>
              Work Orders
            </NavLink>
            <NavLink to="/equipment" className={navClass}>
              Equipment
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${healthLabel.className}`}
              title={`API base URL: ${API_BASE_URL}`}
            >
              {healthLabel.text}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white py-3">
        <div className="mx-auto max-w-6xl px-4 text-xs text-slate-500">
          Connected to <span className="font-mono">{API_BASE_URL}</span>
        </div>
      </footer>
    </div>
  );
}
