-- Prevent accidental reassignment of an account already owned by another tenant.
-- Applied to Supabase project gtmmllcxhdejwjjnyzrh as migration 20261015080825.
CREATE OR REPLACE FUNCTION public.platform_admin_create_school_subscription(
  p_school_name text,
  p_slug text,
  p_school_code text,
  p_owner_email text,
  p_plan_id uuid,
  p_payment_reference text DEFAULT NULL
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
DECLARE
  v_owner record;
  v_plan public.subscription_plans;
  v_school_id uuid;
  v_start timestamptz := now();
BEGIN
  IF auth.uid() IS NULL OR NOT private.frahoosh_is_platform_admin() THEN
    RAISE EXCEPTION 'فقط مدیر کل فراهوش مجاز به ایجاد مدرسه و اشتراک است.' USING errcode = '42501';
  END IF;
  IF nullif(btrim(p_school_name), '') IS NULL THEN
    RAISE EXCEPTION 'نام مدرسه الزامی است.' USING errcode = '23514';
  END IF;
  IF p_slug IS NULL OR lower(btrim(p_slug)) !~ '^[a-z0-9]+([.-][a-z0-9]+)*$' THEN
    RAISE EXCEPTION 'شناسه مدرسه باید انگلیسی و شامل حروف کوچک، عدد و خط تیره باشد.' USING errcode = '23514';
  END IF;
  IF nullif(btrim(p_owner_email), '') IS NULL THEN
    RAISE EXCEPTION 'رایانامه حساب مدیر مدرسه الزامی است.' USING errcode = '23514';
  END IF;

  SELECT a.auth_user_id, a.role, a.username, a.tenant_school_id,
         coalesce(u.email, a.email) AS owner_email
    INTO v_owner
    FROM public.account_settings a
    LEFT JOIN auth.users u ON u.id = a.auth_user_id
   WHERE a.auth_user_id IS NOT NULL
     AND (
       lower(coalesce(u.email, a.email, '')) = lower(btrim(p_owner_email))
       OR lower(a.username) = lower(btrim(p_owner_email))
     )
   ORDER BY a.updated_at DESC NULLS LAST
   LIMIT 1;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'حساب مدیر مدرسه پیدا نشد؛ ابتدا حساب کاربری او را بسازید.' USING errcode = 'P0002';
  END IF;
  IF lower(coalesce(v_owner.role,'')) NOT IN ('manager','مدیر','مدیریت','مدیر مدرسه','principal','administrator','admin') THEN
    RAISE EXCEPTION 'حساب انتخاب‌شده نقش مدیریت مدرسه ندارد.' USING errcode = '23514';
  END IF;
  IF v_owner.tenant_school_id IS NOT NULL
     AND v_owner.tenant_school_id <> (SELECT id FROM public.schools WHERE slug='frahoosh-default' LIMIT 1) THEN
    RAISE EXCEPTION 'این حساب از قبل به مدرسهٔ دیگری متصل است؛ برای جلوگیری از انتقال ناخواسته، حساب مدیر یکتای همان مدرسه را وارد کنید.' USING errcode = '23514';
  END IF;

  SELECT * INTO v_plan
    FROM public.subscription_plans
   WHERE id = p_plan_id AND is_active = true;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'طرح اشتراک معتبر یا فعال نیست.' USING errcode = 'P0002';
  END IF;
  IF v_plan.price_irr <= 0 THEN
    RAISE EXCEPTION 'قیمت طرح هنوز ثبت نشده است؛ ابتدا قیمت را در مدیریت طرح‌ها تعیین کنید.' USING errcode = '23514';
  END IF;

  INSERT INTO public.schools(slug, name, school_code, owner_auth_user_id, status)
  VALUES(lower(btrim(p_slug)), btrim(p_school_name), nullif(btrim(coalesce(p_school_code,'')),''), v_owner.auth_user_id, 'active')
  RETURNING id INTO v_school_id;

  UPDATE public.account_settings
     SET tenant_school_id = v_school_id, updated_at = now()
   WHERE auth_user_id = v_owner.auth_user_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'اتصال حساب مدیر مدرسه به مدرسه جدید انجام نشد.' USING errcode = 'P0002';
  END IF;

  INSERT INTO public.school_subscriptions(
    school_id, plan_id, duration_months, student_min, student_limit, price_irr,
    starts_at, ends_at, grace_days, status, payment_reference, created_by
  )
  VALUES(
    v_school_id, v_plan.id, v_plan.duration_months, v_plan.student_min, v_plan.student_limit, v_plan.price_irr,
    v_start, v_start + make_interval(months => v_plan.duration_months), 0, 'active',
    nullif(btrim(coalesce(p_payment_reference,'')),''), auth.uid()
  );

  RETURN v_school_id;
END;
$function$;

REVOKE ALL ON FUNCTION public.platform_admin_create_school_subscription(text,text,text,text,uuid,text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.platform_admin_create_school_subscription(text,text,text,text,uuid,text) TO authenticated;
