-- Harden auth-email lookup: it must never be callable anonymously.
revoke execute on function public.lookup_auth_email_by_national_code(text) from anon;
