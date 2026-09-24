-- Frahoosh test-account bridge
-- Run this once in the target Supabase SQL Editor after creating the three
-- Auth users. It links the Auth identities to the school roles used by the
-- Android app. The same national code is intentional for this test.
--
-- Auth users expected:
-- ali.test@frahoosh.local
-- reza.test@frahoosh.local
-- mohamad.test@frahoosh.local
-- Passwords are the first Persian letter of the name + 0123456789.

create schema if not exists private;

insert into public.account_settings (username, display_name, email, national_code, preferences, updated_at)
values
 ('ali.test@frahoosh.local','علی','ali.test@frahoosh.local','0123456789','{"role":"teacher"}'::jsonb,now()),
 ('reza.test@frahoosh.local','رضا','reza.test@frahoosh.local','0123456789','{"role":"parent"}'::jsonb,now()),
 ('mohamad.test@frahoosh.local','محمد','mohamad.test@frahoosh.local','0123456789','{"role":"student"}'::jsonb,now())
on conflict do nothing;

-- Keep exactly one school user row for each test identity.
delete from public.users
where username in ('ali.test@frahoosh.local','reza.test@frahoosh.local','mohamad.test@frahoosh.local');

insert into public.users (username, role, display_name, permissions)
values
 ('ali.test@frahoosh.local','teacher','علی','{}'::jsonb),
 ('reza.test@frahoosh.local','parent','رضا','{}'::jsonb),
 ('mohamad.test@frahoosh.local','student','محمد','{}'::jsonb);

-- Teacher record used by the meeting target selector.
delete from public.teachers where email='ali.test@frahoosh.local';
insert into public.teachers (first_name,last_name,national_code,email,subject,employment_status)
values ('علی','تست','0123456789','ali.test@frahoosh.local','عمومی','فعال');

-- Student record used by the parent -> child selector.
delete from public.students where email='mohamad.test@frahoosh.local';
insert into public.students (first_name,last_name,national_code,email,grade,class_name)
values ('محمد','تست','0123456789','mohamad.test@frahoosh.local','هفتم','7/1');

-- Resolve the teacher/student links after their rows exist.
update public.users u
set linked_teacher_id=(select t.id from public.teachers t where t.email='ali.test@frahoosh.local' limit 1)
where u.username='ali.test@frahoosh.local';

update public.users u
set linked_student_id=(select s.id from public.students s where s.email='mohamad.test@frahoosh.local' limit 1)
where u.username='mohamad.test@frahoosh.local';

delete from public.parent_children
where parent_username='reza.test@frahoosh.local';

insert into public.parent_children (parent_username,student_id)
select 'reza.test@frahoosh.local',s.id
from public.students s
where s.email='mohamad.test@frahoosh.local'
limit 1;

-- Multi-account national-code lookup. Do not use LIMIT 1 here: the three
-- temporary test accounts intentionally share one placeholder national code.
create or replace function public.lookup_auth_emails_by_national_code(p_national_code text)
returns table(email text)
language sql
security definer
set search_path = ''
stable
as $$
  select distinct u.email
  from auth.users u
  join public.account_settings a
    on lower(trim(a.email))=lower(trim(u.email))
  where regexp_replace(translate(coalesce(a.national_code,''),'۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789'),'[^0-9]','','g')
      = regexp_replace(translate(coalesce(p_national_code,''),'۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789'),'[^0-9]','','g')
    and regexp_replace(translate(coalesce(p_national_code,''),'۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789'),'[^0-9]','','g') <> '';
$$;

revoke all on function public.lookup_auth_emails_by_national_code(text) from public;
grant execute on function public.lookup_auth_emails_by_national_code(text) to anon, authenticated;

create or replace function public.lookup_auth_email_by_national_code(p_national_code text)
returns text
language sql
security definer
set search_path = ''
stable
as $$
  select email
  from public.lookup_auth_emails_by_national_code(p_national_code)
  limit 1;
$$;

revoke all on function public.lookup_auth_email_by_national_code(text) from public;
grant execute on function public.lookup_auth_email_by_national_code(text) to anon, authenticated;
