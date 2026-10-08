-- Trigger functions do not need direct API EXECUTE privileges.
-- Keep certificate registration assignment available to PostgreSQL triggers only.
REVOKE EXECUTE ON FUNCTION public.frahoosh_assign_certificate_registration() FROM anon, authenticated;
