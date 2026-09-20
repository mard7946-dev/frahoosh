-- Frahoosh national-code login bridge for Supabase Auth.
-- Resolves a national code to the email used by Supabase Auth.
-- The function exposes only the matching email and performs no table writes.
create or replace function public.lookup_auth_email_by_national_code(p_national_code text)
returns text
language sql
security definer
set search_path = public
stable
as $$
  select a.email
  from public.account_settings a
  where regexp_replace(coalesce(a.national_code, ''), '[^0-9]', '', 'g') = regexp_replace(coalesce(p_national_code, ''), '[^0-9]', '', 'g')
  limit 1;
$$;

revoke all on function public.lookup_auth_email_by_national_code(text) from public;
grant execute on function public.lookup_auth_email_by_national_code(text) to anon, authenticated;
