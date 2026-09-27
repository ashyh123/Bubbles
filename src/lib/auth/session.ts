import 'server-only';
import { SupabaseConfigError } from '@/lib/env';
import { createClient } from '@/lib/supabase/server';

export type CurrentUser = {
  id: string;
  email: string | null;
};

export async function getCurrentUser(): Promise<{
  user: CurrentUser | null;
  configMissing: boolean;
}> {
  try {
    const supabase = await createClient();
    const { data, error } = await supabase.auth.getUser();
    if (error || !data.user) {
      return { user: null, configMissing: false };
    }
    return {
      user: { id: data.user.id, email: data.user.email ?? null },
      configMissing: false,
    };
  } catch (error) {
    if (error instanceof SupabaseConfigError) {
      return { user: null, configMissing: true };
    }
    return { user: null, configMissing: false };
  }
}
