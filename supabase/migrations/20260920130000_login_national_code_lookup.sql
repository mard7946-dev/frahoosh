-- Frahoosh: resolve a school national code to the matching Supabase Auth email.
-- The function is deliberately narrow: it returns one email only for an exact
-- national_code match and never exposes passwords or auth metadata.
create or replace function public.lookup_auth_email_by_national_code(p_national_code text)
returns text
language sql
security definer
set search_path = ''
stable
as $$
  select u.email
  from auth.users as u
  join public.account_settings as a
    on lower(trim(a.email)) = lower(trim(u.email))
  where regexp_replace(translate(coalesce(a.national_code, ''), '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'), '[^0-9]', '', 'g')
        = regexp_replace(translate(coalesce(p_national_code, ''), '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'), '[^0-9]', '', 'g')
    and regexp_replace(translate(coalesce(p_national_code, ''), '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'), '[^0-9]', '', 'g') <> ''
  limit 1;
$$;

revoke all on function public.lookup_auth_email_by_national_code(text) from public;
grant execute on function public.lookup_auth_email_by_national_code(text) to anon;
grant execute on function public.lookup_auth_email_by_national_code(text) to authenticated;
