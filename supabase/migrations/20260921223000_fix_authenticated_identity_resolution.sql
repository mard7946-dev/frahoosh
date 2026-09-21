-- Frahoosh: resolve the authenticated user's role and links from
-- the same identity data used by the mobile login.
--
-- The previous helper only matched users.username to auth.jwt()->>'email'.
-- Login also supports national-code/username identifiers, so that comparison
-- can leave a valid manager with an empty role and consequently no RLS rows.
-- Keep the role decision inside SECURITY DEFINER helpers; RLS remains the
-- authorization boundary.

create or replace function private.frahoosh_current_role()
returns text
language sql
stable
security definer
set search_path=''
as $$
  select coalesce(
    (
      select nullif(trim(u.role),'')
      from public.users u
      left join public.account_settings a
        on lower(coalesce(a.email,'')) = lower(coalesce(auth.jwt()->>'email',''))
      where lower(coalesce(u.username,'')) = lower(coalesce(auth.jwt()->>'email',''))
         or (
           nullif(trim(a.national_code),'') is not null
           and lower(trim(coalesce(u.username,''))) = lower(trim(a.national_code))
         )
      order by case
        when lower(coalesce(u.username,'')) = lower(coalesce(auth.jwt()->>'email','')) then 0
        else 1
      end
      limit 1
    ),
    ''
  )
$$;

create or replace function private.frahoosh_current_student_id()
returns bigint
language sql
stable
security definer
set search_path=''
as $$
  select coalesce(
    (
      select u.linked_student_id
      from public.users u
      left join public.account_settings a
        on lower(coalesce(a.email,'')) = lower(coalesce(auth.jwt()->>'email',''))
      where lower(coalesce(u.username,'')) = lower(coalesce(auth.jwt()->>'email',''))
         or (
           nullif(trim(a.national_code),'') is not null
           and lower(trim(coalesce(u.username,''))) = lower(trim(a.national_code))
         )
      limit 1
    ),
    (
      select s.id
      from public.students s
      join public.account_settings a
        on lower(a.email)=lower(coalesce(auth.jwt()->>'email',''))
      where s.national_code=a.national_code
      limit 1
    )
  )
$$;

create or replace function private.frahoosh_current_teacher_id()
returns bigint
language sql
stable
security definer
set search_path=''
as $$
  select coalesce(
    (
      select u.linked_teacher_id
      from public.users u
      left join public.account_settings a
        on lower(coalesce(a.email,'')) = lower(coalesce(auth.jwt()->>'email',''))
      where lower(coalesce(u.username,'')) = lower(coalesce(auth.jwt()->>'email',''))
         or (
           nullif(trim(a.national_code),'') is not null
           and lower(trim(coalesce(u.username,''))) = lower(trim(a.national_code))
         )
      limit 1
    ),
    (
      select t.id
      from public.teachers t
      join public.account_settings a
        on lower(a.email)=lower(coalesce(auth.jwt()->>'email',''))
      where t.national_code=a.national_code
      limit 1
    )
  )
$$;

create or replace function private.frahoosh_is_staff()
returns boolean
language sql
stable
security definer
set search_path=''
as $$
  select lower(coalesce(private.frahoosh_current_role(),''))
    = any(array[
      'مدیر','مدیریت','manager',
      'معاون آموزشی','educational',
      'معاون اجرایی','اجرایی','executive',
      'معاون پرورشی','cultural',
      'مشاوره','counselor','advisor',
      'دبیر','teacher'
    ])
$$;

revoke all on function private.frahoosh_current_role() from public;
revoke all on function private.frahoosh_current_student_id() from public;
revoke all on function private.frahoosh_current_teacher_id() from public;
revoke all on function private.frahoosh_is_staff() from public;

grant execute on function private.frahoosh_current_role() to authenticated;
grant execute on function private.frahoosh_current_student_id() to authenticated;
grant execute on function private.frahoosh_current_teacher_id() to authenticated;
grant execute on function private.frahoosh_is_staff() to authenticated;
