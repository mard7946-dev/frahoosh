-- Public login bridge: resolve a national code to the Auth email without exposing account rows.
CREATE OR REPLACE FUNCTION public.lookup_auth_emails_by_national_code(p_national_code text)
RETURNS TABLE(email text)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT a.email::text
  FROM public.account_settings a
  WHERE regexp_replace(coalesce(a.national_code, a.username, ''), '[^0-9]', '', 'g')
        = regexp_replace(coalesce(p_national_code, ''), '[^0-9]', '', 'g')
    AND coalesce(a.email, '') <> ''
  ORDER BY a.email;
$$;
GRANT EXECUTE ON FUNCTION public.lookup_auth_emails_by_national_code(text) TO anon, authenticated;