-- Enforce tenant isolation and subscription activity as restrictive policies.
-- Restrictive policies are ANDed with existing role-specific policies, preventing
-- legacy permissive manager policies from bypassing tenant boundaries.
DO $$
DECLARE
  item record;
BEGIN
  FOR item IN
    SELECT DISTINCT c.table_name
    FROM information_schema.columns c
    JOIN pg_class pc ON pc.relname = c.table_name
    JOIN pg_namespace pn ON pn.oid = pc.relnamespace AND pn.nspname = 'public'
    WHERE c.table_schema = 'public'
      AND c.column_name = 'tenant_school_id'
      AND pc.relkind IN ('r', 'p')
      AND pc.relrowsecurity
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS frahoosh_tenant_boundary_select ON public.%I', item.table_name);
    EXECUTE format('DROP POLICY IF EXISTS frahoosh_tenant_boundary_insert ON public.%I', item.table_name);
    EXECUTE format('DROP POLICY IF EXISTS frahoosh_tenant_boundary_update ON public.%I', item.table_name);
    EXECUTE format('DROP POLICY IF EXISTS frahoosh_tenant_boundary_delete ON public.%I', item.table_name);

    EXECUTE format(
      'CREATE POLICY frahoosh_tenant_boundary_select ON public.%I AS RESTRICTIVE FOR SELECT TO authenticated USING (tenant_school_id = private.frahoosh_current_school_id() OR private.frahoosh_is_platform_admin())',
      item.table_name
    );
    EXECUTE format(
      'CREATE POLICY frahoosh_tenant_boundary_insert ON public.%I AS RESTRICTIVE FOR INSERT TO authenticated WITH CHECK ((tenant_school_id = private.frahoosh_current_school_id() AND private.frahoosh_school_access_active(tenant_school_id)) OR private.frahoosh_is_platform_admin())',
      item.table_name
    );
    EXECUTE format(
      'CREATE POLICY frahoosh_tenant_boundary_update ON public.%I AS RESTRICTIVE FOR UPDATE TO authenticated USING ((tenant_school_id = private.frahoosh_current_school_id() AND private.frahoosh_school_access_active(tenant_school_id)) OR private.frahoosh_is_platform_admin()) WITH CHECK ((tenant_school_id = private.frahoosh_current_school_id() AND private.frahoosh_school_access_active(tenant_school_id)) OR private.frahoosh_is_platform_admin())',
      item.table_name
    );
    EXECUTE format(
      'CREATE POLICY frahoosh_tenant_boundary_delete ON public.%I AS RESTRICTIVE FOR DELETE TO authenticated USING ((tenant_school_id = private.frahoosh_current_school_id() AND private.frahoosh_school_access_active(tenant_school_id)) OR private.frahoosh_is_platform_admin())',
      item.table_name
    );
  END LOOP;
END;
$$;
