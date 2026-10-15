-- Daily schedule override and enforced teacher-first classroom entry.
alter table public.weekly_schedule_entries
  add column if not exists day_enabled boolean not null default true;

create or replace function public.set_weekly_schedule_day_enabled(p_weekday text, p_enabled boolean)
returns integer
language plpgsql security definer set search_path = ''
as $$
declare
  v_role text := lower(coalesce((select private.frahoosh_current_role()),''));
  v_count integer := 0;
  v_now timestamptz := now();
begin
  if v_role not in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی') then
    raise exception 'فقط مدیریت یا معاون آموزشی می‌تواند وضعیت همه کلاس‌های یک روز را تغییر دهد.';
  end if;
  if p_weekday not in ('0','1','2','3','4','5','6') then
    raise exception 'روز انتخاب‌شده معتبر نیست.';
  end if;
  update public.weekly_schedule_entries
    set day_enabled = p_enabled,
        activated_at = null,
        activated_by = coalesce((select auth.uid()::text),'management')
    where weekday = p_weekday;
  get diagnostics v_count = row_count;
  if not p_enabled then
    update public.online_class_sessions s set ended_at=v_now::text
    where nullif(btrim(coalesce(s.ended_at,'')),'') is null
      and exists(select 1 from public.weekly_schedule_entries w
                 where w.online_class_id=s.class_id and w.weekday=p_weekday and not w.day_enabled);
    update public.online_classes c
      set status='pending',start_at=null,end_at=null
      where exists(select 1 from public.weekly_schedule_entries w
                   where w.online_class_id=c.id and w.weekday=p_weekday and not w.day_enabled);
  end if;
  return v_count;
end;
$$;
revoke all on function public.set_weekly_schedule_day_enabled(text,boolean) from public,anon;
grant execute on function public.set_weekly_schedule_day_enabled(text,boolean) to authenticated;

create or replace function public.refresh_online_class_statuses()
returns void
language plpgsql
security definer
set search_path = public
as $function$
declare
  v_now timestamp with time zone := now();
  v_today date := (now() at time zone 'Asia/Tehran')::date;
  v_weekday text := extract(dow from (now() at time zone 'Asia/Tehran'))::integer::text;
  cids integer[];
begin
  update public.online_classes c
  set start_at = ((v_today + w.start_time) at time zone 'Asia/Tehran'),
      end_at = ((v_today + w.end_time) at time zone 'Asia/Tehran'),
      auto_activate = true,
      auto_close = true,
      status = case
        when v_now < ((v_today + w.start_time) at time zone 'Asia/Tehran') then 'pending'
        when v_now >= ((v_today + w.end_time) at time zone 'Asia/Tehran') then c.status
        else 'active'
      end
  from public.weekly_schedule_entries w
  where w.online_class_id = c.id and w.weekday = v_weekday
    and w.start_time is not null and w.end_time is not null and w.day_enabled;

  update public.weekly_schedule_entries w
  set activated_at = case
    when w.weekday = v_weekday
     and v_now >= ((v_today + w.start_time) at time zone 'Asia/Tehran')
     and v_now < ((v_today + w.end_time) at time zone 'Asia/Tehran')
    then coalesce(w.activated_at, v_now) else null end
  where w.start_time is not null and w.end_time is not null;

  update public.online_classes c
  set start_at = null, end_at = null,
      status = case when exists (
        select 1 from public.online_class_sessions s
        where s.class_id = c.id and nullif(btrim(coalesce(s.ended_at, '')), '') is null
      ) then 'active' else 'pending' end
  where exists (
    select 1 from public.weekly_schedule_entries w
    where w.online_class_id = c.id and w.start_time is not null and w.end_time is not null and w.day_enabled
  )
  and not exists (
    select 1 from public.weekly_schedule_entries w
    where w.online_class_id = c.id and w.weekday = v_weekday
      and w.start_time is not null and w.end_time is not null
  );

  select array_agg(id) into cids from public.online_classes
  where auto_close and end_at is not null and end_at <= v_now and status <> 'closed';
  update public.online_classes set status = 'closed'
  where auto_close and end_at is not null and end_at <= v_now;
  if cids is not null then
    update public.online_class_sessions set ended_at = v_now::text
    where class_id = any(cids) and nullif(btrim(coalesce(ended_at, '')), '') is null;
  end if;
  update public.online_classes set status = 'active'
  where auto_activate and start_at is not null and start_at <= v_now
    and (end_at is null or end_at > v_now) and status <> 'closed';
end;
$function$;

create or replace function public.start_online_class_session(p_class_id integer)
returns bigint
language plpgsql
security definer
set search_path to ''
as $function$
declare
  v_role text := lower(coalesce((select private.frahoosh_current_role()), ''));
  v_teacher_id integer := (select private.frahoosh_current_teacher_id());
  v_duration integer;
  v_session_id bigint;
  v_teacher_user_id uuid;
begin
  if not (
    v_role in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','executive','معاون اجرایی','معاونت اجرایی')
    or (v_role in ('teacher','دبیر') and exists (
      select 1 from public.online_class_teachers t
      where t.class_id = p_class_id and t.teacher_id = v_teacher_id
    ))
  ) then raise exception 'not authorized to start this class'; end if;

  if v_role in ('teacher','دبیر')
     and exists (select 1 from public.weekly_schedule_entries w
       where w.online_class_id = p_class_id and w.start_time is not null and w.end_time is not null)
     and not exists (select 1 from public.weekly_schedule_entries w
       where w.online_class_id = p_class_id
         and w.weekday = extract(dow from (now() at time zone 'Asia/Tehran'))::integer::text
         and w.start_time is not null and w.end_time is not null and w.day_enabled
         and (now() at time zone 'Asia/Tehran')::time >= w.start_time
         and (now() at time zone 'Asia/Tehran')::time < w.end_time)
  then raise exception 'ورود دبیر به این کلاس فقط در بازه زمانی زنگ برنامه هفتگی مجاز است.'; end if;

  select greatest(5, least(240, coalesce(c.duration,50))) into v_duration
  from public.online_classes c where c.id = p_class_id;
  if v_duration is null then raise exception 'class not found'; end if;

  if v_role in ('teacher','دبیر') then
    select a.auth_user_id into v_teacher_user_id
    from public.teachers t join public.account_settings a on a.national_code = t.national_code
    where t.id = v_teacher_id order by a.updated_at desc nulls last limit 1;
    v_teacher_user_id := coalesce(v_teacher_user_id, auth.uid());
  end if;

  select s.id into v_session_id from public.online_class_sessions s
  where s.class_id = p_class_id and coalesce(s.ended_at,'') = ''
  order by s.id desc limit 1;
  if v_session_id is not null then
    if v_teacher_user_id is not null then
      update public.online_class_sessions set teacher_user_id = v_teacher_user_id::text where id = v_session_id;
    end if;
    update public.online_classes set status = 'active', activated_at = coalesce(activated_at, now()),
      pages = 15, smart_board = 1, quiz = 1, camera = 1, microphone = 1, record = 1
    where id = p_class_id;
    return v_session_id;
  end if;

  insert into public.online_class_sessions
    (class_id, started_at, ended_at, created_at, duration_minutes, teacher_user_id)
  values (p_class_id, now()::text, null, now()::text, v_duration,
    case when v_teacher_user_id is null then null else v_teacher_user_id::text end)
  returning id into v_session_id;
  update public.online_classes set status = 'active', activated_at = now(), pages = 15,
    smart_board = 1, quiz = 1, camera = 1, microphone = 1, record = 1
  where id = p_class_id;
  return v_session_id;
end;
$function$;


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
  day_enabled boolean,
  activated_at timestamptz,
  active_session_id integer,
  active_session_started_at text
)
language sql stable security definer
set search_path = public, pg_temp
as $$
  select w.id,w.class_name,w.weekday,w.period,w.subject,w.teacher_name,
         w.online_class_id,w.start_time,w.end_time,w.day_enabled,w.activated_at,
         s.id,s.started_at
  from public.weekly_schedule_entries w
  left join lateral (
    select x.id,x.started_at
    from public.online_class_sessions x
    where x.class_id=w.online_class_id
      and nullif(btrim(coalesce(x.ended_at,'')),'') is null
      and nullif(btrim(coalesce(x.teacher_user_id,'')),'') is not null
    order by x.id desc limit 1
  ) s on true
  where p_weekday is null or w.weekday=p_weekday
  order by w.class_name,w.period,w.id;
$$;
revoke all on function public.get_student_class_schedule(text) from public;
grant execute on function public.get_student_class_schedule(text) to anon, authenticated;

