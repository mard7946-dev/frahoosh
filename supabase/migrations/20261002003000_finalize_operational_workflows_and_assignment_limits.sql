-- Final operational workflow foundation
alter table public.assignments
  add column if not exists max_file_size_mb integer not null default 10,
  add column if not exists expires_at timestamptz;
alter table public.assignment_submissions
  add column if not exists file_name text,
  add column if not exists file_mime_type text,
  add column if not exists file_size_bytes bigint,
  add column if not exists expires_at timestamptz;
alter table public.assignment_submissions drop constraint if exists assignment_submissions_file_size_check;
alter table public.assignment_submissions add constraint assignment_submissions_file_size_check
  check (file_size_bytes is null or file_size_bytes between 0 and 10485760);
create or replace function public.validate_assignment_submission()
returns trigger language plpgsql security definer set search_path=public as $$
declare a record;
begin
 select id,due_date,expires_at,max_file_size_mb into a from public.assignments where id=new.assignment_id;
 if not found then raise exception 'تکلیف انتخاب‌شده وجود ندارد'; end if;
 if a.due_date is not null and now()>a.due_date then raise exception 'مهلت ارسال این تکلیف به پایان رسیده است'; end if;
 if a.expires_at is not null and now()>a.expires_at then raise exception 'مهلت نگهداری/ارسال این تکلیف به پایان رسیده است'; end if;
 if new.file_size_bytes is not null and new.file_size_bytes > greatest(coalesce(a.max_file_size_mb,10),1)*1048576 then
   raise exception 'حجم فایل از سقف تعیین‌شده بیشتر است';
 end if;
 new.expires_at:=coalesce(new.expires_at,a.expires_at,now()+interval '10 days'); return new;
end; $$;
drop trigger if exists trg_validate_assignment_submission on public.assignment_submissions;
create trigger trg_validate_assignment_submission before insert or update on public.assignment_submissions
for each row execute function public.validate_assignment_submission();
create index if not exists idx_assignments_expires_at on public.assignments(expires_at);
create index if not exists idx_assignment_submissions_expires_at on public.assignment_submissions(expires_at);
create table if not exists public.module_activations (
 module_key text primary key, active boolean not null default false, activated_by uuid,
 activated_at timestamptz, updated_at timestamptz not null default now(), settings jsonb not null default '{}'::jsonb
);
alter table public.module_activations enable row level security;
drop policy if exists module_activations_staff_all on public.module_activations;
create policy module_activations_staff_all on public.module_activations for all to authenticated
using(private.frahoosh_is_staff()) with check(private.frahoosh_is_staff());
drop policy if exists module_activations_authenticated_read on public.module_activations;
create policy module_activations_authenticated_read on public.module_activations for select to authenticated using(true);
insert into public.module_activations(module_key,active) values
('activity_registrations',false),('student_council',false),('school_mayor',false),('school_ally',false),
('basij_registration',false),('certificate_requests',true),('parent_children',true),('transport_requests',false),
('parent_activities',false),('survey_responses',false),('teacher_exams',false),('online_classes',false)
on conflict(module_key) do nothing;
create or replace function public.is_module_active(p_module_key text)
returns boolean language sql stable security definer set search_path=public as $$
select coalesce((select active from public.module_activations where module_key=p_module_key),true) $$;
revoke all on function public.is_module_active(text) from public;
grant execute on function public.is_module_active(text) to authenticated;
drop policy if exists parent_children_parent_select on public.parent_children;
create policy parent_children_parent_select on public.parent_children for select to authenticated using(
 lower(coalesce(parent_username,'')) in(select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid())
 or lower(coalesce(parent_username,'')) in(select lower(coalesce(a.email,'')) from public.account_settings a where a.auth_user_id=auth.uid())
 or lower(coalesce(parent_username,'')) in(select lower(coalesce(a.national_code,'')) from public.account_settings a where a.auth_user_id=auth.uid())
);
drop policy if exists parent_children_parent_insert on public.parent_children;
create policy parent_children_parent_insert on public.parent_children for insert to authenticated with check(
 lower(coalesce(parent_username,'')) in(select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid())
 or lower(coalesce(parent_username,'')) in(select lower(coalesce(a.national_code,'')) from public.account_settings a where a.auth_user_id=auth.uid())
);
drop policy if exists parent_children_parent_update on public.parent_children;
create policy parent_children_parent_update on public.parent_children for update to authenticated using(
 lower(coalesce(parent_username,'')) in(select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid())
) with check(
 lower(coalesce(parent_username,'')) in(select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid())
);
drop policy if exists parent_children_parent_delete on public.parent_children;
create policy parent_children_parent_delete on public.parent_children for delete to authenticated using(
 lower(coalesce(parent_username,'')) in(select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid())
);