import { describe, expect, it } from 'vitest';
import { readJudgeProvider, readPublicSupabaseEnv, SupabaseConfigError } from '@/lib/env';

describe('readPublicSupabaseEnv', () => {
  it('returns the public url and anon key', () => {
    expect(
      readPublicSupabaseEnv({
        NEXT_PUBLIC_SUPABASE_URL: 'http://127.0.0.1:54321',
        NEXT_PUBLIC_SUPABASE_ANON_KEY: 'anon',
      }),
    ).toEqual({
      url: 'http://127.0.0.1:54321',
      anonKey: 'anon',
    });
  });

  it('fails closed when either value is missing', () => {
    expect(() => readPublicSupabaseEnv({})).toThrow(SupabaseConfigError);
  });
});

describe('readJudgeProvider', () => {
  it('defaults to llm', () => {
    expect(readJudgeProvider({})).toBe('llm');
  });

  it('accepts jev', () => {
    expect(readJudgeProvider({ JUDGE_PROVIDER: 'jev' })).toBe('jev');
  });

  it('rejects unknown providers', () => {
    expect(() => readJudgeProvider({ JUDGE_PROVIDER: 'other' })).toThrow(/llm or jev/);
  });
});
