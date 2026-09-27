-- Bubble schema. Edit this file in place until it has been applied to a shared database.
-- All public tables enable RLS. User-owned rows are filtered by user_id.
-- Idea text must never be written to application logs.

create extension if not exists vector with schema extensions;

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

revoke all on function public.set_updated_at() from public;
grant execute on function public.set_updated_at() to authenticated, service_role;

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (user_id)
  values (new.id)
  on conflict (user_id) do nothing;
  return new;
end;
$$;

revoke all on function public.handle_new_user() from public;
grant execute on function public.handle_new_user() to supabase_auth_admin, service_role;

create or replace function public.enforce_habit_template()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.template_id is not null
    and not exists (
      select 1
      from public.habits template
      where template.id = new.template_id
        and template.user_id is null
        and template.source = 'preset'
    ) then
    raise exception 'template_id must reference a preset template'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke all on function public.enforce_habit_template() from public;
grant execute on function public.enforce_habit_template() to authenticated, service_role;

create or replace function public.enforce_goal_node_same_tree()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.parent_id is not null
    and not exists (
      select 1
      from public.goal_nodes parent
      where parent.id = new.parent_id
        and parent.tree_id = new.tree_id
        and parent.user_id = new.user_id
    ) then
    raise exception 'goal node parent must belong to the same tree'
      using errcode = '23514';
  end if;

  if exists (
    select 1
    from public.goal_nodes child
    where child.parent_id = new.id
      and child.tree_id is distinct from new.tree_id
  ) then
    raise exception 'goal node children must stay in the same tree'
      using errcode = '23514';
  end if;

  return new;
end;
$$;

revoke all on function public.enforce_goal_node_same_tree() from public;
grant execute on function public.enforce_goal_node_same_tree() to authenticated, service_role;

-- ---------------------------------------------------------------------------
-- profiles
-- ---------------------------------------------------------------------------

create table public.profiles (
  user_id uuid primary key references auth.users (id) on delete cascade,
  timezone text not null default 'Asia/Shanghai',
  judge_confidence_min numeric(3, 2) not null default 0.60,
  prefs jsonb not null default '{}'::jsonb,
  onboarded_at timestamptz,
  feed_max_items smallint not null default 5,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint profiles_confidence_check check (
    judge_confidence_min >= 0 and judge_confidence_min <= 1
  ),
  constraint profiles_feed_max_items_check check (feed_max_items between 3 and 5)
);

comment on table public.profiles is
  'Per-user preferences. prefs holds the nightly preference portrait.';

-- ---------------------------------------------------------------------------
-- categories (global presets, no user_id)
-- ---------------------------------------------------------------------------

create table public.categories (
  id uuid primary key default gen_random_uuid(),
  key text not null,
  name_zh text not null,
  description_en text not null,
  color text not null,
  is_preset boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint categories_key_unique unique (key),
  constraint categories_key_check check (
    key in ('health', 'learning', 'creation', 'career', 'relationships', 'other')
  ),
  constraint categories_color_check check (color ~ '^#[0-9A-Fa-f]{6}$')
);

comment on table public.categories is
  'System life-area categories. description_en is the Judge option text.';

-- ---------------------------------------------------------------------------
-- bubbles
-- ---------------------------------------------------------------------------

create table public.bubbles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  content text not null,
  category_id uuid references public.categories (id) on delete restrict,
  category_status text not null default 'unjudged',
  embedding extensions.vector(1536),
  embedding_model text,
  source text not null default 'web',
  idempotency_key text,
  breakdown_status text not null default 'pending',
  breakdown_reason text,
  breakdown_error text,
  breakdown_generation_count integer not null default 0,
  manual_retry_count integer not null default 0,
  manual_retry_on date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint bubbles_id_user_unique unique (id, user_id),
  constraint bubbles_content_check check (char_length(btrim(content)) between 1 and 8000),
  constraint bubbles_category_status_check check (
    category_status in ('unjudged', 'auto', 'pending', 'confirmed')
  ),
  constraint bubbles_source_check check (
    source in ('web', 'api', 'mcp', 'shortcut', 'assistant', 'expand')
  ),
  constraint bubbles_idempotency_key_length_check check (
    idempotency_key is null or char_length(idempotency_key) between 1 and 200
  ),
  constraint bubbles_breakdown_status_check check (
    breakdown_status in (
      'pending',
      'small',
      'generating',
      'ready',
      'picked',
      'failed',
      'not_applicable'
    )
  ),
  constraint bubbles_breakdown_reason_check check (
    (
      breakdown_status = 'not_applicable'
      and breakdown_reason in ('reflection', 'habit_like')
    )
    or (breakdown_status <> 'not_applicable' and breakdown_reason is null)
  ),
  constraint bubbles_breakdown_error_check check (
    breakdown_error is null
    or (
      breakdown_status = 'failed'
      and breakdown_error in ('model_error', 'rate_limited', 'timeout')
    )
  ),
  constraint bubbles_breakdown_generation_count_check check (breakdown_generation_count >= 0),
  constraint bubbles_manual_retry_check check (
    manual_retry_count between 0 and 3
    and (manual_retry_count = 0 or manual_retry_on is not null)
  )
);

comment on column public.bubbles.content is
  'Private idea text. Application logs must not print this value.';
comment on column public.bubbles.category_status is
  'unjudged until a judge runs. pending means low confidence and waiting for the user.';
comment on column public.bubbles.manual_retry_count is
  'Manual breakdown retries for manual_retry_on. The app resets the counter when the local date changes. Cap is 3 per idea per day.';

create unique index bubbles_user_idempotency_key_idx
  on public.bubbles (user_id, idempotency_key)
  where idempotency_key is not null;

create index bubbles_user_created_at_idx
  on public.bubbles (user_id, created_at desc);

create index bubbles_category_id_idx
  on public.bubbles (category_id);

create index bubbles_user_pending_idx
  on public.bubbles (user_id)
  where category_status = 'pending';

create index bubbles_embedding_hnsw_idx
  on public.bubbles
  using hnsw (embedding extensions.vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- judge_results
-- Composite FK keeps a result from pointing at another user's bubble.
-- confidence is null for yes/no questions, which only have a probability.
-- ---------------------------------------------------------------------------

create table public.judge_results (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  bubble_id uuid not null,
  provider text not null,
  model text not null,
  question_key text not null,
  answer text not null,
  probabilities jsonb not null default '{}'::jsonb,
  confidence numeric(4, 3),
  latency_ms integer not null,
  cost_usd numeric(12, 6),
  final boolean not null default false,
  overridden_by_user boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint judge_results_id_user_unique unique (id, user_id),
  constraint judge_results_bubble_user_fkey
    foreign key (bubble_id, user_id) references public.bubbles (id, user_id) on delete cascade,
  constraint judge_results_provider_check check (provider in ('llm', 'jev')),
  constraint judge_results_confidence_check check (
    confidence is null or (confidence >= 0 and confidence <= 1)
  ),
  constraint judge_results_latency_check check (latency_ms >= 0)
);

create index judge_results_bubble_id_idx
  on public.judge_results (bubble_id, created_at desc);

create index judge_results_user_id_idx
  on public.judge_results (user_id);

-- ---------------------------------------------------------------------------
-- links
-- ---------------------------------------------------------------------------

create table public.links (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  bubble_a uuid not null,
  bubble_b uuid not null,
  similarity double precision not null,
  kind text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint links_id_user_unique unique (id, user_id),
  constraint links_bubble_a_user_fkey
    foreign key (bubble_a, user_id) references public.bubbles (id, user_id) on delete cascade,
  constraint links_bubble_b_user_fkey
    foreign key (bubble_b, user_id) references public.bubbles (id, user_id) on delete cascade,
  constraint links_distinct_bubbles_check check (bubble_a <> bubble_b),
  constraint links_similarity_check check (similarity >= -1 and similarity <= 1),
  constraint links_kind_check check (kind in ('auto', 'confirmed', 'dismissed'))
);

create unique index links_unordered_pair_uidx
  on public.links (user_id, least(bubble_a, bubble_b), greatest(bubble_a, bubble_b));

create index links_bubble_a_idx on public.links (bubble_a);
create index links_bubble_b_idx on public.links (bubble_b);
create index links_user_id_idx on public.links (user_id);

-- ---------------------------------------------------------------------------
-- habits
-- user_id null + source preset: shared template, read-only.
-- user_id set + source preset + template_id: the user's copy, editable.
-- ---------------------------------------------------------------------------

create table public.habits (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users (id) on delete cascade,
  category_id uuid not null references public.categories (id) on delete restrict,
  title text not null,
  size text not null,
  est_minutes integer not null,
  interval_days integer not null,
  source text not null,
  template_id uuid,
  goal_node_id uuid,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint habits_id_user_unique unique (id, user_id),
  constraint habits_template_id_fkey
    foreign key (template_id) references public.habits (id) on delete restrict,
  constraint habits_template_not_self_check check (template_id is null or template_id <> id),
  constraint habits_title_check check (char_length(btrim(title)) between 1 and 200),
  constraint habits_size_check check (size in ('xs', 's', 'm', 'l')),
  constraint habits_interval_check check (interval_days > 0),
  constraint habits_source_check check (source in ('preset', 'user', 'expand')),
  constraint habits_status_check check (status in ('active', 'paused', 'archived')),
  constraint habits_preset_owner_check check (
    (user_id is null and source = 'preset' and template_id is null)
    or (user_id is not null and source = 'preset' and template_id is not null)
    or (user_id is not null and source in ('user', 'expand'))
  ),
  constraint habits_size_minutes_check check (
    (size = 'xs' and est_minutes between 1 and 5)
    or (size = 's' and est_minutes between 6 and 30)
    or (size = 'm' and est_minutes between 31 and 120)
    or (size = 'l' and est_minutes > 120)
  )
);

create trigger habits_enforce_template
  before insert or update on public.habits
  for each row
  execute function public.enforce_habit_template();

create index habits_user_id_idx on public.habits (user_id);
create index habits_category_id_idx on public.habits (category_id);
create index habits_template_id_idx on public.habits (template_id);

-- ---------------------------------------------------------------------------
-- habit_weights
-- weight and boost are double precision so repeated x0.97 decay does not stick.
-- The composite foreign key references habits (id, user_id). A shared template
-- has a null user_id, so it is not a valid target. Weights belong on the user's
-- copy. An EXISTS policy that also allowed presets would undo that.
-- ---------------------------------------------------------------------------

create table public.habit_weights (
  user_id uuid not null references auth.users (id) on delete cascade,
  habit_id uuid not null,
  weight double precision not null default 3.0,
  boost double precision not null default 0,
  boost_until timestamptz,
  last_done_at timestamptz,
  last_decay_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, habit_id),
  constraint habit_weights_habit_user_fkey
    foreign key (habit_id, user_id) references public.habits (id, user_id) on delete restrict,
  constraint habit_weights_weight_check check (weight >= 0.5 and weight <= 10),
  constraint habit_weights_boost_check check (boost >= 0)
);

create index habit_weights_habit_id_idx on public.habit_weights (habit_id);

-- ---------------------------------------------------------------------------
-- daily_feeds / feed_items
-- ---------------------------------------------------------------------------

create table public.daily_feeds (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  date date not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint daily_feeds_id_user_unique unique (id, user_id),
  constraint daily_feeds_user_date_unique unique (user_id, date)
);

create index daily_feeds_user_id_idx on public.daily_feeds (user_id, date desc);

create table public.feed_items (
  id uuid primary key default gen_random_uuid(),
  feed_id uuid not null,
  user_id uuid not null references auth.users (id) on delete cascade,
  habit_id uuid,
  goal_node_id uuid,
  rank integer not null,
  score double precision not null,
  factors jsonb not null default '{}'::jsonb,
  reason_text text,
  action text not null default 'shown',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint feed_items_id_user_unique unique (id, user_id),
  constraint feed_items_feed_user_fkey
    foreign key (feed_id, user_id) references public.daily_feeds (id, user_id) on delete cascade,
  constraint feed_items_habit_user_fkey
    foreign key (habit_id, user_id) references public.habits (id, user_id) on delete restrict,
  constraint feed_items_feed_rank_unique unique (feed_id, rank),
  constraint feed_items_rank_check check (rank > 0),
  constraint feed_items_action_check check (
    action in ('shown', 'done', 'skipped', 'swapped')
  ),
  constraint feed_items_target_check check (num_nonnulls(habit_id, goal_node_id) = 1)
);

create index feed_items_feed_id_idx on public.feed_items (feed_id, rank);
create index feed_items_user_id_idx on public.feed_items (user_id);
create index feed_items_habit_id_idx on public.feed_items (habit_id);

-- ---------------------------------------------------------------------------
-- goal_trees / goal_tree_bubbles / goal_nodes
-- ---------------------------------------------------------------------------

create table public.goal_trees (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  mode text not null,
  constraints jsonb not null default '{}'::jsonb,
  model text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint goal_trees_id_user_unique unique (id, user_id),
  constraint goal_trees_mode_check check (mode in ('concrete', 'bigger', 'micro'))
);

create index goal_trees_user_id_idx on public.goal_trees (user_id, created_at desc);

create table public.goal_tree_bubbles (
  tree_id uuid not null,
  bubble_id uuid not null,
  user_id uuid not null references auth.users (id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (tree_id, bubble_id),
  constraint goal_tree_bubbles_tree_user_fkey
    foreign key (tree_id, user_id) references public.goal_trees (id, user_id) on delete cascade,
  constraint goal_tree_bubbles_bubble_user_fkey
    foreign key (bubble_id, user_id) references public.bubbles (id, user_id) on delete cascade
);

create index goal_tree_bubbles_bubble_id_idx on public.goal_tree_bubbles (bubble_id);
create index goal_tree_bubbles_user_id_idx on public.goal_tree_bubbles (user_id);

create table public.goal_nodes (
  id uuid primary key default gen_random_uuid(),
  tree_id uuid not null,
  user_id uuid not null references auth.users (id) on delete cascade,
  parent_id uuid references public.goal_nodes (id) on delete cascade,
  kind text not null,
  title text not null,
  est_minutes integer,
  repeatable boolean not null default false,
  interval_days integer,
  status text not null default 'suggested',
  habit_id uuid,
  done_definition text,
  accepted_at timestamptz,
  pinned boolean not null default false,
  position integer not null default 0,
  category_id uuid references public.categories (id) on delete restrict,
  specificity_score double precision,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint goal_nodes_id_user_unique unique (id, user_id),
  constraint goal_nodes_tree_user_fkey
    foreign key (tree_id, user_id) references public.goal_trees (id, user_id) on delete cascade,
  constraint goal_nodes_kind_check check (kind in ('goal', 'milestone', 'task', 'action')),
  constraint goal_nodes_status_check check (
    status in ('suggested', 'accepted', 'done', 'dismissed')
  ),
  constraint goal_nodes_title_check check (char_length(btrim(title)) between 1 and 200),
  constraint goal_nodes_est_minutes_check check (est_minutes is null or est_minutes > 0),
  constraint goal_nodes_interval_check check (interval_days is null or interval_days > 0),
  constraint goal_nodes_position_check check (position >= 0),
  constraint goal_nodes_specificity_check check (
    specificity_score is null or (specificity_score >= 1 and specificity_score <= 10)
  )
);

create trigger goal_nodes_enforce_same_tree
  before insert or update on public.goal_nodes
  for each row
  execute function public.enforce_goal_node_same_tree();

create index goal_nodes_tree_id_idx on public.goal_nodes (tree_id);
create index goal_nodes_user_id_idx on public.goal_nodes (user_id);
create index goal_nodes_parent_id_idx on public.goal_nodes (parent_id);
create index goal_nodes_category_id_idx on public.goal_nodes (category_id);

alter table public.habits
  add constraint habits_goal_node_user_fkey
  foreign key (goal_node_id, user_id) references public.goal_nodes (id, user_id) on delete set null;

alter table public.goal_nodes
  add constraint goal_nodes_habit_user_fkey
  foreign key (habit_id, user_id) references public.habits (id, user_id) on delete set null;

alter table public.feed_items
  add constraint feed_items_goal_node_user_fkey
  foreign key (goal_node_id, user_id) references public.goal_nodes (id, user_id) on delete restrict;

create index habits_goal_node_id_idx on public.habits (goal_node_id);
create index goal_nodes_habit_id_idx on public.goal_nodes (habit_id);
create index feed_items_goal_node_id_idx on public.feed_items (goal_node_id);

-- ---------------------------------------------------------------------------
-- completions
-- History is not removed when a habit or action is deleted (ON DELETE RESTRICT).
-- ---------------------------------------------------------------------------

create table public.completions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  habit_id uuid,
  goal_node_id uuid,
  done_at timestamptz not null default now(),
  feed_item_id uuid references public.feed_items (id) on delete set null,
  note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint completions_id_user_unique unique (id, user_id),
  constraint completions_habit_user_fkey
    foreign key (habit_id, user_id) references public.habits (id, user_id) on delete restrict,
  constraint completions_goal_node_user_fkey
    foreign key (goal_node_id, user_id) references public.goal_nodes (id, user_id) on delete restrict,
  constraint completions_target_check check (num_nonnulls(habit_id, goal_node_id) = 1)
);

create index completions_user_done_at_idx on public.completions (user_id, done_at desc);
create index completions_habit_id_idx on public.completions (habit_id);
create index completions_goal_node_id_idx on public.completions (goal_node_id);
create index completions_feed_item_id_idx on public.completions (feed_item_id);

-- ---------------------------------------------------------------------------
-- api_tokens
-- Only the hash is stored. Clients may list tokens; creating and revoking
-- go through the service role.
-- ---------------------------------------------------------------------------

create table public.api_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  token_hash text not null,
  scopes text[] not null default '{bubbles:write}',
  last_used_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint api_tokens_id_user_unique unique (id, user_id),
  constraint api_tokens_token_hash_unique unique (token_hash),
  constraint api_tokens_token_hash_check check (token_hash ~ '^[0-9a-f]{64}$'),
  constraint api_tokens_scopes_check check (
    cardinality(scopes) > 0
    and scopes <@ array['bubbles:write']::text[]
  )
);

create index api_tokens_user_id_idx on public.api_tokens (user_id);

-- ---------------------------------------------------------------------------
-- updated_at triggers
-- ---------------------------------------------------------------------------

do $$
declare
  table_name text;
begin
  foreach table_name in array array[
    'profiles',
    'categories',
    'bubbles',
    'judge_results',
    'links',
    'habits',
    'habit_weights',
    'completions',
    'daily_feeds',
    'feed_items',
    'goal_trees',
    'goal_tree_bubbles',
    'goal_nodes',
    'api_tokens'
  ]
  loop
    execute format(
      'create trigger %I before update on public.%I for each row execute function public.set_updated_at()',
      table_name || '_set_updated_at',
      table_name
    );
  end loop;
end $$;

-- ---------------------------------------------------------------------------
-- RLS
-- postgres and service_role bypass RLS. Authenticated policies are what the
-- Data API enforces. Composite foreign keys, not the policies, stop a child
-- row from pointing at another user's parent.
-- ---------------------------------------------------------------------------

alter table public.profiles enable row level security;
alter table public.categories enable row level security;
alter table public.bubbles enable row level security;
alter table public.judge_results enable row level security;
alter table public.links enable row level security;
alter table public.habits enable row level security;
alter table public.habit_weights enable row level security;
alter table public.completions enable row level security;
alter table public.daily_feeds enable row level security;
alter table public.feed_items enable row level security;
alter table public.goal_trees enable row level security;
alter table public.goal_tree_bubbles enable row level security;
alter table public.goal_nodes enable row level security;
alter table public.api_tokens enable row level security;

create policy profiles_select_own on public.profiles for select to authenticated using (user_id = (select auth.uid()));
create policy profiles_insert_own on public.profiles for insert to authenticated with check (user_id = (select auth.uid()));
create policy profiles_update_own on public.profiles for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));

create policy categories_select_authenticated on public.categories for select to authenticated using (true);

create policy bubbles_select_own on public.bubbles for select to authenticated using (user_id = (select auth.uid()));
create policy bubbles_insert_own on public.bubbles for insert to authenticated with check (user_id = (select auth.uid()));
create policy bubbles_update_own on public.bubbles for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy bubbles_delete_own on public.bubbles for delete to authenticated using (user_id = (select auth.uid()));

create policy judge_results_select_own on public.judge_results for select to authenticated using (user_id = (select auth.uid()));
create policy judge_results_insert_own on public.judge_results for insert to authenticated with check (user_id = (select auth.uid()));
create policy judge_results_update_own on public.judge_results for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy judge_results_delete_own on public.judge_results for delete to authenticated using (user_id = (select auth.uid()));

create policy links_select_own on public.links for select to authenticated using (user_id = (select auth.uid()));
create policy links_insert_own on public.links for insert to authenticated with check (user_id = (select auth.uid()));
create policy links_update_own on public.links for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy links_delete_own on public.links for delete to authenticated using (user_id = (select auth.uid()));

create policy habits_select_own_or_preset on public.habits for select to authenticated using (user_id is null or user_id = (select auth.uid()));
create policy habits_insert_own on public.habits for insert to authenticated with check (user_id = (select auth.uid()));
create policy habits_update_own on public.habits for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy habits_delete_own on public.habits for delete to authenticated using (user_id = (select auth.uid()));

create policy habit_weights_select_own on public.habit_weights for select to authenticated using (user_id = (select auth.uid()));
create policy habit_weights_insert_own on public.habit_weights for insert to authenticated with check (user_id = (select auth.uid()));
create policy habit_weights_update_own on public.habit_weights for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy habit_weights_delete_own on public.habit_weights for delete to authenticated using (user_id = (select auth.uid()));

create policy completions_select_own on public.completions for select to authenticated using (user_id = (select auth.uid()));
create policy completions_insert_own on public.completions for insert to authenticated with check (user_id = (select auth.uid()));
create policy completions_update_own on public.completions for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy completions_delete_own on public.completions for delete to authenticated using (user_id = (select auth.uid()));

create policy daily_feeds_select_own on public.daily_feeds for select to authenticated using (user_id = (select auth.uid()));
create policy daily_feeds_insert_own on public.daily_feeds for insert to authenticated with check (user_id = (select auth.uid()));
create policy daily_feeds_update_own on public.daily_feeds for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy daily_feeds_delete_own on public.daily_feeds for delete to authenticated using (user_id = (select auth.uid()));

create policy feed_items_select_own on public.feed_items for select to authenticated using (user_id = (select auth.uid()));
create policy feed_items_insert_own on public.feed_items for insert to authenticated with check (user_id = (select auth.uid()));
create policy feed_items_update_own on public.feed_items for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy feed_items_delete_own on public.feed_items for delete to authenticated using (user_id = (select auth.uid()));

create policy goal_trees_select_own on public.goal_trees for select to authenticated using (user_id = (select auth.uid()));
create policy goal_trees_insert_own on public.goal_trees for insert to authenticated with check (user_id = (select auth.uid()));
create policy goal_trees_update_own on public.goal_trees for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy goal_trees_delete_own on public.goal_trees for delete to authenticated using (user_id = (select auth.uid()));

create policy goal_tree_bubbles_select_own on public.goal_tree_bubbles for select to authenticated using (user_id = (select auth.uid()));
create policy goal_tree_bubbles_insert_own on public.goal_tree_bubbles for insert to authenticated with check (user_id = (select auth.uid()));
create policy goal_tree_bubbles_update_own on public.goal_tree_bubbles for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy goal_tree_bubbles_delete_own on public.goal_tree_bubbles for delete to authenticated using (user_id = (select auth.uid()));

create policy goal_nodes_select_own on public.goal_nodes for select to authenticated using (user_id = (select auth.uid()));
create policy goal_nodes_insert_own on public.goal_nodes for insert to authenticated with check (user_id = (select auth.uid()));
create policy goal_nodes_update_own on public.goal_nodes for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy goal_nodes_delete_own on public.goal_nodes for delete to authenticated using (user_id = (select auth.uid()));

create policy api_tokens_select_own on public.api_tokens for select to authenticated using (user_id = (select auth.uid()));

-- ---------------------------------------------------------------------------
-- Grants. anon can read nothing useful (RLS has no anon policies) and cannot
-- write. authenticated cannot create or revoke api tokens.
-- ---------------------------------------------------------------------------

grant usage on schema public to anon, authenticated, service_role;
grant select, insert, update, delete on all tables in schema public to anon, authenticated;
grant all privileges on all tables in schema public to service_role;
grant usage, select on all sequences in schema public to anon, authenticated, service_role;

revoke insert, update, delete on all tables in schema public from anon;
revoke insert, update, delete on table public.api_tokens from authenticated;

create trigger on_auth_user_created
  after insert on auth.users
  for each row
  execute function public.handle_new_user();
