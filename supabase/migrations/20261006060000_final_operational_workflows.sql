create or replace function public.create_online_class_with_members(
  p_teacher_id integer default null,
  p_subject text default null,
  p_grade text default null,
  p_class_name text default null,
  p_start_time text default null,
  p_end_time text default null,
  p_join_url text default null
) returns integer language plpgsql security definer set search_path='' as $$
declare v_role text; v_class_id integer; v_teacher_name text;
begin
  if auth.uid() is null then raise exception 'نشست کاربر معتبر نیست'; end if;
  v_role:=lower(trim(coalesce(private.frahoosh_current_role(),'')));
  if v_role not in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی') then raise exception 'فقط مدیر و معاون آموزشی اجازه تشکیل کلاس آنلاین دارند'; end if;
  if coalesce(trim(p_subject),'')='' then raise exception 'نام درس الزامی است'; end if;
  if coalesce(trim(p_grade),'')='' then raise exception 'پایه الزامی است'; end if;
  if coalesce(trim(p_class_name),'')='' then raise exception 'نام کلاس الزامی است'; end if;
  if p_teacher_id is not null then
    select trim(coalesce(first_name,'')||' '||coalesce(last_name,'')) into v_teacher_name from public.teachers where id=p_teacher_id limit 1;
    if coalesce(v_teacher_name,'')='' then raise exception 'دبیر انتخاب‌شده در سامانه پیدا نشد'; end if;
  end if;
  insert into public.online_classes(title,subject,lesson,teacher,grade,class_name,duration,status,start_time,end_time,start_time_shamsi,end_time_shamsi,activated_by,join_url,meeting_url)
  values(trim(p_subject),trim(p_subject),trim(p_subject),v_teacher_name,trim(p_grade),trim(p_class_name),0,'inactive',p_start_time,p_end_time,p_start_time,p_end_time,coalesce(public.current_account_username(),''),p_join_url,p_join_url)
  returning id into v_class_id;
  if p_teacher_id is not null then
    insert into public.online_class_teachers(class_id,teacher_id,teacher_name) values(v_class_id,p_teacher_id,v_teacher_name) on conflict(class_id,teacher_id) do nothing;
    insert into public.online_class_students(class_id,student_id,student_name)
    select distinct v_class_id,s.id,trim(coalesce(s.first_name,'')||' '||coalesce(s.last_name,'')) from public.teacher_classes tc join public.students s on s.class_name=tc.class_name and s.grade=tc.grade where tc.teacher_id=p_teacher_id and coalesce(tc.active,1)=1 on conflict(class_id,student_id) do nothing;
  end if;
  return v_class_id;
end $$;
revoke all on function public.create_online_class_with_members(integer,text,text,text,text,text,text) from public;
revoke all on function public.create_online_class_with_members(integer,text,text,text,text,text,text) from anon;
grant execute on function public.create_online_class_with_members(integer,text,text,text,text,text,text) to authenticated;

-- Final operational workflow contract for Android/Web clients.
alter table public.smart_board_content add column if not exists audience_type text default 'student_parent';
alter table public.smart_board_content add column if not exists active boolean default true;
alter table public.smart_board_content add column if not exists created_by text default '';

create or replace function public.activate_online_class(p_class_id integer)
returns boolean language plpgsql security definer set search_path='' as $$
begin
  if lower(coalesce(private.frahoosh_current_role(),'')) not in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی') then
    raise exception 'فقط مدیر و معاون آموزشی اجازه فعال‌سازی کلاس آنلاین دارند';
  end if;
  update public.online_classes set status='active', activated_by=coalesce(public.current_account_username(),''), activated_at=now() where id=p_class_id;
  return found;
end $$;

drop policy if exists manager_exec_crud_online_classes on public.online_classes;
drop policy if exists manager_educational_crud_online_classes on public.online_classes;
create policy manager_educational_crud_online_classes on public.online_classes for all to authenticated
using(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی'))
with check(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی'));

drop policy if exists manager_exec_crud_online_class_students on public.online_class_students;
drop policy if exists manager_educational_crud_online_class_students on public.online_class_students;
create policy manager_educational_crud_online_class_students on public.online_class_students for all to authenticated
using(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی'))
with check(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی'));

drop policy if exists manager_exec_crud_online_class_teachers on public.online_class_teachers;
drop policy if exists manager_educational_crud_online_class_teachers on public.online_class_teachers;
create policy manager_educational_crud_online_class_teachers on public.online_class_teachers for all to authenticated
using(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی'))
with check(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی'));

drop policy if exists manager_educational_crud_weekly_schedule on public.weekly_schedule;
create policy manager_educational_crud_weekly_schedule on public.weekly_schedule for all to authenticated
using(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی'))
with check(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی'));

drop policy if exists manager_educational_crud_exam_schedule on public.exam_schedule;
create policy manager_educational_crud_exam_schedule on public.exam_schedule for all to authenticated
using(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی'))
with check(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی'));

drop policy if exists counseling_staff_crud_records on public.counseling_records;
create policy counseling_staff_crud_records on public.counseling_records for all to authenticated
using(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','advisor','counselor','مشاور','مشاوره','educational','معاون آموزشی','معاونت آموزشی'))
with check(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','advisor','counselor','مشاور','مشاوره','educational','معاون آموزشی','معاونت آموزشی'));

drop policy if exists counseling_staff_crud_followups on public.counseling_followups;
create policy counseling_staff_crud_followups on public.counseling_followups for all to authenticated
using(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','advisor','counselor','مشاور','مشاوره','educational','معاون آموزشی','معاونت آموزشی'))
with check(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','advisor','counselor','مشاور','مشاوره','educational','معاون آموزشی','معاونت آموزشی'));

drop policy if exists counseling_staff_crud_guidance on public.counseling_guidance;
create policy counseling_staff_crud_guidance on public.counseling_guidance for all to authenticated
using(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','advisor','counselor','مشاور','مشاوره','educational','معاون آموزشی','معاونت آموزشی'))
with check(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','advisor','counselor','مشاور','مشاوره','educational','معاون آموزشی','معاونت آموزشی'));

drop policy if exists smart_board_schoolwide_read on public.smart_board_content;
create policy smart_board_schoolwide_read on public.smart_board_content for select to authenticated using(active=true);

drop policy if exists smart_board_schoolwide_staff_write on public.smart_board_content;
create policy smart_board_schoolwide_staff_write on public.smart_board_content for all to authenticated
using(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','cultural','معاون پرورشی','معاونت پرورشی','advisor','counselor','مشاور','مشاوره'))
with check(lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','cultural','معاون پرورشی','معاونت پرورشی','advisor','counselor','مشاور','مشاوره'));
