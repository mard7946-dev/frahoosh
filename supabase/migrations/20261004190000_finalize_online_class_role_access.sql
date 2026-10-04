-- Final online-class authorization contract: only manager + executive may create/manage classes.
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
begin
  if auth.uid() is null then
    raise exception 'نشست کاربر معتبر نیست';
  end if;
  v_role := lower(trim(coalesce(private.frahoosh_current_role(), '')));
  if v_role not in ('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی') then
    raise exception 'فقط مدیر و معاون اجرایی اجازه تشکیل کلاس آنلاین دارند';
  end if;
  if coalesce(trim(p_subject),'') = '' then raise exception 'نام درس الزامی است'; end if;
  if coalesce(trim(p_grade),'') = '' then raise exception 'پایه الزامی است'; end if;
  if coalesce(trim(p_class_name),'') = '' then raise exception 'نام کلاس الزامی است'; end if;
  if p_teacher_id is not null then
    select trim(coalesce(t.first_name,'') || ' ' || coalesce(t.last_name,''))
      into v_teacher_name from public.teachers t where t.id=p_teacher_id limit 1;
    if v_teacher_name is null or trim(v_teacher_name)='' then
      raise exception 'دبیر انتخاب‌شده در سامانه پیدا نشد';
    end if;
  end if;
  insert into public.online_classes(
    title,subject,lesson,teacher,grade,class_name,duration,status,
    start_time,end_time,start_time_shamsi,end_time_shamsi,activated_by,join_url,meeting_url
  ) values(
    trim(p_subject),trim(p_subject),trim(p_subject),v_teacher_name,trim(p_grade),trim(p_class_name),
    0,'inactive',p_start_time,p_end_time,p_start_time,p_end_time,
    coalesce(public.current_account_username(),''),p_join_url,p_join_url
  ) returning id into v_class_id;
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

create or replace function public.activate_online_class(p_class_id integer)
returns boolean
language plpgsql
security definer
set search_path = ''
as $function$
begin
  if lower(coalesce(private.frahoosh_current_role(),'')) not in ('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی') then
    raise exception 'فقط مدیر و معاون اجرایی اجازه فعال‌سازی کلاس آنلاین دارند';
  end if;
  update public.online_classes
     set status='active',activated_by=coalesce(public.current_account_username(),''),activated_at=now()
   where id=p_class_id;
  return found;
end;
$function$;

revoke all on function public.activate_online_class(integer) from public;
revoke all on function public.activate_online_class(integer) from anon;
grant execute on function public.activate_online_class(integer) to authenticated;

drop policy if exists online_classes_management_full_access on public.online_classes;
drop policy if exists online_classes_update on public.online_classes;
drop policy if exists online_class_students_staff_full_access on public.online_class_students;
drop policy if exists "staff full access online_class_students" on public.online_class_students;
drop policy if exists "staff domain access online_class_students" on public.online_class_students;
drop policy if exists online_class_teachers_staff_full_access on public.online_class_teachers;
drop policy if exists "staff full access online_class_teachers" on public.online_class_teachers;

drop policy if exists manager_exec_crud_online_classes on public.online_classes;
create policy manager_exec_crud_online_classes on public.online_classes for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) in
('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'))
with check (lower(coalesce(private.frahoosh_current_role(),'')) in
('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'));

drop policy if exists educational_online_classes_read on public.online_classes;
create policy educational_online_classes_read on public.online_classes for select to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) in
('educational','معاون آموزشی','معاونت آموزشی'));

drop policy if exists manager_exec_crud_online_class_students on public.online_class_students;
create policy manager_exec_crud_online_class_students on public.online_class_students for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) in
('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'))
with check (lower(coalesce(private.frahoosh_current_role(),'')) in
('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'));

drop policy if exists manager_exec_crud_online_class_teachers on public.online_class_teachers;
create policy manager_exec_crud_online_class_teachers on public.online_class_teachers for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) in
('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'))
with check (lower(coalesce(private.frahoosh_current_role(),'')) in
('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی'));
