import { createBrowserClient } from '@supabase/ssr';
import type { Database } from '@/lib/db/database.types';
import { SupabaseConfigError } from '@/lib/env';

export function createClient() {
  // Literal member access. Next inlines these into the browser bundle.
  // Reading them through a helper or a variable does not.
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    throw new SupabaseConfigError(
      'Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY',
    );
  }
  return createBrowserClient<Database>(url, anonKey);
}
