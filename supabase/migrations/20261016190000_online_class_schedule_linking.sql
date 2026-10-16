-- Online classroom schedule linking support
alter table public.weekly_schedule_entries add column if not exists teacher_username text;

CREATE OR REPLACE FUNCTION private.frahoosh_weekday_number(p_weekday text)
 RETURNS text
 LANGUAGE sql
 IMMUTABLE
 SET search_path TO ''
AS $function$
  select case replace(replace(replace(regexp_replace(lower(trim(coalesce(p_weekday,''))), '[[:space:]]', '', 'g'), chr(8204), ''), 'ي', 'ی'), 'ك', 'ک')
    when 'شنبه' then '6'
    when 'یکشنبه' then '0'
    when 'دوشنبه' then '1'
    when 'سهشنبه' then '2'
    when 'چهارشنبه' then '3'
    when 'پنجشنبه' then '4'
    when 'جمعه' then '5'
    when '0' then '0' when '1' then '1' when '2' then '2'
    when '3' then '3' when '4' then '4' when '5' then '5' when '6' then '6'
    else trim(coalesce(p_weekday,''))
  end
$function$


CREATE OR REPLACE FUNCTION public.get_student_class_schedule(p_weekday text DEFAULT NULL::text)
 RETURNS TABLE(schedule_id bigint, class_name text, weekday text, period integer, subject text, teacher_name text, online_class_id integer, start_time time without time zone, end_time time without time zone, day_enabled boolean, activated_at timestamp with time zone, active_session_id integer, active_session_started_at text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
  select w.id,w.class_name,private.frahoosh_weekday_number(w.weekday),w.period,w.subject,
         w.teacher_name,w.online_class_id,w.start_time,w.end_time,w.day_enabled,w.activated_at,
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
  where w.tenant_school_id=private.frahoosh_current_school_id()
    and (p_weekday is null or private.frahoosh_weekday_number(w.weekday)=private.frahoosh_weekday_number(p_weekday))
  order by w.class_name,w.period,w.id;
$function$


CREATE OR REPLACE FUNCTION public.register_online_class_student_guest(p_class_id integer, p_session_id integer, p_display_name text, p_class_name text)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
declare
  v_uid uuid := auth.uid();
  v_name text := btrim(coalesce(p_display_name,''));
  v_class text := btrim(coalesce(p_class_name,''));
  v_school uuid;
  v_today text := extract(dow from (now() at time zone 'Asia/Tehran'))::integer::text;
  v_now time := (now() at time zone 'Asia/Tehran')::time;
begin
  select c.tenant_school_id into v_school from public.online_classes c where c.id=p_class_id;
  if v_school is null then raise exception 'مدرسهٔ کلاس مشخص نیست؛ کلاس باید به مدرسه متصل شود'; end if;
  if not exists(select 1 from public.online_classes c where c.id=p_class_id and c.tenant_school_id=v_school) then
    raise exception 'کلاس متعلق به این مدرسه نیست';
  end if;
  if private.frahoosh_current_school_id() is not null and private.frahoosh_current_school_id() <> v_school then
    raise exception 'کلاس متعلق به مدرسهٔ دیگری است';
  end if;
  if v_uid is null then raise exception 'ورود مهمان معتبر نیست'; end if;
  if v_name='' or v_class='' then raise exception 'نام دانش‌آموز و کلاس الزامی است'; end if;
  if not exists (
    select 1 from public.online_class_sessions s
    where s.id=p_session_id and s.class_id=p_class_id and coalesce(s.ended_at,'')=''
      and nullif(btrim(coalesce(s.teacher_user_id,'')),'') is not null
  ) then raise exception 'جلسه کلاس فعال نیست'; end if;
  if not exists (
    select 1 from public.weekly_schedule_entries w
    where w.tenant_school_id=v_school and w.online_class_id=p_class_id and w.activated_at is not null
      and w.day_enabled and private.frahoosh_weekday_number(w.weekday)=v_today
      and w.start_time is not null and w.end_time is not null
      and v_now>=w.start_time and v_now<w.end_time
      and replace(replace(regexp_replace(lower(btrim(coalesce(w.class_name,''))), '[[:space:]]', '', 'g'),'ي','ی'),'ك','ک')
        = replace(replace(regexp_replace(lower(v_class), '[[:space:]]', '', 'g'),'ي','ی'),'ك','ک')
  ) then raise exception 'این کلاس در برنامه هفتگیِ فعالِ همین زنگ ثبت نشده است'; end if;
  update public.guest_online_members set display_name=v_name,role='guest',left_at=null
    where class_id=p_class_id and user_id=v_uid;
  if not found then
    insert into public.guest_online_members(class_id,user_id,display_name,role) values(p_class_id,v_uid,v_name,'guest');
  end if;
  return true;
end;
$function$


CREATE OR REPLACE FUNCTION public.start_online_class_session(p_class_id integer)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_role text := lower(coalesce((select private.frahoosh_current_role()), ''));
  v_teacher_id integer := (select private.frahoosh_current_teacher_id());
  v_teacher_username text := (select lower(trim(a.username)) from public.account_settings a where a.auth_user_id=auth.uid() order by a.updated_at desc nulls last limit 1);
  v_duration integer;
  v_session_id bigint;
  v_teacher_user_id uuid;
  v_today text := extract(dow from (now() at time zone 'Asia/Tehran'))::integer::text;
  v_now time := (now() at time zone 'Asia/Tehran')::time;
begin
  if not exists(select 1 from public.online_classes c where c.id=p_class_id and c.tenant_school_id=private.frahoosh_current_school_id()) then
    raise exception 'کلاس متعلق به این مدرسه نیست یا پیدا نشد';
  end if;

  if not (
    v_role in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','executive','معاون اجرایی','معاونت اجرایی')
    or (v_role in ('teacher','دبیر') and (
      exists (select 1 from public.online_class_teachers t where t.class_id=p_class_id and t.teacher_id=v_teacher_id)
      or exists (select 1 from public.weekly_schedule_entries w where w.online_class_id=p_class_id and w.teacher_id=v_teacher_id)
      or exists (select 1 from public.weekly_schedule_entries w where w.online_class_id=p_class_id and lower(trim(coalesce(w.teacher_username,'')))=v_teacher_username and v_teacher_username is not null)
    ))
  ) then raise exception 'not authorized to start this class'; end if;

  if v_role in ('teacher','دبیر') and not exists (
    select 1 from public.weekly_schedule_entries w
    where w.tenant_school_id=private.frahoosh_current_school_id()
      and w.online_class_id=p_class_id
      and (w.teacher_id=v_teacher_id or (v_teacher_username is not null and lower(trim(coalesce(w.teacher_username,'')))=v_teacher_username))
      and private.frahoosh_weekday_number(w.weekday)=v_today
      and w.day_enabled and w.start_time is not null and w.end_time is not null
      and v_now>=w.start_time and v_now<w.end_time
  ) then raise exception 'ورود دبیر فقط در زنگ فعالِ اختصاص‌یافته به خود او مجاز است.'; end if;

  if exists (
    select 1 from public.weekly_schedule_entries w
    where w.tenant_school_id=private.frahoosh_current_school_id()
      and w.online_class_id=p_class_id
      and private.frahoosh_weekday_number(w.weekday)=v_today
      and not w.day_enabled
  ) then raise exception 'کلاس‌های این روز توسط مدیریت غیرفعال شده‌اند.'; end if;

  if v_role in ('teacher','دبیر')
     and exists (select 1 from public.weekly_schedule_entries w where w.online_class_id=p_class_id and w.start_time is not null and w.end_time is not null)
     and not exists (select 1 from public.weekly_schedule_entries w
       where w.tenant_school_id=private.frahoosh_current_school_id()
         and w.online_class_id=p_class_id
         and private.frahoosh_weekday_number(w.weekday)=v_today
         and w.start_time is not null and w.end_time is not null and w.day_enabled
         and v_now>=w.start_time and v_now<w.end_time)
  then raise exception 'ورود دبیر به این کلاس فقط در بازه زمانی زنگ برنامه هفتگی مجاز است.'; end if;

  select greatest(5,least(240,coalesce(c.duration,50))) into v_duration
  from public.online_classes c where c.id=p_class_id;
  if v_duration is null then raise exception 'class not found'; end if;

  if v_role in ('teacher','دبیر') then v_teacher_user_id:=auth.uid(); end if;

  select s.id into v_session_id from public.online_class_sessions s
  where s.class_id=p_class_id and coalesce(s.ended_at,'')=''
  order by s.id desc limit 1;

  if v_session_id is not null then
    if v_teacher_user_id is not null then
      update public.online_class_sessions set teacher_user_id=v_teacher_user_id::text where id=v_session_id;
    end if;
    update public.online_classes set status='active',activated_at=coalesce(activated_at,now()),
      pages=15,smart_board=1,quiz=1,camera=1,microphone=1,record=1 where id=p_class_id;
    update public.weekly_schedule_entries set activated_at=coalesce(activated_at,now())
    where tenant_school_id=private.frahoosh_current_school_id() and online_class_id=p_class_id and day_enabled
      and private.frahoosh_weekday_number(weekday)=v_today
      and start_time is not null and end_time is not null and v_now>=start_time and v_now<end_time;
    return v_session_id;
  end if;

  insert into public.online_class_sessions(class_id,started_at,ended_at,created_at,duration_minutes,teacher_user_id)
  values(p_class_id,now()::text,null,now()::text,v_duration,case when v_teacher_user_id is null then null else v_teacher_user_id::text end)
  returning id into v_session_id;

  update public.online_classes set status='active',activated_at=now(),pages=15,
    smart_board=1,quiz=1,camera=1,microphone=1,record=1 where id=p_class_id;

  update public.weekly_schedule_entries set activated_at=coalesce(activated_at,now())
  where tenant_school_id=private.frahoosh_current_school_id() and online_class_id=p_class_id and day_enabled
    and private.frahoosh_weekday_number(weekday)=v_today
    and start_time is not null and end_time is not null and v_now>=start_time and v_now<end_time;

  return v_session_id;
end;
$function$

