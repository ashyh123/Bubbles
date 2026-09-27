export type { HabitSize, HabitSource, HabitStatus } from '@/lib/db/enums';

/** Weight updates (complete, skip, decay, boost) are implemented in a later milestone. */
export const INITIAL_HABIT_WEIGHT = 3;
export const HABIT_WEIGHT_MIN = 0.5;
export const HABIT_WEIGHT_MAX = 10;
