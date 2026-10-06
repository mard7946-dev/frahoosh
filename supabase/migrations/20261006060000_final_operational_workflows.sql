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
