import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { CATEGORY_CRITERIA_EN, CATEGORY_KEYS } from '@/lib/db/enums';

const migration = readFileSync('supabase/migrations/20260927120000_init.sql', 'utf8');
const seed = readFileSync('supabase/seed.sql', 'utf8');

const EXPECTED_TABLES = [
  'api_tokens',
  'bubbles',
  'categories',
  'completions',
  'daily_feeds',
  'feed_items',
  'goal_nodes',
  'goal_trees',
  'habit_weights',
  'habits',
  'judge_results',
  'links',
  'profiles',
];

const CATEGORY_IDS: Record<(typeof CATEGORY_KEYS)[number], string> = {
  health: 'a0000000-0000-4000-8000-000000000001',
  learning: 'a0000000-0000-4000-8000-000000000002',
  creation: 'a0000000-0000-4000-8000-000000000003',
  career: 'a0000000-0000-4000-8000-000000000004',
  relationships: 'a0000000-0000-4000-8000-000000000005',
  other: 'a0000000-0000-4000-8000-000000000006',
};

describe('schema migration', () => {
  it('creates the PRD tables and enables RLS on each of them', () => {
    const created = [...migration.matchAll(/create table public\.(\w+)/gi)]
      .map((match) => match[1])
      .filter((name): name is string => Boolean(name));
    expect(created.sort()).toEqual([...EXPECTED_TABLES].sort());

    for (const table of EXPECTED_TABLES) {
      expect(migration).toMatch(
        new RegExp(`alter table public\\.${table} enable row level security`, 'i'),
      );
    }
  });

  it('uniquely indexes bubble idempotency keys and the embedding', () => {
    expect(migration).toMatch(
      /create unique index bubbles_user_idempotency_key_idx[\s\S]*where idempotency_key is not null/i,
    );
    expect(migration).toMatch(/embedding extensions\.vector\(1536\)/);
    expect(migration).toMatch(/using hnsw \(embedding extensions\.vector_cosine_ops\)/);
  });

  it('creates a profile with the milestone defaults on signup', () => {
    expect(migration).toMatch(/timezone text not null default 'Asia\/Shanghai'/);
    expect(migration).toMatch(
      /judge_confidence_min numeric\(3, 2\) not null default 0\.60/,
    );
    expect(migration).toMatch(/create trigger on_auth_user_created/);
  });
});

describe('seed data', () => {
  it('seeds six categories with the PRD English criteria', () => {
    for (const key of CATEGORY_KEYS) {
      expect(seed).toContain(`'${key}'`);
      expect(seed).toContain(CATEGORY_CRITERIA_EN[key]);
    }
  });

  it('seeds 5 to 8 preset habits for every category', () => {
    for (const key of CATEGORY_KEYS) {
      const id = CATEGORY_IDS[key];
      const mentions = seed.split(id).length - 1;
      const habitCount = mentions - 1;
      expect(habitCount, key).toBeGreaterThanOrEqual(5);
      expect(habitCount, key).toBeLessThanOrEqual(8);
    }
  });
});
