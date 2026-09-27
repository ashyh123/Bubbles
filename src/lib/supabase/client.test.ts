import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('browser supabase client', () => {
  it('reads public env vars as literal process.env members', () => {
    const source = readFileSync(new URL('./client.ts', import.meta.url), 'utf8');
    expect(source).toContain('process.env.NEXT_PUBLIC_SUPABASE_URL');
    expect(source).toContain('process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY');
    expect(source).not.toContain('readPublicSupabaseEnv');
  });
});
