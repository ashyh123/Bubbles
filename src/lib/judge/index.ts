import type { JudgeProviderName } from '@/lib/db/enums';

/**
 * Pluggable classifier. LLMJudge and JevJudge land in a later milestone.
 * JUDGE_PROVIDER selects the implementation; callers should depend on this type only.
 */
export interface JudgeChoice {
  answer: string;
  probabilities: Record<string, number>;
  confidence: number;
  provider: JudgeProviderName;
  model: string;
  latencyMs: number;
}

export interface JudgeYesNo {
  p: number;
  provider: JudgeProviderName;
  model: string;
  latencyMs: number;
}

export interface JudgeScore {
  value: number;
  confidence: number;
  provider: JudgeProviderName;
  model: string;
  latencyMs: number;
}

export interface Judge {
  choose(input: {
    text: string;
    context?: object;
    question: string;
    options: Record<string, string>;
  }): Promise<JudgeChoice>;
  yesNo(input: { text: string; context?: object; question: string }): Promise<JudgeYesNo>;
  score(input: {
    text: string;
    context?: object;
    question: string;
    criteria: string[];
  }): Promise<JudgeScore>;
}
