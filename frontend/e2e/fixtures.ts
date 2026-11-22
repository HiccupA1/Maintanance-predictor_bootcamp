/**
 * Shared E2E fixtures.
 *
 * Authentication: the browser receives a Supabase-shaped session, signed by
 * the test key from tools/testenv, in the localStorage key supabase-js reads
 * (`sb-localhost-auth-token`). The API verifies that token through its real
 * JWKS path. The Supabase Auth HTTP endpoints (sign-in, user, logout) are
 * stubbed at the network layer, because the real Supabase service is outside
 * the system under test.
 */
import fs from 'node:fs';
import path from 'node:path';
import { test as base, expect, type APIRequestContext, type Page } from '@playwright/test';

import { API_URL, E2E_DIR } from './env';

export type Role = 'Admin' | 'PlantManager' | 'Operator' | 'MaintenanceEngineer';
export const ROLES: Role[] = ['Admin', 'PlantManager', 'Operator', 'MaintenanceEngineer'];
export const NAMES: Record<Role, string> = {
  Admin: 'Ada Admin',
  PlantManager: 'Pat Manager',
  Operator: 'Olu Operator',
  MaintenanceEngineer: 'Mia Engineer',
};

type Session = Record<string, unknown> & { access_token: string; user: Record<string, unknown> };
const sessions = JSON.parse(
  fs.readFileSync(path.join(E2E_DIR, 'sessions.json'), 'utf8'),
) as Record<Role, Session>;

export const STORAGE_KEY = 'sb-localhost-auth-token';
export const SUPABASE = 'http://localhost:54321';

/** Unique suffix so parallel tests never share records. */
export const uid = () =>
  `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`.toUpperCase();

/** Stub the Supabase Auth endpoints; `signIn` decides the sign-in result. */
export async function stubSupabase(page: Page, signIn: Role | 'fail' = 'fail') {
  await page.route(`${SUPABASE}/**`, async (route) => {
    const url = route.request().url();
    if (url.includes('/auth/v1/token')) {
      if (signIn === 'fail') {
        return route.fulfill({
          status: 400,
          json: { error: 'invalid_grant', error_description: 'Invalid login credentials' },
        });
      }
      return route.fulfill({ json: sessions[signIn] });
    }
    if (url.includes('/auth/v1/user')) {
      const role = signIn === 'fail' ? 'Operator' : signIn;
      return route.fulfill({ json: sessions[role].user });
    }
    if (url.includes('/auth/v1/logout')) return route.fulfill({ status: 204, body: '' });
    return route.fulfill({ json: {} });
  });
}

/** Start the page already signed in as `role`. */
export async function signInAs(page: Page, role: Role) {
  await stubSupabase(page, role);
  await page.addInitScript(
    ([key, value]) => {
      if (!window.sessionStorage.getItem('e2e-signed-out')) {
        window.localStorage.setItem(key, value);
      }
    },
    [STORAGE_KEY, JSON.stringify(sessions[role])],
  );
}

/** API client authenticated as `role`, for test setup and verification. */
export class Api {
  constructor(
    private readonly request: APIRequestContext,
    private readonly role: Role,
  ) {}

  private headers() {
    return { Authorization: `Bearer ${sessions[this.role].access_token}` };
  }

  as(role: Role) {
    return new Api(this.request, role);
  }

  async call<T = unknown>(method: string, url: string, data?: unknown): Promise<T> {
    const resp = await this.request.fetch(`${API_URL}/v1${url}`, {
      method,
      headers: this.headers(),
      data,
    });
    if (!resp.ok()) {
      throw new Error(`${method} ${url} -> ${resp.status()} ${await resp.text()}`);
    }
    return (resp.status() === 204 ? undefined : await resp.json()) as T;
  }

  status(method: string, url: string, data?: unknown) {
    return this.request
      .fetch(`${API_URL}/v1${url}`, { method, headers: this.headers(), data })
      .then((r) => r.status());
  }

  /** Equipment with one parameter; returns ids. As Admin + PlantManager. */
  async machine(
    opts: { min?: number | null; max?: number | null; criticality?: number; name?: string } = {},
  ) {
    const id = `E2E-${uid()}`;
    const eq = await this.as('Admin').call<{ id: string; equipment_id: string; name: string }>(
      'POST',
      '/equipment',
      {
        equipment_id: id,
        name: opts.name ?? `Pump ${id}`,
        location: 'E2E plant',
        type: 'Pump',
        criticality: opts.criticality ?? 3,
      },
    );
    const param = await this.as('PlantManager').call<{ id: string; name: string }>(
      'POST',
      `/equipment/${id}/parameters`,
      {
        name: 'Temperature',
        unit: 'C',
        min_threshold: opts.min === undefined ? 10 : opts.min,
        max_threshold: opts.max === undefined ? 80 : opts.max,
        active: true,
      },
    );
    return { equipmentId: id, equipmentPk: eq.id, name: eq.name, parameterId: param.id };
  }

  reading(equipmentId: string, parameterId: string, value: string) {
    return this.as('Operator').call<{ id: string }>('POST', '/readings', {
      equipment_id: equipmentId,
      parameter_id: parameterId,
      value,
    });
  }

  async alertFor(equipmentPk: string) {
    const alerts = await this.as('PlantManager').call<
      { id: string; equipment_id: string; status: string; source?: string }[]
    >('GET', '/alerts');
    return alerts.filter((a) => a.equipment_id === equipmentPk);
  }

  /** Machine with a breach -> one open threshold alert. */
  async machineWithAlert() {
    const m = await this.machine();
    await this.reading(m.equipmentId, m.parameterId, '95');
    const [alert] = await this.alertFor(m.equipmentPk);
    return { ...m, alertId: alert.id };
  }
}

type Fixtures = { api: Api };

export const test = base.extend<Fixtures>({
  api: async ({ request }, use) => {
    await use(new Api(request, 'Admin'));
  },
});

export { expect };
