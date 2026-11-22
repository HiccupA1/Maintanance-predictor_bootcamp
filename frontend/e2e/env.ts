import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const FRONTEND_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const REPO_ROOT = path.resolve(FRONTEND_DIR, '..');
export const E2E_DIR = process.env.E2E_DIR ?? path.join(REPO_ROOT, 'reports', 'e2e-env');
export const API_PORT = Number(process.env.E2E_API_PORT ?? 8000);
export const WEB_PORT = Number(process.env.E2E_WEB_PORT ?? 4173);
export const API_URL = `http://127.0.0.1:${API_PORT}`;
export const WEB_URL = `http://127.0.0.1:${WEB_PORT}`;
