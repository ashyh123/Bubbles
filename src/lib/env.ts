import { JUDGE_PROVIDERS, type JudgeProviderName } from '@/lib/db/enums';

export type EnvSource = {
  [key: string]: string | undefined;
};

export class SupabaseConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SupabaseConfigError';
  }
}

export function readPublicSupabaseEnv(env: EnvSource = process.env): {
  url: string;
  anonKey: string;
} {
  const url = env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    throw new SupabaseConfigError(
      'Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY',
    );
  }
  return { url, anonKey };
}

export function readServiceRoleKey(env: EnvSource = process.env): string {
  const key = env.SUPABASE_SERVICE_ROLE_KEY;
  if (!key) {
    throw new SupabaseConfigError('Missing SUPABASE_SERVICE_ROLE_KEY');
  }
  return key;
}

export function readJudgeProvider(env: EnvSource = process.env): JudgeProviderName {
  const value = env.JUDGE_PROVIDER ?? 'llm';
  if (!JUDGE_PROVIDERS.includes(value as JudgeProviderName)) {
    throw new Error('JUDGE_PROVIDER must be llm or jev');
  }
  return value as JudgeProviderName;
}
