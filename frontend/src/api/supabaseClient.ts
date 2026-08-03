import { createClient, type SupabaseClient } from '@supabase/supabase-js';

import { SUPABASE_ANON_KEY, SUPABASE_URL } from '../config/env';

let cachedClient: SupabaseClient | null = null;

// PUBLIC_INTERFACE
export function getSupabaseClient(): SupabaseClient {
  /**
   * Return a singleton Supabase client.
   *
   * This throws a clear error when required environment variables are missing,
   * so the UI can surface an actionable message in misconfigured environments.
   *
   * @throws {Error} When `VITE_SUPABASE_URL` or `VITE_SUPABASE_ANON_KEY` are missing.
   */
  if (cachedClient) return cachedClient;

  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error(
      'Supabase is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in the frontend environment.',
    );
  }

  cachedClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
      // Keep default browser session persistence.
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });

  return cachedClient;
}
