-- Frahoosh ZIP contract hardening
-- Ensures existing deployments have every field required by the canonical ZIP
-- workspaces without replacing or duplicating existing tables.

alter table if exists public.report_cards
  add column if not exists grade_level text,
  add column if not exists academic_year text,
  add column if not exists report_date text;

alter table if exists public.generated_weekly_schedule
  add column if not exists source_id bigint;

alter table if exists public.weekly_schedule
  add column if not exists teacher_id bigint,
  add column if not exists weekdays text;

alter table if exists public.discipline_records
  add column if not exists title text,
  add column if not exists priority text default 'normal',
  add column if not exists status text default 'pending',
  add column if not exists item_id bigint,
  add column if not exists deduction numeric default 0,
  add column if not exists actor_username text,
  add column if not exists actor_role text,
  add column if not exists note text;

alter table if exists public.attendance
  add column if not exists teacher_id bigint,
  add column if not exists subject text,
  add column if not exists class_name text,
  add column if not exists attendance_date text;

alter table if exists public.teacher_attendance
  add column if not exists student_name text,
  add column if not exists note text,
  add column if not exists description text;

-- These tables are part of the ZIP canonical source and must be reachable
-- by authenticated Web/Android users under the existing application RLS model.
do $$
declare t text;
begin
  foreach t in array array[
    'report_cards','generated_weekly_schedule','weekly_schedule','discipline_records','attendance','teacher_attendance'
  ] loop
    if to_regclass('public.' || t) is not null then
      execute format('alter table public.%I enable row level security', t);
      execute format('drop policy if exists frahoosh_zip_authenticated on public.%I', t);
      execute format('create policy frahoosh_zip_authenticated on public.%I for all to authenticated using (true) with check (true)', t);
    end if;
  end loop;
end $$;
