/**
 * Browser end-to-end tests: the real frontend build talking to the real API
 * and Postgres (Docs/stage-7/e2e-test-matrix.md, Docs/runbooks/e2e.md).
 *
 * Prerequisites, which CI performs:
 *   1. Postgres at DATABASE_URL, migrated (`alembic upgrade head`).
 *   2. `python -m tools.testenv.seed $E2E_DIR` from the repo root, which writes
 *      the JWKS, per-role tokens and sessions, and seeds users and the model.
 * Playwright then starts the API (uvicorn) and a production build of the
 * frontend (vite preview).
 */
import path from 'node:path';
import { defineConfig, devices } from '@playwright/test';

import { API_PORT, API_URL, E2E_DIR, FRONTEND_DIR, REPO_ROOT, WEB_PORT, WEB_URL } from './e2e/env';

const python = process.env.E2E_PYTHON ?? 'python';
const jwksUrl = new URL(`file:///${path.join(E2E_DIR, 'jwks.json').replace(/\\/g, '/')}`).href;

export default defineConfig({
  testDir: './e2e/specs',
  outputDir: './reports/e2e-artifacts',
  fullyParallel: true,
  workers: 2,
  // No retries: a test that needs a retry to pass is reported as failing.
  retries: 0,
  forbidOnly: Boolean(process.env.CI),
  timeout: 30_000,
  expect: { timeout: 7_500 },
  reporter: [
    ['list'],
    ['junit', { outputFile: 'reports/e2e-junit.xml' }],
    ['html', { outputFolder: 'reports/e2e-html', open: 'never' }],
  ],
  use: {
    baseURL: WEB_URL,
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `${python} -m uvicorn app.main:app --host 127.0.0.1 --port ${API_PORT} --log-level warning`,
      cwd: REPO_ROOT,
      url: `${API_URL}/v1/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        APP_ENV: 'test',
        SUPABASE_JWKS_URL: jwksUrl,
        CORS_ORIGINS: `${WEB_URL},http://localhost:${WEB_PORT}`,
        DATABASE_URL: process.env.DATABASE_URL ?? '',
        MODEL_STORE_DIR: process.env.MODEL_STORE_DIR ?? path.join(E2E_DIR, 'models'),
        OMP_NUM_THREADS: '1',
      },
    },
    {
      command: `node ./node_modules/vite/bin/vite.js build && node ./node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port ${WEB_PORT} --strictPort`,
      cwd: FRONTEND_DIR,
      url: WEB_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
      env: {
        VITE_API_BASE_URL: API_URL,
        VITE_SUPABASE_URL: 'http://localhost:54321',
        VITE_SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_e2e',
      },
    },
  ],
});
