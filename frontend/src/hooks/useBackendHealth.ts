import { useEffect, useState } from 'react';

import { getDbHealth, getHealth } from '../api/health';

// PUBLIC_INTERFACE
export type BackendHealthState = 'checking' | 'ok' | 'degraded' | 'down';
/** Aggregated backend availability state shown in the app shell. */

// PUBLIC_INTERFACE
export function useBackendHealth(): BackendHealthState {
  /**
   * Probe `GET /health` and `GET /health/db` once on mount.
   *
   * @returns `checking` while in flight, `ok` when both probes succeed,
   *   `degraded` when liveness passes but the database probe fails, and
   *   `down` when the service is unreachable.
   */
  const [state, setState] = useState<BackendHealthState>('checking');

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    void (async () => {
      try {
        await getHealth(controller.signal);
      } catch {
        if (!cancelled) setState('down');
        return;
      }
      try {
        await getDbHealth(controller.signal);
        if (!cancelled) setState('ok');
      } catch {
        if (!cancelled) setState('degraded');
      }
    })();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  return state;
}
