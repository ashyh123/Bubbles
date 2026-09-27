/** Normalized factors from PRD 4.4. The scorer itself is a later milestone. */
export interface ScoreFactors {
  W: number;
  R: number;
  G: number;
  S: number;
  P: number;
}

export const SCORE_WEIGHTS = {
  W: 0.35,
  R: 0.2,
  G: 0.2,
  S: 0.1,
  P: 0.15,
} as const satisfies Record<keyof ScoreFactors, number>;
