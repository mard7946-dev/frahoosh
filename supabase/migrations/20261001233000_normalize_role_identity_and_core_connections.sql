-- Normalize authenticated identity resolution and core cross-role RLS.
-- Auth identity is anchored by account_settings.auth_user_id; legacy users is fallback only.

create or replace function private.frahoosh_current_role()
returns text language sql stable security definer set search_path to ''
as $function$
  select coalesce(
    (select a.role from public.account_settings a where a.auth_user_id = auth.uid() limit 1),
    (select u.role from public.users u where lower(u.username)=lower(coalesce(auth.jwt()->>'email','')) limit 1),
    ''
  )
$function$;

create or replace function private.frahoosh_current_student_id()
returns bigint language sql stable security definer set search_path to ''
as $function$
  select coalesce(
    (select s.id from public.account_settings a join public.students s on s.national_code=a.national_code
      where a.auth_user_id=auth.uid() limit 1),
    (select u.linked_student_id from public.users u
      where lower(u.username)=lower(coalesce(auth.jwt()->>'email','')) limit 1)
  )
$function$;

create or replace function private.frahoosh_current_teacher_id()
returns bigint language sql stable security definer set search_path to ''
as $function$
  select coalesce(
    (select t.id from public.account_settings a join public.teachers t on t.national_code=a.national_code
      where a.auth_user_id=auth.uid() limit 1),
    (select u.linked_teacher_id from public.users u
      where lower(u.username)=lower(coalesce(auth.jwt()->>'email','')) limit 1)
  )
$function$;

create or replace function private.frahoosh_is_staff()
returns boolean language sql stable security definer set search_path to ''
as $function$
  select lower(coalesce(private.frahoosh_current_role(),'')) = any(array[
    'مدیر','مدیریت','manager','معاون آموزشی','educational',
    'معاون اجرایی','اجرایی','executive','معاون پرورشی','cultural',
    'مشاوره','counselor','advisor','دبیر','teacher'
  ])
$function$;

-- Core staff CRUD.
drop policy if exists "staff full access teachers" on public.teachers;
create policy "staff full access teachers" on public.teachers for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access teacher_classes" on public.teacher_classes;
create policy "staff full access teacher_classes" on public.teacher_classes for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access online_class_students" on public.online_class_students;
create policy "staff full access online_class_students" on public.online_class_students for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access online_class_teachers" on public.online_class_teachers;
create policy "staff full access online_class_teachers" on public.online_class_teachers for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access assignments" on public.assignments;
create policy "staff full access assignments" on public.assignments for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access attendance" on public.attendance;
create policy "staff full access attendance" on public.attendance for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access grades" on public.grades;
create policy "staff full access grades" on public.grades for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access student_grades" on public.student_grades;
create policy "staff full access student_grades" on public.student_grades for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access parent_meetings" on public.parent_meetings;
create policy "staff full access parent_meetings" on public.parent_meetings for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access teacher_parent_meetings" on public.teacher_parent_meetings;
create policy "staff full access teacher_parent_meetings" on public.teacher_parent_meetings for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access payment_records" on public.payment_records;
create policy "staff full access payment_records" on public.payment_records for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access teacher_exams" on public.teacher_exams;
create policy "staff full access teacher_exams" on public.teacher_exams for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));
drop policy if exists "staff full access online_classes" on public.online_classes;
create policy "staff full access online_classes" on public.online_classes for all to authenticated using ((select private.frahoosh_is_staff())) with check ((select private.frahoosh_is_staff()));

-- Student assignment submissions.
drop policy if exists "student assignment submissions insert" on public.assignment_submissions;
create policy "student assignment submissions insert" on public.assignment_submissions for insert to authenticated with check (student_id=(select private.frahoosh_current_student_id()));
drop policy if exists "student assignment submissions update" on public.assignment_submissions;
create policy "student assignment submissions update" on public.assignment_submissions for update to authenticated using (student_id=(select private.frahoosh_current_student_id())) with check (student_id=(select private.frahoosh_current_student_id()));
drop policy if exists "student assignment submissions delete" on public.assignment_submissions;
create policy "student assignment submissions delete" on public.assignment_submissions for delete to authenticated using (student_id=(select private.frahoosh_current_student_id()));

-- Parent visibility through parent_children.
drop policy if exists "parent read assignments" on public.assignments;
create policy "parent read assignments" on public.assignments for select to authenticated using (exists (select 1 from public.parent_children pc join public.account_settings a on lower(a.username)=lower(pc.parent_username) where pc.student_id=assignments.student_id and a.auth_user_id=(select auth.uid())));
drop policy if exists "parent read assignment submissions" on public.assignment_submissions;
create policy "parent read assignment submissions" on public.assignment_submissions for select to authenticated using (exists (select 1 from public.parent_children pc join public.account_settings a on lower(a.username)=lower(pc.parent_username) where pc.student_id=assignment_submissions.student_id and a.auth_user_id=(select auth.uid())));
drop policy if exists "parent read attendance" on public.attendance;
create policy "parent read attendance" on public.attendance for select to authenticated using (exists (select 1 from public.parent_children pc join public.account_settings a on lower(a.username)=lower(pc.parent_username) where pc.student_id=attendance.student_id and a.auth_user_id=(select auth.uid())));
drop policy if exists "parent read grades" on public.grades;
create policy "parent read grades" on public.grades for select to authenticated using (exists (select 1 from public.parent_children pc join public.account_settings a on lower(a.username)=lower(pc.parent_username) where pc.student_id=grades.student_id and a.auth_user_id=(select auth.uid())));
drop policy if exists "parent read student_grades" on public.student_grades;
create policy "parent read student_grades" on public.student_grades for select to authenticated using (exists (select 1 from public.parent_children pc join public.account_settings a on lower(a.username)=lower(pc.parent_username) where pc.student_id=student_grades.student_id and a.auth_user_id=(select auth.uid())));

-- Parent/student payment access for linked student records.
drop policy if exists "parent payment access" on public.payment_records;
create policy "parent payment access" on public.payment_records for all to authenticated
using (exists (select 1 from public.parent_children pc join public.account_settings a on lower(a.username)=lower(pc.parent_username)
  where pc.student_id=payment_records.student_id and lower(payment_records.parent_username)=lower(pc.parent_username) and a.auth_user_id=(select auth.uid())))
with check (exists (select 1 from public.parent_children pc join public.account_settings a on lower(a.username)=lower(pc.parent_username)
  where pc.student_id=payment_records.student_id and lower(payment_records.parent_username)=lower(pc.parent_username) and a.auth_user_id=(select auth.uid())));

drop policy if exists "student payment access" on public.payment_records;
create policy "student payment access" on public.payment_records for all to authenticated
using (student_id=(select private.frahoosh_current_student_id()))
with check (student_id=(select private.frahoosh_current_student_id()));

drop policy if exists "messages authenticated send" on public.messages;
create policy "messages authenticated send" on public.messages for insert to authenticated
with check (lower(coalesce(sender,''))=lower(coalesce(auth.jwt()->>'email','')));