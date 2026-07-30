import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * Vite configuration for the frontend app.
 *
 * - React plugin for JSX/Fast Refresh.
 * - Dev server on port 3000 with host binding so it works inside containers.
 * - Vitest configured with jsdom + Testing Library setup file.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
  },
  preview: {
    host: true,
    port: 3000,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
});
