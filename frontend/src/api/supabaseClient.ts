import { createClient, type SupabaseClient } from '@supabase/supabase-js';

import { SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL } from '../config/env';

let cachedClient: SupabaseClient | null = null;

// PUBLIC_INTERFACE
export class SupabaseConfigError extends Error {
  /**
   * Error thrown when Supabase is not configured correctly for the frontend.
   * This is intended to be rendered directly in the UI with actionable steps.
   */
  constructor(message: string) {
    super(message);
    this.name = 'SupabaseConfigError';
  }
}

function validateSupabaseUrl(value: string): void {
  // Basic sanity checks to prevent "Failed to fetch" due to malformed URL/scheme.
  // We intentionally keep this lightweight and non-blocking for local setups,
  // but we do require an explicit protocol.
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new SupabaseConfigError(
      `Invalid VITE_SUPABASE_URL: "${value}". Expected a fully-qualified URL like "https://<project-ref>.supabase.co".`,
    );
  }
  if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') {
    throw new SupabaseConfigError(
      `Invalid VITE_SUPABASE_URL protocol: "${parsed.protocol}". Expected "https:" (recommended) or "http:".`,
    );
  }
}

// PUBLIC_INTERFACE
export function getSupabaseClient(): SupabaseClient {
  /**
   * Return a singleton Supabase client.
   *
   * This throws a clear error when required environment variables are missing,
   * so the UI can surface an actionable message in misconfigured environments.
   *
   * @throws {SupabaseConfigError} When `VITE_SUPABASE_URL` or `VITE_SUPABASE_PUBLISHABLE_KEY` are missing/invalid.
   */
  if (cachedClient) return cachedClient;

  if (!SUPABASE_URL || !SUPABASE_PUBLISHABLE_KEY) {
    throw new SupabaseConfigError(
      [
        'Supabase is not configured for this frontend build.',
        '',
        'Set these Vite environment variables:',
        '- VITE_SUPABASE_URL (e.g. https://<project-ref>.supabase.co)',
        '- VITE_SUPABASE_PUBLISHABLE_KEY (sb_publishable_...)',
        '',
        'Tip: copy `frontend/.env.example` to `frontend/.env.local` for local development.',
      ].join('\n'),
    );
  }

  validateSupabaseUrl(SUPABASE_URL);

  cachedClient = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
    auth: {
      // Keep default browser session persistence.
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });

  return cachedClient;
}
