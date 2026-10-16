-- The original tenant-scope policy predates the tenant-boundary policy and
-- omitted its platform-admin exception. PostgreSQL combines restrictive
-- policies with AND, so it could reject inserts even when the newer boundary
-- policy correctly authorized a platform administrator.
--
-- Remove only the duplicate restrictive policy from these two tables. The
-- tenant-boundary policies remain restrictive and continue to enforce school
-- ownership, active subscription, and the explicit platform-admin exception.
DROP POLICY IF EXISTS frahoosh_tenant_scope ON public.online_classes;
DROP POLICY IF EXISTS frahoosh_tenant_scope ON public.teachers;
