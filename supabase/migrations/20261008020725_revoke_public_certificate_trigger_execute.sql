-- Trigger functions do not need direct API EXECUTE privileges.
REVOKE EXECUTE ON FUNCTION public.frahoosh_assign_certificate_registration() FROM PUBLIC, anon, authenticated;
