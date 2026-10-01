-- Allow numeric login to resolve Auth email from account_settings before a
-- canonical public.users row exists. This is required during user onboarding.
create or replace function public.lookup_auth_emails_by_national_code(p_national_code text)
returns table(email text)
language sql
security definer
set search_path to 'public'
as $function$
  select distinct a.email::text
  from public.account_settings a
  where regexp_replace(coalesce(a.national_code, a.username, ''),'[^0-9]','','g')
        = regexp_replace(coalesce(p_national_code, ''),'[^0-9]','','g')
    and coalesce(a.email,'') <> ''
  order by a.email;
$function$;

grant execute on function public.lookup_auth_emails_by_national_code(text) to anon, authenticated;
