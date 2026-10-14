alter table public.weekly_schedule_entries
  add column if not exists start_time time without time zone,
  add column if not exists end_time time without time zone;

alter table public.weekly_schedule_entries
  drop constraint if exists weekly_schedule_entries_valid_bell_times;
alter table public.weekly_schedule_entries
  add constraint weekly_schedule_entries_valid_bell_times
  check (start_time is null or end_time is null or start_time < end_time);

create or replace function public.validate_weekly_schedule_bell_times()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.start_time is null or new.end_time is null then
    raise exception 'برای ثبت برنامه هفتگی باید ساعت شروع و پایان زنگ مشخص شود.';
  end if;
  if new.start_time >= new.end_time then
    raise exception 'ساعت پایان باید بعد از ساعت شروع باشد.';
  end if;
  if exists (
    select 1 from public.weekly_schedule_entries w
    where w.id is distinct from new.id
      and w.weekday = new.weekday
      and (
        (new.teacher_id is not null and w.teacher_id = new.teacher_id)
        or coalesce(nullif(btrim(w.class_name), ''), '') = coalesce(nullif(btrim(new.class_name), ''), '')
      )
      and w.start_time is not null and w.end_time is not null
      and new.start_time < w.end_time and w.start_time < new.end_time
  ) then
    raise exception 'این بازه زمانی با برنامه زنگ دیگری برای همین دبیر یا کلاس تداخل دارد.';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_validate_weekly_schedule_bell_times on public.weekly_schedule_entries;
create trigger trg_validate_weekly_schedule_bell_times
before insert or update of weekday, period, class_name, teacher_id, start_time, end_time
on public.weekly_schedule_entries
for each row execute function public.validate_weekly_schedule_bell_times();

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
    and w.start_time is not null and w.end_time is not null;

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
    where w.online_class_id = c.id and w.start_time is not null and w.end_time is not null
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
         and w.start_time is not null and w.end_time is not null
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
