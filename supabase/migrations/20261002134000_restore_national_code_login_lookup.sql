-- Restore the anonymous pre-auth lookup required to map a national code to its Auth email.
-- No password or session data is returned by this function.
grant execute on function public.lookup_auth_email_by_national_code(text) to anon, authenticated;
