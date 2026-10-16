-- Manager-controlled daily activation for the public student timetable.
-- New schedule rows remain hidden from students until the manager enables that weekday.
ALTER TABLE public.weekly_schedule_entries
  ALTER COLUMN day_enabled SET DEFAULT false;

UPDATE public.weekly_schedule_entries
SET teacher_name = CASE
  WHEN teacher_name ILIKE '%حیدری%' THEN 'مسلم محمد زاده'
  WHEN teacher_name ILIKE '%ذولفقاری%' OR teacher_name ILIKE '%ذوالفقاری%' THEN 'عزیزاله حاجی زاده'
  ELSE teacher_name
END
WHERE teacher_name ILIKE '%حیدری%'
   OR teacher_name ILIKE '%ذولفقاری%'
   OR teacher_name ILIKE '%ذوالفقاری%';

CREATE OR REPLACE FUNCTION public.get_public_student_class_schedule(
  p_weekday text DEFAULT NULL::text,
  p_tenant_school_id uuid DEFAULT NULL::uuid
)
RETURNS TABLE(
  schedule_id bigint,
  class_name text,
  weekday text,
  period integer,
  subject text,
  teacher_name text,
  online_class_id integer,
  start_time time without time zone,
  end_time time without time zone,
  day_enabled boolean,
  activated_at timestamp with time zone,
  active_session_id integer,
  active_session_started_at text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO 'public', 'pg_temp'
AS $function$
  SELECT w.id,
         w.class_name,
         private.frahoosh_weekday_number(w.weekday),
         w.period,
         w.subject,
         w.teacher_name,
         w.online_class_id,
         w.start_time,
         w.end_time,
         w.day_enabled,
         w.activated_at,
         s.id,
         s.started_at
  FROM public.weekly_schedule_entries w
  LEFT JOIN LATERAL (
    SELECT x.id, x.started_at
    FROM public.online_class_sessions x
    WHERE x.class_id = w.online_class_id
      AND NULLIF(BTRIM(COALESCE(x.ended_at, '')), '') IS NULL
      AND NULLIF(BTRIM(COALESCE(x.teacher_user_id, '')), '') IS NOT NULL
    ORDER BY x.id DESC
    LIMIT 1
  ) s ON true
  WHERE p_tenant_school_id IS NOT NULL
    AND w.tenant_school_id = p_tenant_school_id
    AND w.day_enabled IS TRUE
    AND (
      p_weekday IS NULL
      OR private.frahoosh_weekday_number(w.weekday) = private.frahoosh_weekday_number(p_weekday)
    )
  ORDER BY w.class_name, w.period, w.id;
$function$;

GRANT EXECUTE ON FUNCTION public.get_public_student_class_schedule(text, uuid)
TO anon, authenticated;
