import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * Vite configuration for the frontend app.
 *
 * - React plugin for JSX/Fast Refresh.
 * - Dev server on port 3000 with host binding so it works inside containers.
 * - Vitest configured with jsdom + Testing Library setup file.
 *
 * Note: This environment has previously shown intermittent esbuild runtime faults.
 * Set `VITE_SAFE_MODE=1` (or run `npm run dev:safe`) to start Vite with no plugins,
 * as an isolation/workaround mode.
 */
export default defineConfig({
  plugins: process.env.VITE_SAFE_MODE ? [] : [react()],
  optimizeDeps: process.env.VITE_NO_OPTIMIZE ? { disabled: true } : undefined,
  server: {
    host: true,
    port: 3000,
    // Allow Kavia preview hostnames (and any proxy host) to access the dev server.
    // This resolves: "Blocked request. This host is not allowed".
    allowedHosts: true,
  },
  preview: {
    host: true,
    port: 3000,
    // Mirror host allowance for `vite preview` as well.
    allowedHosts: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
});
