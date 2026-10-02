-- Allow the unauthenticated login bootstrap to resolve a national code to the
-- Auth email. The function itself is SECURITY DEFINER and returns only the
-- email mapped to the supplied national code/username.
grant execute on function public.lookup_auth_email_by_national_code(text) to anon;
grant execute on function public.lookup_auth_email_by_national_code(text) to authenticated;
