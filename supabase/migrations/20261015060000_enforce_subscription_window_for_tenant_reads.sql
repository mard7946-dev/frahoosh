-- Enforce subscription start and end dates at the database boundary.
CREATE OR REPLACE FUNCTION private.frahoosh_school_access_active(p_school_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO ''
AS $function$
  SELECT EXISTS (
    SELECT 1
    FROM public.school_subscriptions ss
    JOIN public.schools s ON s.id = ss.school_id
    WHERE ss.school_id = p_school_id
      AND s.status = 'active'
      AND ss.status IN ('active', 'past_due')
      AND now() >= ss.starts_at
      AND now() <= ss.ends_at + make_interval(days => ss.grace_days)
  );
$function$;

CREATE OR REPLACE FUNCTION private.frahoosh_enforce_student_limit()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''
AS $function$
DECLARE
  v_limit integer;
  v_count bigint;
BEGIN
  IF new.tenant_school_id IS NULL THEN
    RAISE EXCEPTION 'مدرسهٔ دانش‌آموز مشخص نیست.' USING errcode = '42501';
  END IF;

  SELECT ss.student_limit INTO v_limit
  FROM public.school_subscriptions ss
  WHERE ss.school_id = new.tenant_school_id
    AND ss.status IN ('active', 'past_due')
    AND now() >= ss.starts_at
    AND now() <= ss.ends_at + make_interval(days => ss.grace_days)
  ORDER BY ss.ends_at DESC
  LIMIT 1;

  IF v_limit IS NULL THEN
    RAISE EXCEPTION 'اشتراک فعال مدرسه وجود ندارد یا هنوز شروع نشده است.' USING errcode = '42501';
  END IF;

  SELECT count(*) INTO v_count
  FROM public.students s
  WHERE s.tenant_school_id = new.tenant_school_id
    AND (tg_op = 'INSERT' OR s.id IS DISTINCT FROM new.id);

  IF v_count >= v_limit THEN
    RAISE EXCEPTION 'ظرفیت اشتراک مدرسه تکمیل شده است (حداکثر % دانش‌آموز).', v_limit USING errcode = '23514';
  END IF;

  RETURN new;
END;
$function$;

-- Expired schools may read their own account/subscription metadata so the manager
-- can see renewal status, but cannot read operational tenant data until renewed.
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
    IF item.table_name = 'account_settings' THEN
      EXECUTE format(
        'CREATE POLICY frahoosh_tenant_boundary_select ON public.%I AS RESTRICTIVE FOR SELECT TO authenticated USING (tenant_school_id = private.frahoosh_current_school_id() OR private.frahoosh_is_platform_admin())',
        item.table_name
      );
    ELSE
      EXECUTE format(
        'CREATE POLICY frahoosh_tenant_boundary_select ON public.%I AS RESTRICTIVE FOR SELECT TO authenticated USING ((tenant_school_id = private.frahoosh_current_school_id() AND private.frahoosh_school_access_active(tenant_school_id)) OR private.frahoosh_is_platform_admin())',
        item.table_name
      );
    END IF;
  END LOOP;
END;
$$;
