-- Harden online class creation: authenticated management only, atomic class/member creation.
create or replace function public.create_online_class_with_members(
  p_teacher_id integer,
  p_subject text,
  p_start_time text,
  p_end_time text,
  p_join_url text default null
)
returns integer
language plpgsql
security definer
set search_path = public, private
as $function$
declare
  v_role text;
  v_teacher record;
  v_class_id integer;
begin
  if auth.uid() is null then
    raise exception 'نشست کاربر معتبر نیست';
  end if;
  v_role := lower(trim(coalesce(private.frahoosh_current_role(), '')));
  if v_role not in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','executive','معاون اجرایی','معاونت اجرایی') then
    raise exception 'فقط مدیر، معاون اجرایی و معاون آموزشی اجازه تشکیل کلاس آنلاین دارند';
  end if;
  select id, first_name, last_name, subject, grade, class_name into v_teacher
  from public.teachers where id = p_teacher_id limit 1;
  if v_teacher.id is null then raise exception 'دبیر انتخاب‌شده در سامانه پیدا نشد'; end if;
  insert into public.online_classes
    (title,subject,lesson,teacher,grade,class_name,duration,status,start_time,end_time,start_time_shamsi,end_time_shamsi,activated_by,join_url,meeting_url)
  values
    (coalesce(nullif(trim(p_subject),''),coalesce(v_teacher.subject,'')) || ' - ' || trim(coalesce(v_teacher.first_name,'') || ' ' || coalesce(v_teacher.last_name,'')),
     coalesce(nullif(trim(p_subject),''),coalesce(v_teacher.subject,'')),
     coalesce(nullif(trim(p_subject),''),coalesce(v_teacher.subject,'')),
     trim(coalesce(v_teacher.first_name,'') || ' ' || coalesce(v_teacher.last_name,'')),
     v_teacher.grade,v_teacher.class_name,0,'inactive',p_start_time,p_end_time,p_start_time,p_end_time,
     coalesce(public.current_account_username(),''),p_join_url,p_join_url)
  returning id into v_class_id;
  insert into public.online_class_teachers(class_id,teacher_id,teacher_name)
  values(v_class_id,v_teacher.id,trim(coalesce(v_teacher.first_name,'') || ' ' || coalesce(v_teacher.last_name,'')));
  insert into public.online_class_students(class_id,student_id,student_name)
  select distinct v_class_id,s.id,trim(coalesce(s.first_name,'') || ' ' || coalesce(s.last_name,''))
  from public.teacher_classes tc join public.students s on s.class_name=tc.class_name and s.grade=tc.grade
  where tc.teacher_id=v_teacher.id and coalesce(tc.active,1)=1
  on conflict (class_id,student_id) do nothing;
  return v_class_id;
end;
$function$;
revoke all on function public.create_online_class_with_members(integer,text,text,text,text) from public;
grant execute on function public.create_online_class_with_members(integer,text,text,text,text) to authenticated;