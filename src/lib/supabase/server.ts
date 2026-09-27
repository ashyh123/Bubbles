import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import 'server-only';
import type { Database } from '@/lib/db/database.types';
import { readPublicSupabaseEnv } from '@/lib/env';

export async function createClient() {
  const cookieStore = await cookies();
  const { url, anonKey } = readPublicSupabaseEnv();

  return createServerClient<Database>(url, anonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options);
          });
        } catch {
          // Server Components cannot set cookies. The proxy refreshes the session.
        }
      },
    },
  });
}
