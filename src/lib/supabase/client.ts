import { createBrowserClient } from '@supabase/ssr';
import type { Database } from '@/lib/db/database.types';
import { readPublicSupabaseEnv } from '@/lib/env';

export function createClient() {
  const { url, anonKey } = readPublicSupabaseEnv();
  return createBrowserClient<Database>(url, anonKey);
}
