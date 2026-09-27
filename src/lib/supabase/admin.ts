import { createClient } from '@supabase/supabase-js';
import 'server-only';
import type { Database } from '@/lib/db/database.types';
import { readPublicSupabaseEnv, readServiceRoleKey } from '@/lib/env';

/** Service role bypasses RLS. Never import this from a Client Component. */
export function createAdminClient() {
  const { url } = readPublicSupabaseEnv();
  return createClient<Database>(url, readServiceRoleKey(), {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });
}
