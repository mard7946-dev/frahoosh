-- Simplify online-class formation and restrict visibility to connected roles.
-- Manager/educational/executive manage classes; students and teachers only see
-- classes to which they are actually connected.

drop policy if exists "online_classes_authenticated_read" on public.online_classes;
drop policy if exists "online_classes_read" on public.online_classes;
drop policy if exists "online_classes_manage" on public.online_classes;
drop policy if exists "online_classes_manager_insert" on public.online_classes;
drop policy if exists "online_classes_manager_update" on public.online_classes;
drop policy if exists "staff full access online_classes" on public.online_classes;

create policy "online_classes_management_full_access"
on public.online_classes
for all to authenticated
using (
  (select private.frahoosh_current_role()) = any (
    array[
      'manager','مدیر','مدیریت',
      'educational','معاون آموزشی','معاونت آموزشی',
      'executive','معاون اجرایی','معاونت اجرایی'
    ]::text[]
  )
)
with check (
  (select private.frahoosh_current_role()) = any (
    array[
      'manager','مدیر','مدیریت',
      'educational','معاون آموزشی','معاونت آموزشی',
      'executive','معاون اجرایی','معاونت اجرایی'
    ]::text[]
  )
);

create policy "online_classes_student_linked_read"
on public.online_classes
for select to authenticated
using (
  exists (
    select 1
    from public.online_class_students ocs
    where ocs.class_id = online_classes.id
      and ocs.student_id = (select private.frahoosh_current_student_id())
  )
);

create policy "online_classes_teacher_linked_read"
on public.online_classes
for select to authenticated
using (
  exists (
    select 1
    from public.online_class_teachers oct
    where oct.class_id = online_classes.id
      and oct.teacher_id = (select private.frahoosh_current_teacher_id())
  )
);

drop policy if exists "online class students authenticated read" on public.online_class_students;
create policy "online_class_students_staff_full_access"
on public.online_class_students
for all to authenticated
using ((select private.frahoosh_is_staff()))
with check ((select private.frahoosh_is_staff()));

create policy "online_class_students_student_own_read"
on public.online_class_students
for select to authenticated
using (student_id = (select private.frahoosh_current_student_id()));

drop policy if exists "online class teachers authenticated read" on public.online_class_teachers;
create policy "online_class_teachers_staff_full_access"
on public.online_class_teachers
for all to authenticated
using ((select private.frahoosh_is_staff()))
with check ((select private.frahoosh_is_staff()));

create policy "online_class_teachers_teacher_own_read"
on public.online_class_teachers
for select to authenticated
using (teacher_id = (select private.frahoosh_current_teacher_id()));

create index if not exists idx_online_class_students_student_id
  on public.online_class_students using btree (student_id);

create index if not exists idx_online_class_teachers_teacher_id
  on public.online_class_teachers using btree (teacher_id);
