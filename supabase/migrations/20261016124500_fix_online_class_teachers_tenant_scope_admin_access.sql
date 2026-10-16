-- The legacy restrictive tenant-scope policy omitted the platform-admin exception.
-- Restrictive policies are combined with AND, so this duplicate could block
-- valid inserts even when the tenant-boundary policy authorized the request.
-- Remove only the duplicate policy; tenant-boundary policies continue to enforce
-- school ownership, active subscription, and the explicit platform-admin exception.
DROP POLICY IF EXISTS frahoosh_tenant_scope ON public.online_class_teachers;
