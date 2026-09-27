import { describe, expect, it } from 'vitest';
import { SCORE_WEIGHTS } from '@/lib/feed';

describe('SCORE_WEIGHTS', () => {
  it('matches the PRD weighted sum and totals 1', () => {
    expect(SCORE_WEIGHTS).toEqual({
      W: 0.35,
      R: 0.2,
      G: 0.2,
      S: 0.1,
      P: 0.15,
    });
    const sum = Object.values(SCORE_WEIGHTS).reduce((total, weight) => total + weight, 0);
    expect(sum).toBeCloseTo(1, 10);
  });
});
