-- Resolve the Auth email behind a national code without exposing account_settings rows.
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
