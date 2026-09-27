-- RLS checks for local Supabase: `supabase test db`
-- Requires Docker. The transaction is rolled back, including the auth users.

begin;

create extension if not exists pgtap with schema extensions;

set search_path = public, extensions, auth;

select plan(13);

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
  (
    select timezone
    from public.profiles
    where user_id = '11111111-1111-4111-8111-111111111111'
  ),
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

-- set_config via PERFORM so the TAP stream stays free of extra result rows.
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
    insert into public.bubbles (user_id, content, source)
    values ('11111111-1111-4111-8111-111111111111', 'user-a-private-idea', 'web')
  $$,
  'user A can insert their own bubble'
);

select is(
  (select count(*) from public.bubbles),
  1::bigint,
  'user A can read their own bubble'
);

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

select is(
  (select count(*) from public.bubbles),
  0::bigint,
  'user B cannot read user A bubbles'
);

select throws_ok(
  $$
    insert into public.bubbles (user_id, content, source)
    values ('11111111-1111-4111-8111-111111111111', 'spoofed', 'web')
  $$,
  'user B cannot insert a bubble owned by user A'
);

select is(
  (select count(*) from public.categories),
  6::bigint,
  'authenticated users can read preset categories'
);

select ok(
  (
    select count(*) between 5 and 8
    from public.habits
    where user_id is null
      and category_id = 'a0000000-0000-4000-8000-000000000001'
  ),
  'health presets are visible and within 5-8 habits'
);

select is(
  (
    with updated as (
      update public.habits
      set title = 'hacked'
      where user_id is null
      returning 1
    )
    select count(*) from updated
  ),
  0::bigint,
  'preset habits are read-only'
);

select is(
  (
    with updated as (
      update public.bubbles
      set content = 'stolen'
      returning 1
    )
    select count(*) from updated
  ),
  0::bigint,
  'user B cannot update user A bubbles'
);

select is(
  (
    select count(*)
    from public.profiles
    where user_id = '11111111-1111-4111-8111-111111111111'
  ),
  0::bigint,
  'user B cannot read user A profile'
);

reset role;
set local role anon;

select is(
  (select count(*) from public.bubbles),
  0::bigint,
  'anon cannot read bubbles'
);

select * from finish();
rollback;
