-- Production fix for national-code login and the six school test accounts.
create or replace function public.lookup_auth_emails_by_national_code(p_national_code text)
returns table(email text)
language sql
security definer
set search_path = public
stable
as $$
  select distinct trim(a.email)::text
  from public.account_settings a
  where regexp_replace(coalesce(a.national_code,''), '[^0-9]', '', 'g')
        = regexp_replace(coalesce(p_national_code,''), '[^0-9]', '', 'g')
    and trim(coalesce(a.email,'')) <> ''
  order by 1;
$$;
revoke all on function public.lookup_auth_emails_by_national_code(text) from public;
grant execute on function public.lookup_auth_emails_by_national_code(text) to anon, authenticated;

drop policy if exists account_settings_select_self on public.account_settings;
create policy account_settings_select_self
on public.account_settings for select to authenticated
using (lower(trim(coalesce(email,''))) = lower(trim(coalesce(auth.jwt() ->> 'email',''))));

drop policy if exists users_self_read on public.users;
create policy users_self_read
on public.users for select to authenticated
using (
  lower(username) = lower(coalesce(auth.jwt() ->> 'email',''))
  or exists (
    select 1 from public.account_settings a
    where lower(trim(coalesce(a.email,''))) = lower(trim(coalesce(auth.jwt() ->> 'email','')))
      and regexp_replace(coalesce(a.national_code,''),'[^0-9]','','g')
          = regexp_replace(coalesce(users.username,''),'[^0-9]','','g')
  )
);

-- Correct test-account roles/links.
update public.users set role='executive', display_name='امیرحسین زارعی', linked_staff_id=5, permissions='{"*":true}'::jsonb where username='1234567891';
update public.users set role='educational', display_name='محمدرضا صفی', linked_staff_id=6, permissions='{"*":true}'::jsonb where username='1234567892';
update public.users set role='cultural', display_name='عادل کلهر', linked_staff_id=7, permissions='{"*":true}'::jsonb where username='1234567893';
update public.users set role='teacher', display_name='رضا مردانه جهان تیغ', linked_teacher_id=2, permissions='{"*":true}'::jsonb where username='1234567894';
update public.users set role='student', display_name='حسن محمدی', linked_student_id=2, permissions='{"*":true}'::jsonb where username='1234567895';
update public.users set role='manager', display_name='حسن مردانه جهان تیغ', permissions='{"*":true}'::jsonb where username='0053409531';

update public.staff set role='معاون اجرایی', national_code='1234567891' where id=5;
update public.staff set role='معاون آموزشی', national_code='1234567892' where id=6;
update public.staff set role='معاون پرورشی', national_code='1234567893' where id=7;
update public.teachers set national_code='1234567894', email='reza.mardaneh@frahoosh.test' where id=2;
update public.students set national_code='1234567895', email='hassan.mohammadi@frahoosh.test' where id=2;
