-- Make online-class creation atomic: the RPC owns all initial class setup.
-- The mobile client no longer performs follow-up PATCH/INSERT calls that can fail
-- after the class row has already been created.
create or replace function public.create_online_class_with_members(
  p_teacher_id integer default null,
  p_subject text default null,
  p_grade text default null,
  p_class_name text default null,
  p_start_time text default null,
  p_end_time text default null,
  p_join_url text default null
)
returns integer
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_role text;
  v_class_id integer;
  v_teacher_name text := null;
  v_join_url text;
begin
  if auth.uid() is null then raise exception 'نشست کاربر معتبر نیست'; end if;
  v_role := lower(trim(coalesce(private.frahoosh_current_role(), '')));
  if v_role not in ('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی') then
    raise exception 'فقط مدیر و معاون اجرایی اجازه تشکیل کلاس آنلاین دارند';
  end if;
  if coalesce(trim(p_subject),'') = '' then raise exception 'نام درس الزامی است'; end if;
  if coalesce(trim(p_grade),'') = '' then raise exception 'پایه الزامی است'; end if;
  if coalesce(trim(p_class_name),'') = '' then raise exception 'نام کلاس الزامی است'; end if;

  if p_teacher_id is not null then
    select trim(coalesce(t.first_name,'') || ' ' || coalesce(t.last_name,''))
      into v_teacher_name
      from public.teachers t where t.id=p_teacher_id limit 1;
    if v_teacher_name is null or trim(v_teacher_name)='' then
      raise exception 'دبیر انتخاب‌شده در سامانه پیدا نشد';
    end if;
  end if;

  v_join_url := coalesce(nullif(trim(p_join_url),''), 'frahoosh://online-class/pending');

  insert into public.online_classes(
    title,subject,lesson,teacher,grade,class_name,duration,status,
    pages,record,smart_board,quiz,camera,microphone,
    start_time,end_time,start_time_shamsi,end_time_shamsi,
    activated_by,join_url,meeting_url
  ) values(
    trim(p_subject),trim(p_subject),trim(p_subject),v_teacher_name,
    trim(p_grade),trim(p_class_name),0,'inactive',
    15,1,1,1,1,1,
    p_start_time,p_end_time,p_start_time,p_end_time,
    coalesce(public.current_account_username(),''),v_join_url,v_join_url
  ) returning id into v_class_id;

  insert into public.online_class_settings(
    class_id,public_chat_enabled,private_chat_enabled,board_enabled,file_share_enabled,
    media_enabled,quiz_enabled,camera_enabled,microphone_enabled,screen_share_enabled,
    updated_at_shamsi
  ) values (
    v_class_id,1,1,1,1,1,1,1,1,1,
    to_char(now(),'YYYY-MM-DD HH24:MI')
  )
  on conflict (class_id) do update set
    public_chat_enabled=1, private_chat_enabled=1, board_enabled=1,
    file_share_enabled=1, media_enabled=1, quiz_enabled=1,
    camera_enabled=1, microphone_enabled=1, screen_share_enabled=1,
    updated_at_shamsi=excluded.updated_at_shamsi;

  if p_teacher_id is not null then
    insert into public.online_class_teachers(class_id,teacher_id,teacher_name)
    values(v_class_id,p_teacher_id,v_teacher_name)
    on conflict (class_id,teacher_id) do nothing;

    insert into public.online_class_students(class_id,student_id,student_name)
    select distinct v_class_id,s.id,trim(coalesce(s.first_name,'') || ' ' || coalesce(s.last_name,''))
    from public.teacher_classes tc
    join public.students s on s.class_name=tc.class_name and s.grade=tc.grade
    where tc.teacher_id=p_teacher_id and coalesce(tc.active,1)=1
    on conflict (class_id,student_id) do nothing;
  end if;

  return v_class_id;
end;
$function$;

revoke all on function public.create_online_class_with_members(integer,text,text,text,text,text,text) from public;
revoke all on function public.create_online_class_with_members(integer,text,text,text,text,text,text) from anon;
grant execute on function public.create_online_class_with_members(integer,text,text,text,text,text,text) to authenticated;
