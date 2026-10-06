-- Frahoosh final backend hardening for the approved legacy Supabase project.
-- Canonical authenticated roles + relationship/payment indexes.

create or replace function private.frahoosh_current_role()
returns text language sql stable security definer set search_path to ''
as $function$
  select case lower(trim(replace(replace(replace(coalesce(
    (select a.role from public.account_settings a where a.auth_user_id = auth.uid() limit 1),
    (select u.role from public.users u where lower(u.username)=lower(coalesce(auth.jwt()->>'email','')) limit 1),
    ''
  ), 'ي','ی'),'ك','ک'), chr(8204), ' ')))
    when 'admin' then 'manager' when 'administrator' then 'manager' when 'manager' then 'manager'
    when 'مدیر' then 'manager' when 'مدیریت' then 'manager' when 'مدیر مدرسه' then 'manager' when 'مدیریت مدرسه' then 'manager'
    when 'educational' then 'educational' when 'educational_deputy' then 'educational' when 'معاون آموزشی' then 'educational' when 'معاونت آموزشی' then 'educational' when 'آموزشی' then 'educational'
    when 'executive' then 'executive' when 'executive_deputy' then 'executive' when 'معاون اجرایی' then 'executive' when 'معاونت اجرایی' then 'executive' when 'اجرایی' then 'executive'
    when 'cultural' then 'cultural' when 'cultural_deputy' then 'cultural' when 'معاون پرورشی' then 'cultural' when 'معاونت پرورشی' then 'cultural' when 'پرورشی' then 'cultural'
    when 'advisor' then 'advisor' when 'counselor' then 'advisor' when 'counseling' then 'advisor' when 'مشاور' then 'advisor' when 'مشاوره' then 'advisor'
    when 'teacher' then 'teacher' when 'teacher_staff' then 'teacher' when 'دبیر' then 'teacher' when 'دبیران' then 'teacher' when 'معلم' then 'teacher'
    when 'student' then 'student' when 'دانش‌آموز' then 'student' when 'دانش آموز' then 'student' when 'دانش‌آموزان' then 'student'
    when 'parent' then 'parent' when 'parent_guardian' then 'parent' when 'guardian' then 'parent' when 'ولی' then 'parent' when 'اولیا' then 'parent'
    else lower(trim(replace(replace(coalesce((select a.role from public.account_settings a where a.auth_user_id=auth.uid() limit 1),
      (select u.role from public.users u where lower(u.username)=lower(coalesce(auth.jwt()->>'email','')) limit 1),''),'ي','ی'),'ك','ک')))
  end
$function$;

create or replace function private.frahoosh_has_role(allowed_roles text[])
returns boolean language sql stable security definer set search_path to ''
as $function$ select private.frahoosh_current_role() = any(allowed_roles) $function$;

create index if not exists idx_account_settings_auth_user_id on public.account_settings(auth_user_id);
create index if not exists idx_account_settings_national_code on public.account_settings(national_code);
create index if not exists idx_parent_children_parent_username on public.parent_children(parent_username);
create index if not exists idx_parent_children_student_id on public.parent_children(student_id);
create index if not exists idx_teacher_classes_teacher_id on public.teacher_classes(teacher_id);
create index if not exists idx_teacher_classes_class_name on public.teacher_classes(class_name);
create index if not exists idx_meeting_requests_requester_username on public.meeting_requests(requester_username);
create index if not exists idx_meeting_requests_target_username on public.meeting_requests(target_username);
create index if not exists idx_meeting_requests_status on public.meeting_requests(status);
create index if not exists idx_payment_offers_active_status on public.payment_offers(active,status);
create index if not exists idx_payment_records_student_id on public.payment_records(student_id);
create index if not exists idx_payment_records_parent_username on public.payment_records(parent_username);
