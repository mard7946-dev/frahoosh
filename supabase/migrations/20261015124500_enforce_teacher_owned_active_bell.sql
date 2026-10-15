CREATE OR REPLACE FUNCTION public.start_online_class_session(p_class_id integer)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_role text := lower(coalesce((select private.frahoosh_current_role()), ''));
  v_teacher_id integer := (select private.frahoosh_current_teacher_id());
  v_duration integer;
  v_session_id bigint;
  v_teacher_user_id uuid;
begin
  /* FRAHOOSH_TENANT_SCOPE_GUARD */ if not exists(select 1 from public.online_classes c where c.id=p_class_id and c.tenant_school_id=private.frahoosh_current_school_id()) then raise exception 'کلاس متعلق به این مدرسه نیست یا پیدا نشد'; end if;
  
  if not (
    v_role in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','executive','معاون اجرایی','معاونت اجرایی')
    or (v_role in ('teacher','دبیر') and (
      exists (select 1 from public.online_class_teachers t
              where t.class_id = p_class_id and t.teacher_id = v_teacher_id)
      or exists (select 1 from public.weekly_schedule_entries w
                 where w.online_class_id = p_class_id and w.teacher_id = v_teacher_id)
    ))
  ) then raise exception 'not authorized to start this class'; end if;

  if v_role in ('teacher','دبیر') and not exists (
    select 1 from public.weekly_schedule_entries w
    where w.tenant_school_id = private.frahoosh_current_school_id()
      and w.online_class_id = p_class_id and w.teacher_id = v_teacher_id
      and w.weekday = extract(dow from (now() at time zone 'Asia/Tehran'))::integer::text
      and w.day_enabled and w.start_time is not null and w.end_time is not null
      and (now() at time zone 'Asia/Tehran')::time >= w.start_time
      and (now() at time zone 'Asia/Tehran')::time < w.end_time
  ) then raise exception 'ورود دبیر فقط در زنگ فعالِ اختصاص‌یافته به خود او مجاز است.'; end if;

  if exists (
    select 1 from public.weekly_schedule_entries w
    where w.online_class_id = p_class_id
      and w.weekday = extract(dow from (now() at time zone 'Asia/Tehran'))::integer::text
      and not w.day_enabled
  ) then raise exception 'کلاس‌های این روز توسط مدیریت غیرفعال شده‌اند.'; end if;

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
    update public.weekly_schedule_entries
      set activated_at = coalesce(activated_at, now())
      where online_class_id = p_class_id and day_enabled
        and weekday = extract(dow from (now() at time zone 'Asia/Tehran'))::integer::text
        and start_time is not null and end_time is not null
        and (now() at time zone 'Asia/Tehran')::time >= start_time
        and (now() at time zone 'Asia/Tehran')::time < end_time;
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
  update public.weekly_schedule_entries
    set activated_at = coalesce(activated_at, now())
    where online_class_id = p_class_id and day_enabled
      and weekday = extract(dow from (now() at time zone 'Asia/Tehran'))::integer::text
      and start_time is not null and end_time is not null
      and (now() at time zone 'Asia/Tehran')::time >= start_time
      and (now() at time zone 'Asia/Tehran')::time < end_time;
  return v_session_id;
end;
$function$
;
