-- RLS and cross-parent checks. `supabase test db` rolls this transaction back.

begin;

create extension if not exists pgtap with schema extensions;

set search_path = public, extensions, auth;

select plan(106);

insert into auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at,
  confirmation_token,
  recovery_token,
  email_change_token_new,
  email_change,
  email_change_token_current,
  phone_change,
  phone_change_token,
  reauthentication_token,
  is_sso_user,
  is_anonymous
)
values
  (
    '00000000-0000-0000-0000-000000000000',
    '11111111-1111-4111-8111-111111111111',
    'authenticated',
    'authenticated',
    'user-a@example.com',
    '',
    now(),
    '{"provider":"email","providers":["email"]}'::jsonb,
    '{}'::jsonb,
    now(),
    now(),
    '',
    '',
    '',
    '',
    '',
    '',
    '',
    '',
    false,
    false
  ),
  (
    '00000000-0000-0000-0000-000000000000',
    '22222222-2222-4222-8222-222222222222',
    'authenticated',
    'authenticated',
    'user-b@example.com',
    '',
    now(),
    '{"provider":"email","providers":["email"]}'::jsonb,
    '{}'::jsonb,
    now(),
    now(),
    '',
    '',
    '',
    '',
    '',
    '',
    '',
    '',
    false,
    false
  );

insert into public.api_tokens (id, user_id, token_hash)
values (
  'c0000000-0000-4000-8000-000000000050',
  '11111111-1111-4111-8111-111111111111',
  'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
);

select is(
  (
    select count(*)
    from public.profiles
    where user_id in (
      '11111111-1111-4111-8111-111111111111',
      '22222222-2222-4222-8222-222222222222'
    )
  ),
  2::bigint,
  'inserting an auth user creates a profile row'
);

select is(
  (select timezone from public.profiles where user_id = '11111111-1111-4111-8111-111111111111'),
  'Asia/Shanghai',
  'new profile defaults to Asia/Shanghai'
);

select is(
  (
    select judge_confidence_min
    from public.profiles
    where user_id = '11111111-1111-4111-8111-111111111111'
  ),
  0.60::numeric,
  'new profile defaults judge_confidence_min to 0.60'
);

select is(
  (
    select feed_max_items
    from public.profiles
    where user_id = '11111111-1111-4111-8111-111111111111'
  ),
  5::smallint,
  'feed_max_items defaults to 5'
);

select is(
  (
    select data_type
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'habit_weights'
      and column_name = 'weight'
  ),
  'double precision',
  'habit weight is double precision'
);

select is(
  (
    select data_type
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'habit_weights'
      and column_name = 'boost'
  ),
  'double precision',
  'habit boost is double precision'
);

select ok(
  not has_table_privilege('anon', 'public.bubbles', 'INSERT'),
  'anon insert is revoked'
);
select ok(
  not has_table_privilege('anon', 'public.bubbles', 'UPDATE'),
  'anon update is revoked'
);
select ok(
  not has_table_privilege('anon', 'public.bubbles', 'DELETE'),
  'anon delete is revoked'
);
select ok(
  has_table_privilege('authenticated', 'public.api_tokens', 'SELECT'),
  'authenticated can select api tokens'
);
select ok(
  not has_table_privilege('authenticated', 'public.api_tokens', 'INSERT'),
  'authenticated cannot insert api tokens'
);
select ok(
  not has_table_privilege('authenticated', 'public.api_tokens', 'UPDATE'),
  'authenticated cannot update api tokens'
);
select ok(
  not has_table_privilege('authenticated', 'public.api_tokens', 'DELETE'),
  'authenticated cannot delete api tokens'
);

-- User A -------------------------------------------------------------------

do $$
begin
  perform set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);
  perform set_config('request.jwt.claim.role', 'authenticated', true);
  perform set_config(
    'request.jwt.claims',
    '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated"}',
    true
  );
end $$;
set local role authenticated;

select lives_ok(
  $$
    insert into public.bubbles (id, user_id, content, source)
    values
      ('c0000000-0000-4000-8000-000000000001', '11111111-1111-4111-8111-111111111111', 'user-a-private-idea', 'web'),
      ('c0000000-0000-4000-8000-000000000002', '11111111-1111-4111-8111-111111111111', 'user-a-second-idea', 'assistant')
  $$,
  'user A can insert their own bubbles'
);

select is(
  (select category_status from public.bubbles where id = 'c0000000-0000-4000-8000-000000000001'),
  'unjudged',
  'a new bubble starts unjudged'
);
select is(
  (select breakdown_status from public.bubbles where id = 'c0000000-0000-4000-8000-000000000001'),
  'pending',
  'a new bubble starts with breakdown pending'
);

select lives_ok(
  $$
    insert into public.judge_results (
      id, user_id, bubble_id, provider, model, question_key, answer, latency_ms
    )
    values (
      'c0000000-0000-4000-8000-000000000040',
      '11111111-1111-4111-8111-111111111111',
      'c0000000-0000-4000-8000-000000000001',
      'llm',
      'test',
      'small_enough',
      'yes',
      12
    )
  $$,
  'user A can insert a judge result without confidence'
);

select ok(
  (select confidence is null from public.judge_results where id = 'c0000000-0000-4000-8000-000000000040'),
  'yes/no results can omit confidence'
);

select lives_ok(
  $$
    insert into public.links (id, user_id, bubble_a, bubble_b, similarity, kind)
    values (
      'c0000000-0000-4000-8000-000000000041',
      '11111111-1111-4111-8111-111111111111',
      'c0000000-0000-4000-8000-000000000001',
      'c0000000-0000-4000-8000-000000000002',
      0.9,
      'auto'
    )
  $$,
  'user A can link their own bubbles'
);

select lives_ok(
  $$
    insert into public.habits (
      id, user_id, category_id, title, size, est_minutes, interval_days, source, template_id
    )
    values (
      'c0000000-0000-4000-8000-000000000010',
      '11111111-1111-4111-8111-111111111111',
      'a0000000-0000-4000-8000-000000000001',
      '喝一杯水',
      'xs',
      1,
      2,
      'preset',
      'b0000000-0000-4000-8000-000000000001'
    )
  $$,
  'user A can copy a preset habit'
);

select lives_ok(
  $$
    update public.habits
    set status = 'paused', interval_days = 3
    where id = 'c0000000-0000-4000-8000-000000000010'
  $$,
  'user A can pause and reschedule their copy'
);

select is_empty(
  $$
    update public.habits
    set title = 'hacked'
    where id = 'b0000000-0000-4000-8000-000000000001'
    returning 1
  $$,
  'preset templates stay read-only'
);

select lives_ok(
  $$
    insert into public.habit_weights (user_id, habit_id, weight, boost)
    values (
      '11111111-1111-4111-8111-111111111111',
      'c0000000-0000-4000-8000-000000000010',
      0.6561,
      0.051234
    )
  $$,
  'user A can store a precise weight on their copy'
);

select lives_ok(
  $$
    insert into public.daily_feeds (id, user_id, date)
    values (
      'c0000000-0000-4000-8000-000000000020',
      '11111111-1111-4111-8111-111111111111',
      '2026-09-27'
    )
  $$,
  'user A can insert a daily feed'
);

select lives_ok(
  $$
    insert into public.goal_trees (id, user_id, mode)
    values (
      'c0000000-0000-4000-8000-000000000030',
      '11111111-1111-4111-8111-111111111111',
      'micro'
    )
  $$,
  'user A can insert a micro goal tree'
);

select lives_ok(
  $$
    insert into public.goal_tree_bubbles (tree_id, bubble_id, user_id)
    values (
      'c0000000-0000-4000-8000-000000000030',
      'c0000000-0000-4000-8000-000000000001',
      '11111111-1111-4111-8111-111111111111'
    )
  $$,
  'user A can attach their bubble to their tree'
);

select lives_ok(
  $$
    insert into public.goal_nodes (
      id, tree_id, user_id, kind, title, status, done_definition, pinned, position, specificity_score
    )
    values (
      'c0000000-0000-4000-8000-000000000031',
      'c0000000-0000-4000-8000-000000000030',
      '11111111-1111-4111-8111-111111111111',
      'action',
      '倒一杯水',
      'accepted',
      '杯子空了',
      true,
      0,
      8
    )
  $$,
  'user A can insert an accepted action'
);

select lives_ok(
  $$
    insert into public.feed_items (id, feed_id, user_id, habit_id, rank, score)
    values (
      'c0000000-0000-4000-8000-000000000021',
      'c0000000-0000-4000-8000-000000000020',
      '11111111-1111-4111-8111-111111111111',
      'c0000000-0000-4000-8000-000000000010',
      1,
      0.5
    )
  $$,
  'user A can insert a feed item for their habit'
);

select lives_ok(
  $$
    insert into public.completions (id, user_id, habit_id)
    values (
      'c0000000-0000-4000-8000-000000000022',
      '11111111-1111-4111-8111-111111111111',
      'c0000000-0000-4000-8000-000000000010'
    )
  $$,
  'user A can record a habit completion'
);

select lives_ok(
  $$
    insert into public.completions (id, user_id, goal_node_id)
    values (
      'c0000000-0000-4000-8000-000000000023',
      '11111111-1111-4111-8111-111111111111',
      'c0000000-0000-4000-8000-000000000031'
    )
  $$,
  'user A can record an action completion'
);

select is((select count(*) from public.bubbles), 2::bigint, 'user A reads both bubbles');
select is((select count(*) from public.judge_results), 1::bigint, 'user A reads their judge result');
select is((select count(*) from public.links), 1::bigint, 'user A reads their link');
select is(
  (select count(*) from public.habits where user_id = '11111111-1111-4111-8111-111111111111'),
  1::bigint,
  'user A reads their habit copy'
);
select is((select count(*) from public.habit_weights), 1::bigint, 'user A reads their weight');
select is((select count(*) from public.daily_feeds), 1::bigint, 'user A reads their feed');
select is((select count(*) from public.feed_items), 1::bigint, 'user A reads their feed item');
select is((select count(*) from public.goal_trees), 1::bigint, 'user A reads their tree');
select is((select count(*) from public.goal_tree_bubbles), 1::bigint, 'user A reads their tree link');
select is((select count(*) from public.goal_nodes), 1::bigint, 'user A reads their action');
select is((select count(*) from public.completions), 2::bigint, 'user A reads their completions');
select is((select count(*) from public.api_tokens), 1::bigint, 'user A can list their token');
select is((select count(*) from public.categories), 6::bigint, 'authenticated users can read categories');
select ok(
  (
    select count(*) between 5 and 8
    from public.habits
    where user_id is null
      and category_id = 'a0000000-0000-4000-8000-000000000001'
  ),
  'health presets are visible and within 5-8 habits'
);

select throws_ok(
  $$
    insert into public.api_tokens (user_id, token_hash)
    values (
      '11111111-1111-4111-8111-111111111111',
      'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    )
  $$,
  '42501',
  null,
  'user A cannot create an api token from the client role'
);

select throws_ok(
  $$
    update public.api_tokens set revoked_at = null
  $$,
  '42501',
  null,
  'user A cannot clear revoked_at'
);

select throws_ok(
  $$
    insert into public.categories (key, name_zh, description_en, color)
    values ('custom', '自定义', 'nope', '#000000')
  $$,
  '42501',
  null,
  'authenticated users cannot insert categories'
);

-- User B -------------------------------------------------------------------

reset role;
do $$
begin
  perform set_config('request.jwt.claim.sub', '22222222-2222-4222-8222-222222222222', true);
  perform set_config('request.jwt.claim.role', 'authenticated', true);
  perform set_config(
    'request.jwt.claims',
    '{"sub":"22222222-2222-4222-8222-222222222222","role":"authenticated"}',
    true
  );
end $$;
set local role authenticated;

select is((select count(*) from public.bubbles), 0::bigint, 'user B cannot read user A bubbles');
select is((select count(*) from public.judge_results), 0::bigint, 'user B cannot read user A judge results');
select is((select count(*) from public.links), 0::bigint, 'user B cannot read user A links');
select is(
  (select count(*) from public.habits where user_id is not null),
  0::bigint,
  'user B cannot read user A habits'
);
select is((select count(*) from public.habit_weights), 0::bigint, 'user B cannot read user A weights');
select is((select count(*) from public.completions), 0::bigint, 'user B cannot read user A completions');
select is((select count(*) from public.daily_feeds), 0::bigint, 'user B cannot read user A feeds');
select is((select count(*) from public.feed_items), 0::bigint, 'user B cannot read user A feed items');
select is((select count(*) from public.goal_trees), 0::bigint, 'user B cannot read user A trees');
select is((select count(*) from public.goal_tree_bubbles), 0::bigint, 'user B cannot read user A tree links');
select is((select count(*) from public.goal_nodes), 0::bigint, 'user B cannot read user A actions');
select is(
  (select count(*) from public.profiles where user_id = '11111111-1111-4111-8111-111111111111'),
  0::bigint,
  'user B cannot read user A profile'
);
select is((select count(*) from public.api_tokens), 0::bigint, 'user B cannot read user A tokens');

select is_empty($$ update public.bubbles set content = 'stolen' returning 1 $$, 'user B cannot update bubbles');
select is_empty($$ delete from public.bubbles returning 1 $$, 'user B cannot delete bubbles');
select is_empty($$ update public.judge_results set answer = 'no' returning 1 $$, 'user B cannot update judge results');
select is_empty($$ delete from public.judge_results returning 1 $$, 'user B cannot delete judge results');
select is_empty($$ update public.links set kind = 'dismissed' returning 1 $$, 'user B cannot update links');
select is_empty($$ delete from public.links returning 1 $$, 'user B cannot delete links');
select is_empty($$ update public.habits set title = 'hacked' returning 1 $$, 'user B cannot update habits');
select is_empty($$ delete from public.habits returning 1 $$, 'user B cannot delete habits');
select is_empty($$ update public.habit_weights set weight = 1 returning 1 $$, 'user B cannot update weights');
select is_empty($$ delete from public.habit_weights returning 1 $$, 'user B cannot delete weights');
select is_empty($$ update public.completions set note = 'x' returning 1 $$, 'user B cannot update completions');
select is_empty($$ delete from public.completions returning 1 $$, 'user B cannot delete completions');
select is_empty($$ update public.daily_feeds set date = '2026-01-01' returning 1 $$, 'user B cannot update feeds');
select is_empty($$ delete from public.daily_feeds returning 1 $$, 'user B cannot delete feeds');
select is_empty($$ update public.feed_items set score = 0 returning 1 $$, 'user B cannot update feed items');
select is_empty($$ delete from public.feed_items returning 1 $$, 'user B cannot delete feed items');
select is_empty($$ update public.goal_trees set mode = 'bigger' returning 1 $$, 'user B cannot update trees');
select is_empty($$ delete from public.goal_trees returning 1 $$, 'user B cannot delete trees');
select is_empty($$ update public.goal_tree_bubbles set bubble_id = bubble_id returning 1 $$, 'user B cannot update tree links');
select is_empty($$ delete from public.goal_tree_bubbles returning 1 $$, 'user B cannot delete tree links');
select is_empty($$ update public.goal_nodes set title = 'stolen' returning 1 $$, 'user B cannot update actions');
select is_empty($$ delete from public.goal_nodes returning 1 $$, 'user B cannot delete actions');
select is_empty($$ update public.profiles set timezone = 'UTC' where user_id = '11111111-1111-4111-8111-111111111111' returning 1 $$, 'user B cannot update user A profile');
select is_empty($$ delete from public.categories returning 1 $$, 'user B cannot delete categories');

select throws_ok(
  $$
    insert into public.bubbles (user_id, content)
    values ('11111111-1111-4111-8111-111111111111', 'spoofed')
  $$,
  '42501',
  null,
  'user B cannot insert a bubble owned by user A'
);

select throws_ok(
  $$
    insert into public.judge_results (
      user_id, bubble_id, provider, model, question_key, answer, latency_ms
    )
    values (
      '22222222-2222-4222-8222-222222222222',
      'c0000000-0000-4000-8000-000000000001',
      'llm',
      'test',
      'category',
      'health',
      1
    )
  $$,
  '23503',
  null,
  'user B cannot attach a judge result to user A bubble'
);

select throws_ok(
  $$
    insert into public.links (user_id, bubble_a, bubble_b, similarity, kind)
    values (
      '22222222-2222-4222-8222-222222222222',
      'c0000000-0000-4000-8000-000000000001',
      'c0000000-0000-4000-8000-000000000002',
      0.1,
      'auto'
    )
  $$,
  '23503',
  null,
  'user B cannot link user A bubbles'
);

select throws_ok(
  $$
    insert into public.habit_weights (user_id, habit_id, weight)
    values (
      '22222222-2222-4222-8222-222222222222',
      'c0000000-0000-4000-8000-000000000010',
      1
    )
  $$,
  '23503',
  null,
  'user B cannot weight user A habit'
);

select throws_ok(
  $$
    insert into public.habit_weights (user_id, habit_id, weight)
    values (
      '22222222-2222-4222-8222-222222222222',
      'b0000000-0000-4000-8000-000000000001',
      1
    )
  $$,
  '23503',
  null,
  'a weight cannot target a shared preset template'
);

select throws_ok(
  $$
    insert into public.completions (user_id, habit_id)
    values (
      '22222222-2222-4222-8222-222222222222',
      'c0000000-0000-4000-8000-000000000010'
    )
  $$,
  '23503',
  null,
  'user B cannot complete user A habit'
);

select throws_ok(
  $$
    insert into public.goal_nodes (user_id, tree_id, kind, title)
    values (
      '22222222-2222-4222-8222-222222222222',
      'c0000000-0000-4000-8000-000000000030',
      'action',
      '别人的树'
    )
  $$,
  '23503',
  null,
  'user B cannot add a node to user A tree'
);

select lives_ok(
  $$
    insert into public.bubbles (id, user_id, content)
    values (
      'c0000000-0000-4000-8000-000000000003',
      '22222222-2222-4222-8222-222222222222',
      'user-b-idea'
    )
  $$,
  'user B can insert their own bubble'
);

select lives_ok(
  $$
    insert into public.daily_feeds (id, user_id, date)
    values (
      'c0000000-0000-4000-8000-000000000024',
      '22222222-2222-4222-8222-222222222222',
      '2026-09-27'
    )
  $$,
  'user B can insert their own feed'
);

select throws_ok(
  $$
    insert into public.feed_items (feed_id, user_id, habit_id, rank, score)
    values (
      'c0000000-0000-4000-8000-000000000024',
      '22222222-2222-4222-8222-222222222222',
      'c0000000-0000-4000-8000-000000000010',
      1,
      0.2
    )
  $$,
  '23503',
  null,
  'user B cannot hang a feed item on user A habit'
);

select lives_ok(
  $$
    insert into public.goal_trees (id, user_id, mode)
    values (
      'c0000000-0000-4000-8000-000000000032',
      '22222222-2222-4222-8222-222222222222',
      'concrete'
    )
  $$,
  'user B can insert their own tree'
);

select throws_ok(
  $$
    insert into public.goal_tree_bubbles (tree_id, bubble_id, user_id)
    values (
      'c0000000-0000-4000-8000-000000000032',
      'c0000000-0000-4000-8000-000000000001',
      '22222222-2222-4222-8222-222222222222'
    )
  $$,
  '23503',
  null,
  'user B cannot attach user A bubble to their tree'
);

select is((select count(*) from public.bubbles), 1::bigint, 'user B only sees their own bubble');

-- anon ---------------------------------------------------------------------

reset role;
set local role anon;

select is((select count(*) from public.bubbles), 0::bigint, 'anon cannot read bubbles');
select is((select count(*) from public.categories), 0::bigint, 'anon cannot read categories');
select throws_ok(
  $$ insert into public.bubbles (user_id, content) values ('22222222-2222-4222-8222-222222222222', 'nope') $$,
  '42501',
  null,
  'anon cannot insert bubbles'
);

-- User A constraints -------------------------------------------------------

reset role;
do $$
begin
  perform set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);
  perform set_config('request.jwt.claim.role', 'authenticated', true);
  perform set_config(
    'request.jwt.claims',
    '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated"}',
    true
  );
end $$;
set local role authenticated;

select lives_ok(
  $$
    insert into public.goal_nodes (id, tree_id, user_id, parent_id, kind, title)
    values (
      'c0000000-0000-4000-8000-000000000033',
      'c0000000-0000-4000-8000-000000000030',
      '11111111-1111-4111-8111-111111111111',
      'c0000000-0000-4000-8000-000000000031',
      'action',
      'same tree child'
    )
  $$,
  'a parent in the same tree is allowed'
);

select lives_ok(
  $$
    insert into public.goal_trees (id, user_id, mode)
    values (
      'c0000000-0000-4000-8000-000000000034',
      '11111111-1111-4111-8111-111111111111',
      'concrete'
    )
  $$,
  'user A can insert a second tree'
);

select throws_ok(
  $$
    insert into public.goal_nodes (tree_id, user_id, parent_id, kind, title)
    values (
      'c0000000-0000-4000-8000-000000000034',
      '11111111-1111-4111-8111-111111111111',
      'c0000000-0000-4000-8000-000000000031',
      'action',
      'wrong tree'
    )
  $$,
  '23514',
  null,
  'a parent must belong to the same tree'
);

select throws_ok(
  $$ delete from public.habits where id = 'c0000000-0000-4000-8000-000000000010' $$,
  '23503',
  null,
  'a habit with history cannot be deleted'
);

select throws_ok(
  $$ delete from public.goal_nodes where id = 'c0000000-0000-4000-8000-000000000031' $$,
  '23503',
  null,
  'an action with history cannot be deleted'
);

select lives_ok(
  $$
    do $body$
    begin
      delete from public.completions
      where user_id = '11111111-1111-4111-8111-111111111111';
      delete from public.feed_items
      where user_id = '11111111-1111-4111-8111-111111111111';
      delete from public.habit_weights
      where user_id = '11111111-1111-4111-8111-111111111111';
      delete from public.habits
      where user_id = '11111111-1111-4111-8111-111111111111';
      delete from public.goal_nodes
      where user_id = '11111111-1111-4111-8111-111111111111';
    end
    $body$
  $$,
  'history can be removed before the habit and the action'
);

select * from finish();
rollback;
