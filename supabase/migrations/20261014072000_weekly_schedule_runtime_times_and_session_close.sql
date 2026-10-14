-- Return bell times through the existing student schedule RPC so both web and APK can render the real schedule.
drop function if exists public.get_student_class_schedule(text);

create function public.get_student_class_schedule(p_weekday text default null)
returns table (
  schedule_id bigint,
  class_name text,
  weekday text,
  period integer,
  subject text,
  teacher_name text,
  online_class_id integer,
  start_time time without time zone,
  end_time time without time zone,
  activated_at timestamptz,
  active_session_id integer,
  active_session_started_at text
)
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select
    w.id,
    w.class_name,
    w.weekday,
    w.period,
    w.subject,
    w.teacher_name,
    w.online_class_id,
    w.start_time,
    w.end_time,
    w.activated_at,
    s.id,
    s.started_at
  from public.weekly_schedule_entries w
  left join lateral (
    select x.id, x.started_at
    from public.online_class_sessions x
    where x.class_id = w.online_class_id
      and nullif(btrim(coalesce(x.ended_at, '')), '') is null
    order by x.id desc
    limit 1
  ) s on true
  where p_weekday is null or w.weekday = p_weekday
  order by w.class_name, w.period, w.id;
$$;

revoke all on function public.get_student_class_schedule(text) from public;
grant execute on function public.get_student_class_schedule(text) to anon, authenticated;
