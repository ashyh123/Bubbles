export const CATEGORY_KEYS = [
  'health',
  'learning',
  'creation',
  'career',
  'relationships',
  'other',
] as const;

export type CategoryKey = (typeof CATEGORY_KEYS)[number];

export const CATEGORY_CRITERIA_EN: Record<CategoryKey, string> = {
  health: 'Body, sleep, diet, exercise, mental health',
  learning: 'Studying, reading, languages, skills',
  creation: 'Writing, art, side projects, making things',
  career: 'Job, business, money, professional growth',
  relationships: 'Family, friends, partner, social',
  other: 'None of the above clearly fits',
};

export const BUBBLE_SOURCES = ['web', 'api', 'mcp', 'shortcut', 'assistant', 'expand'] as const;
export type BubbleSource = (typeof BUBBLE_SOURCES)[number];

export const CATEGORY_STATUSES = ['unjudged', 'auto', 'pending', 'confirmed'] as const;
export type CategoryStatus = (typeof CATEGORY_STATUSES)[number];

export const BREAKDOWN_STATUSES = [
  'pending',
  'small',
  'generating',
  'ready',
  'picked',
  'failed',
  'not_applicable',
] as const;
export type BreakdownStatus = (typeof BREAKDOWN_STATUSES)[number];

export const BREAKDOWN_REASONS = ['reflection', 'habit_like'] as const;
export type BreakdownReason = (typeof BREAKDOWN_REASONS)[number];

export const BREAKDOWN_ERRORS = ['model_error', 'rate_limited', 'timeout'] as const;
export type BreakdownError = (typeof BREAKDOWN_ERRORS)[number];

export const JUDGE_PROVIDERS = ['llm', 'jev'] as const;
export type JudgeProviderName = (typeof JUDGE_PROVIDERS)[number];

export const LINK_KINDS = ['auto', 'confirmed', 'dismissed'] as const;
export type LinkKind = (typeof LINK_KINDS)[number];

export const HABIT_SIZES = ['xs', 's', 'm', 'l'] as const;
export type HabitSize = (typeof HABIT_SIZES)[number];

export const HABIT_SOURCES = ['preset', 'user', 'expand'] as const;
export type HabitSource = (typeof HABIT_SOURCES)[number];

export const HABIT_STATUSES = ['active', 'paused', 'archived'] as const;
export type HabitStatus = (typeof HABIT_STATUSES)[number];

export const FEED_ACTIONS = ['shown', 'done', 'skipped', 'swapped'] as const;
export type FeedAction = (typeof FEED_ACTIONS)[number];

export const GOAL_MODES = ['concrete', 'bigger', 'micro'] as const;
export type GoalMode = (typeof GOAL_MODES)[number];

export const GOAL_NODE_KINDS = ['goal', 'milestone', 'task', 'action'] as const;
export type GoalNodeKind = (typeof GOAL_NODE_KINDS)[number];

export const GOAL_NODE_STATUSES = ['suggested', 'accepted', 'done', 'dismissed'] as const;
export type GoalNodeStatus = (typeof GOAL_NODE_STATUSES)[number];
