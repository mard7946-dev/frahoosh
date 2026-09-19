-- Frahoosh ZIP canonical field hardening
-- Source: Frahoosh_v16_12_LOGIN_BACKGROUND_FINAL_02.zip
-- Ensures every field declared by shared/module_catalog.json exists on its real
-- Supabase table. Existing data is preserved; all additions are nullable/defaulted.

alter table if exists public.teacher_exams
  add column if not exists exam_date text,
  add column if not exists share_enabled boolean not null default false,
  add column if not exists share_code text;

alter table if exists public.activity_offers
  add column if not exists category text,
  add column if not exists event_date text,
  add column if not exists settings jsonb not null default '{}'::jsonb;

alter table if exists public.student_council
  add column if not exists election_year text;

alter table if exists public.basij_registration
  add column if not exists registration_date text;

alter table if exists public.school_ally
  add column if not exists role text;

alter table if exists public.meeting_requests
  add column if not exists teacher_id bigint,
  add column if not exists parent_phone text,
  add column if not exists target_type text,
  add column if not exists target_person text;

alter table if exists public.certificate_requests
  add column if not exists request_date text;

-- Keep the newly completed fields available through the same authenticated
-- application policy used by the ZIP operational tables.
do $$
declare t text;
begin
  foreach t in array array[
    'teacher_exams','activity_offers','student_council','basij_registration',
    'school_ally','meeting_requests','certificate_requests'
  ] loop
    if to_regclass('public.' || t) is not null then
      execute format('alter table public.%I enable row level security', t);
      execute format('drop policy if exists frahoosh_zip_contract_authenticated on public.%I', t);
      execute format(
        'create policy frahoosh_zip_contract_authenticated on public.%I for all to authenticated using (true) with check (true)',
        t
      );
    end if;
  end loop;
end $$;
