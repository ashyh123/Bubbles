import type {
  BreakdownError,
  BreakdownReason,
  BreakdownStatus,
  BubbleSource,
  CategoryKey,
  CategoryStatus,
  FeedAction,
  GoalMode,
  GoalNodeKind,
  GoalNodeStatus,
  HabitSize,
  HabitSource,
  HabitStatus,
  JudgeProviderName,
  LinkKind,
} from '@/lib/db/enums';

/**
 * Hand-written to match supabase/migrations/20260927120000_init.sql.
 * After `supabase start`, refresh with:
 * supabase gen types typescript --local --schema public > src/lib/db/database.types.ts
 */

export type Json =
  string | number | boolean | null | { [key: string]: Json | undefined } | Json[];

type TableDef<Row, Insert, Update> = {
  Row: Row;
  Insert: Insert;
  Update: Update;
  Relationships: [];
};

export type Database = {
  public: {
    Tables: {
      profiles: TableDef<
        {
          user_id: string;
          timezone: string;
          judge_confidence_min: number;
          prefs: Json;
          onboarded_at: string | null;
          feed_max_items: number;
          created_at: string;
          updated_at: string;
        },
        {
          user_id: string;
          timezone?: string;
          judge_confidence_min?: number;
          prefs?: Json;
          onboarded_at?: string | null;
          feed_max_items?: number;
          created_at?: string;
          updated_at?: string;
        },
        {
          user_id?: string;
          timezone?: string;
          judge_confidence_min?: number;
          prefs?: Json;
          onboarded_at?: string | null;
          feed_max_items?: number;
          created_at?: string;
          updated_at?: string;
        }
      >;
      categories: TableDef<
        {
          id: string;
          key: CategoryKey;
          name_zh: string;
          description_en: string;
          color: string;
          is_preset: boolean;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          key: CategoryKey;
          name_zh: string;
          description_en: string;
          color: string;
          is_preset?: boolean;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          key?: CategoryKey;
          name_zh?: string;
          description_en?: string;
          color?: string;
          is_preset?: boolean;
          created_at?: string;
          updated_at?: string;
        }
      >;
      bubbles: TableDef<
        {
          id: string;
          user_id: string;
          content: string;
          category_id: string | null;
          category_status: CategoryStatus;
          embedding: string | null;
          embedding_model: string | null;
          source: BubbleSource;
          idempotency_key: string | null;
          breakdown_status: BreakdownStatus;
          breakdown_reason: BreakdownReason | null;
          breakdown_error: BreakdownError | null;
          breakdown_generation_count: number;
          manual_retry_count: number;
          manual_retry_on: string | null;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          user_id: string;
          content: string;
          category_id?: string | null;
          category_status?: CategoryStatus;
          embedding?: string | null;
          embedding_model?: string | null;
          source?: BubbleSource;
          idempotency_key?: string | null;
          breakdown_status?: BreakdownStatus;
          breakdown_reason?: BreakdownReason | null;
          breakdown_error?: BreakdownError | null;
          breakdown_generation_count?: number;
          manual_retry_count?: number;
          manual_retry_on?: string | null;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          user_id?: string;
          content?: string;
          category_id?: string | null;
          category_status?: CategoryStatus;
          embedding?: string | null;
          embedding_model?: string | null;
          source?: BubbleSource;
          idempotency_key?: string | null;
          breakdown_status?: BreakdownStatus;
          breakdown_reason?: BreakdownReason | null;
          breakdown_error?: BreakdownError | null;
          breakdown_generation_count?: number;
          manual_retry_count?: number;
          manual_retry_on?: string | null;
          created_at?: string;
          updated_at?: string;
        }
      >;
      judge_results: TableDef<
        {
          id: string;
          user_id: string;
          bubble_id: string;
          provider: JudgeProviderName;
          model: string;
          question_key: string;
          answer: string;
          probabilities: Json;
          confidence: number | null;
          latency_ms: number;
          cost_usd: number | null;
          final: boolean;
          overridden_by_user: boolean;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          user_id: string;
          bubble_id: string;
          provider: JudgeProviderName;
          model: string;
          question_key: string;
          answer: string;
          probabilities?: Json;
          confidence?: number | null;
          latency_ms: number;
          cost_usd?: number | null;
          final?: boolean;
          overridden_by_user?: boolean;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          user_id?: string;
          bubble_id?: string;
          provider?: JudgeProviderName;
          model?: string;
          question_key?: string;
          answer?: string;
          probabilities?: Json;
          confidence?: number | null;
          latency_ms?: number;
          cost_usd?: number | null;
          final?: boolean;
          overridden_by_user?: boolean;
          created_at?: string;
          updated_at?: string;
        }
      >;
      links: TableDef<
        {
          id: string;
          user_id: string;
          bubble_a: string;
          bubble_b: string;
          similarity: number;
          kind: LinkKind;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          user_id: string;
          bubble_a: string;
          bubble_b: string;
          similarity: number;
          kind: LinkKind;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          user_id?: string;
          bubble_a?: string;
          bubble_b?: string;
          similarity?: number;
          kind?: LinkKind;
          created_at?: string;
          updated_at?: string;
        }
      >;
      habits: TableDef<
        {
          id: string;
          user_id: string | null;
          category_id: string;
          title: string;
          size: HabitSize;
          est_minutes: number;
          interval_days: number;
          source: HabitSource;
          template_id: string | null;
          goal_node_id: string | null;
          status: HabitStatus;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          user_id?: string | null;
          category_id: string;
          title: string;
          size: HabitSize;
          est_minutes: number;
          interval_days: number;
          source: HabitSource;
          template_id?: string | null;
          goal_node_id?: string | null;
          status?: HabitStatus;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          user_id?: string | null;
          category_id?: string;
          title?: string;
          size?: HabitSize;
          est_minutes?: number;
          interval_days?: number;
          source?: HabitSource;
          template_id?: string | null;
          goal_node_id?: string | null;
          status?: HabitStatus;
          created_at?: string;
          updated_at?: string;
        }
      >;
      habit_weights: TableDef<
        {
          user_id: string;
          habit_id: string;
          weight: number;
          boost: number;
          boost_until: string | null;
          last_done_at: string | null;
          last_decay_at: string | null;
          created_at: string;
          updated_at: string;
        },
        {
          user_id: string;
          habit_id: string;
          weight?: number;
          boost?: number;
          boost_until?: string | null;
          last_done_at?: string | null;
          last_decay_at?: string | null;
          created_at?: string;
          updated_at?: string;
        },
        {
          user_id?: string;
          habit_id?: string;
          weight?: number;
          boost?: number;
          boost_until?: string | null;
          last_done_at?: string | null;
          last_decay_at?: string | null;
          created_at?: string;
          updated_at?: string;
        }
      >;
      completions: TableDef<
        {
          id: string;
          user_id: string;
          habit_id: string | null;
          goal_node_id: string | null;
          done_at: string;
          feed_item_id: string | null;
          note: string | null;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          user_id: string;
          habit_id?: string | null;
          goal_node_id?: string | null;
          done_at?: string;
          feed_item_id?: string | null;
          note?: string | null;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          user_id?: string;
          habit_id?: string | null;
          goal_node_id?: string | null;
          done_at?: string;
          feed_item_id?: string | null;
          note?: string | null;
          created_at?: string;
          updated_at?: string;
        }
      >;
      daily_feeds: TableDef<
        {
          id: string;
          user_id: string;
          date: string;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          user_id: string;
          date: string;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          user_id?: string;
          date?: string;
          created_at?: string;
          updated_at?: string;
        }
      >;
      feed_items: TableDef<
        {
          id: string;
          feed_id: string;
          user_id: string;
          habit_id: string | null;
          goal_node_id: string | null;
          rank: number;
          score: number;
          factors: Json;
          reason_text: string | null;
          action: FeedAction;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          feed_id: string;
          user_id: string;
          habit_id?: string | null;
          goal_node_id?: string | null;
          rank: number;
          score: number;
          factors?: Json;
          reason_text?: string | null;
          action?: FeedAction;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          feed_id?: string;
          user_id?: string;
          habit_id?: string | null;
          goal_node_id?: string | null;
          rank?: number;
          score?: number;
          factors?: Json;
          reason_text?: string | null;
          action?: FeedAction;
          created_at?: string;
          updated_at?: string;
        }
      >;
      goal_trees: TableDef<
        {
          id: string;
          user_id: string;
          mode: GoalMode;
          constraints: Json;
          model: string | null;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          user_id: string;
          mode: GoalMode;
          constraints?: Json;
          model?: string | null;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          user_id?: string;
          mode?: GoalMode;
          constraints?: Json;
          model?: string | null;
          created_at?: string;
          updated_at?: string;
        }
      >;
      goal_tree_bubbles: TableDef<
        {
          tree_id: string;
          bubble_id: string;
          user_id: string;
          created_at: string;
          updated_at: string;
        },
        {
          tree_id: string;
          bubble_id: string;
          user_id: string;
          created_at?: string;
          updated_at?: string;
        },
        {
          tree_id?: string;
          bubble_id?: string;
          user_id?: string;
          created_at?: string;
          updated_at?: string;
        }
      >;
      goal_nodes: TableDef<
        {
          id: string;
          tree_id: string;
          user_id: string;
          parent_id: string | null;
          kind: GoalNodeKind;
          title: string;
          est_minutes: number | null;
          repeatable: boolean;
          interval_days: number | null;
          status: GoalNodeStatus;
          habit_id: string | null;
          done_definition: string | null;
          accepted_at: string | null;
          pinned: boolean;
          position: number;
          category_id: string | null;
          specificity_score: number | null;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          tree_id: string;
          user_id: string;
          parent_id?: string | null;
          kind: GoalNodeKind;
          title: string;
          est_minutes?: number | null;
          repeatable?: boolean;
          interval_days?: number | null;
          status?: GoalNodeStatus;
          habit_id?: string | null;
          done_definition?: string | null;
          accepted_at?: string | null;
          pinned?: boolean;
          position?: number;
          category_id?: string | null;
          specificity_score?: number | null;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          tree_id?: string;
          user_id?: string;
          parent_id?: string | null;
          kind?: GoalNodeKind;
          title?: string;
          est_minutes?: number | null;
          repeatable?: boolean;
          interval_days?: number | null;
          status?: GoalNodeStatus;
          habit_id?: string | null;
          done_definition?: string | null;
          accepted_at?: string | null;
          pinned?: boolean;
          position?: number;
          category_id?: string | null;
          specificity_score?: number | null;
          created_at?: string;
          updated_at?: string;
        }
      >;
      api_tokens: TableDef<
        {
          id: string;
          user_id: string;
          token_hash: string;
          scopes: string[];
          last_used_at: string | null;
          revoked_at: string | null;
          created_at: string;
          updated_at: string;
        },
        {
          id?: string;
          user_id: string;
          token_hash: string;
          scopes?: string[];
          last_used_at?: string | null;
          revoked_at?: string | null;
          created_at?: string;
          updated_at?: string;
        },
        {
          id?: string;
          user_id?: string;
          token_hash?: string;
          scopes?: string[];
          last_used_at?: string | null;
          revoked_at?: string | null;
          created_at?: string;
          updated_at?: string;
        }
      >;
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
  };
};

export type Tables<Name extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][Name]['Row'];
