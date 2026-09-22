-- Frahoosh: student/parent direct messaging permissions.
-- Students and parents may send direct messages to school staff; recipients
-- can read only messages addressed to their identity or sent by them.

create or replace function private.frahoosh_current_username()
returns text
language sql stable security definer set search_path=''
as $$
  select coalesce(
    (
      select nullif(trim(coalesce(u.username, a.username, a.email, a.national_code)), '')
      from public.users u
      full join public.account_settings a
        on lower(coalesce(a.email,'')) = lower(coalesce(auth.jwt()->>'email',''))
        or lower(coalesce(a.username,'')) = lower(coalesce(auth.jwt()->>'email',''))
      where lower(coalesce(u.username,'')) = lower(coalesce(auth.jwt()->>'email',''))
         or lower(coalesce(a.email,'')) = lower(coalesce(auth.jwt()->>'email',''))
         or lower(coalesce(a.username,'')) = lower(coalesce(auth.jwt()->>'email',''))
         or lower(coalesce(u.username,'')) = lower(coalesce(a.national_code,''))

      order by case
        when lower(coalesce(u.username,'')) = lower(coalesce(auth.jwt()->>'email','')) then 0
        when lower(coalesce(a.email,'')) = lower(coalesce(auth.jwt()->>'email','')) then 1
        else 2
      end
      limit 1
    ),
    nullif(trim(coalesce(auth.jwt()->>'email','')), '')
  )
$$;

-- Keep existing staff/manager policies intact; these policies only add the
-- student/parent side of the direct-message workflow.
drop policy if exists frahoosh_student_parent_message_insert on public.messages;
create policy frahoosh_student_parent_message_insert on public.messages
  for insert to authenticated
  with check (
    lower(coalesce(private.frahoosh_current_role(),'')) = any(array[
      'student','دانش‌آموز','parent','parents','ولی','اولیا'
    ])
    and lower(coalesce(sender,'')) = lower(coalesce(private.frahoosh_current_username(),''))
  );

drop policy if exists frahoosh_message_owner_read on public.messages;
create policy frahoosh_message_owner_read on public.messages
  for select to authenticated
  using (
    lower(coalesce(sender,'')) = lower(coalesce(private.frahoosh_current_username(),''))
    or lower(coalesce(receiver,'')) = lower(coalesce(private.frahoosh_current_username(),''))
    or lower(coalesce(target_name,'')) = lower(coalesce(private.frahoosh_current_username(),''))
    or (select private.frahoosh_is_staff())
  );

drop policy if exists frahoosh_student_parent_target_insert on public.message_targets;
create policy frahoosh_student_parent_target_insert on public.message_targets
  for insert to authenticated
  with check (
    (select private.frahoosh_is_staff())
    or exists (
      select 1
      from public.messages m
      where m.id = message_targets.message_id
        and lower(coalesce(m.sender,'')) = lower(coalesce(private.frahoosh_current_username(),''))
    )
  );

drop policy if exists frahoosh_message_read_insert on public.message_reads;
create policy frahoosh_message_read_insert on public.message_reads
  for insert to authenticated
  with check (
    lower(coalesce(username,'')) = lower(coalesce(private.frahoosh_current_username(),''))
    and exists (
      select 1
      from public.messages m
      where m.id = message_reads.message_id
        and (
          lower(coalesce(m.receiver,'')) = lower(coalesce(private.frahoosh_current_username(),''))
          or lower(coalesce(m.target_name,'')) = lower(coalesce(private.frahoosh_current_username(),''))
        )
    )
  );

drop policy if exists frahoosh_message_read_update on public.message_reads;
create policy frahoosh_message_read_update on public.message_reads
  for update to authenticated
  using (lower(coalesce(username,'')) = lower(coalesce(private.frahoosh_current_username(),''))
  )
  with check (lower(coalesce(username,'')) = lower(coalesce(private.frahoosh_current_username(),''))
  );

grant select, insert, update, delete on table public.messages, public.message_targets, public.message_reads to authenticated;


-- The recipient dropdown needs a safe staff directory. The users table contains
-- no password/secret field; students and parents can see only school-staff roles.
drop policy if exists frahoosh_student_parent_staff_directory on public.users;
create policy frahoosh_student_parent_staff_directory on public.users
  for select to authenticated
  using (
    (select private.frahoosh_is_staff())
    or (
      lower(coalesce(private.frahoosh_current_role(),'')) = any(array[
        'student','دانش‌آموز','parent','parents','ولی','اولیا'
      ])
      and lower(coalesce(role,'')) = any(array[
        'manager','admin','مدیر','مدیریت',
        'educational','معاون آموزشی',
        'executive','معاون اجرایی',
        'cultural','معاون پرورشی',
        'advisor','counselor','مشاور',
        'teacher','دبیر','معلم'
      ])
    )
  );
