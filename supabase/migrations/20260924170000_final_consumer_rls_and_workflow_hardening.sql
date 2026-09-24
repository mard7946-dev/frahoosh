-- Frahoosh final consumer security + workflow hardening.
-- Student/parent UI restrictions are enforced again at the database boundary.
-- Staff roles keep operational access; consumer roles get only their explicitly
-- approved writes.

alter table if exists public.meeting_requests
  add column if not exists title text;

do $$
declare
  t text;
begin
  foreach t in array array[
    'students','teachers','staff','teacher_classes','attendance','grades','student_grades',
    'assignments','discipline_records','educational_followups','academic_followups',
    'teacher_exams','quiz_questions','online_classes','online_class_sessions',
    'online_class_students','online_class_teachers','smart_board_whiteboards',
    'meeting_requests','school_events','report_cards','weekly_schedule','exam_schedule',
    'finance_accounts','finance_transactions','finance_donations','payment_offers',
    'payment_attempts','payment_records','payment_transactions','certificate_requests',
    'archive_items','assets','student_cards','class_cards','class_seat_assignments',
    'exam_seat_assignments','parent_children','parents','message_targets','message_reads',
    'account_settings','messages','assignment_submissions'
  ] loop
    if to_regclass('public.'||t) is not null then
      alter table public."||t||" enable row level security;
    end if;
  end loop;
end $$;

-- Remove the earlier blanket authenticated policies on consumer-sensitive tables.
do $$
declare
  t text;
begin
  foreach t in array array[
    'students','teachers','staff','teacher_classes','attendance','grades','student_grades',
    'assignments','discipline_records','educational_followups','academic_followups',
    'teacher_exams','quiz_questions','online_classes','online_class_sessions',
    'online_class_students','online_class_teachers','smart_board_whiteboards',
    'meeting_requests','school_events','report_cards','weekly_schedule','exam_schedule',
    'finance_accounts','finance_transactions','finance_donations','payment_offers',
    'payment_attempts','payment_records','payment_transactions','certificate_requests',
    'archive_items','assets','student_cards','class_cards','class_seat_assignments',
    'exam_seat_assignments','parent_children','parents','message_targets','message_reads',
    'account_settings','messages','assignment_submissions'
  ] loop
    if to_regclass('public.'||t) is not null then
      execute format('drop policy if exists frahoosh_authenticated_all on public.%I',t);
      execute format('drop policy if exists frahoosh_authenticated_operational on public.%I',t);
      execute format('drop policy if exists frahoosh_manager_operational_write on public.%I',t);
    end if;
  end loop;
end $$;

-- Staff keep operational access. Student/parent never satisfy this predicate.
do $$
declare
  t text;
begin
  foreach t in array array[
    'students','teachers','staff','teacher_classes','attendance','grades','student_grades',
    'assignments','discipline_records','educational_followups','academic_followups',
    'teacher_exams','quiz_questions','online_classes','online_class_sessions',
    'online_class_students','online_class_teachers','smart_board_whiteboards',
    'meeting_requests','school_events','report_cards','weekly_schedule','exam_schedule',
    'finance_accounts','finance_transactions','finance_donations','payment_offers',
    'payment_attempts','payment_records','payment_transactions','certificate_requests',
    'archive_items','assets','student_cards','class_cards','class_seat_assignments',
    'exam_seat_assignments','parent_children','parents','message_targets','message_reads',
    'account_settings','messages','assignment_submissions'
  ] loop
    if to_regclass('public.'||t) is not null then
      execute format(
        'create policy frahoosh_staff_full on public.%I for all to authenticated
         using (coalesce((select private.frahoosh_current_role()),'''') not in (''student'',''parent'',''دانش‌آموز'',''ولی'',''اولیا''))
         with check (coalesce((select private.frahoosh_current_role()),'''') not in (''student'',''parent'',''دانش‌آموز'',''ولی'',''اولیا''))',t);
    end if;
  end loop;
end $$;

-- Consumer read access: student/parent can see data already exposed by their
-- panels, while staff remain governed by the staff policy above.
do $$
declare t text;
begin
  foreach t in array array[
    'students','teachers','staff','teacher_classes','attendance','grades','student_grades',
    'assignments','discipline_records','educational_followups','academic_followups',
    'teacher_exams','quiz_questions','online_classes','online_class_sessions',
    'online_class_students','online_class_teachers','smart_board_whiteboards',
    'meeting_requests','school_events','report_cards','weekly_schedule','exam_schedule',
    'finance_accounts','finance_transactions','finance_donations','payment_offers',
    'payment_records','payment_transactions','certificate_requests','archive_items',
    'assets','student_cards','class_cards','class_seat_assignments','exam_seat_assignments',
    'parent_children','parents','message_targets','message_reads','messages',
    'assignment_submissions'
  ] loop
    if to_regclass('public.'||t) is not null then
      execute format(
        'create policy frahoosh_consumer_read on public.%I for select to authenticated
         using ((select private.frahoosh_current_role()) in (''student'',''parent'',''دانش‌آموز'',''ولی'',''اولیا''))',t);
    end if;
  end loop;
end $$;

-- Student assignment submission: only the currently authenticated student's own rows.
drop policy if exists frahoosh_student_submission_insert on public.assignment_submissions;
create policy frahoosh_student_submission_insert on public.assignment_submissions
for insert to authenticated
with check (
  (select private.frahoosh_current_role()) in ('student','دانش‌آموز')
  and student_id=(select private.frahoosh_current_student_id())
);

drop policy if exists frahoosh_student_submission_update on public.assignment_submissions;
create policy frahoosh_student_submission_update on public.assignment_submissions
for update to authenticated
using (
  (select private.frahoosh_current_role()) in ('student','دانش‌آموز')
  and student_id=(select private.frahoosh_current_student_id())
)
with check (
  (select private.frahoosh_current_role()) in ('student','دانش‌آموز')
  and student_id=(select private.frahoosh_current_student_id())
);

drop policy if exists frahoosh_student_submission_delete on public.assignment_submissions;
create policy frahoosh_student_submission_delete on public.assignment_submissions
for delete to authenticated
using (
  (select private.frahoosh_current_role()) in ('student','دانش‌آموز')
  and student_id=(select private.frahoosh_current_student_id())
);

-- Student/parent direct messaging: sender must belong to the authenticated identity.
drop policy if exists frahoosh_consumer_message_insert on public.messages;
create policy frahoosh_consumer_message_insert on public.messages
for insert to authenticated
with check (
  (select private.frahoosh_current_role()) in ('student','parent','دانش‌آموز','ولی','اولیا')
  and (
    sender_user_id=auth.uid()
    or lower(coalesce(sender,''))=lower(coalesce(auth.jwt()->>'email',''))
    or lower(coalesce(sender,'')) in (
      select lower(coalesce(a.username,'')) from public.account_settings a
      where lower(coalesce(a.email,''))=lower(coalesce(auth.jwt()->>'email',''))
      union
      select lower(coalesce(a.national_code,'')) from public.account_settings a
      where lower(coalesce(a.email,''))=lower(coalesce(auth.jwt()->>'email',''))
    )
  )
);

-- Parent payment requests: only the parent's linked children may be selected.
drop policy if exists frahoosh_parent_payment_insert on public.payment_attempts;
create policy frahoosh_parent_payment_insert on public.payment_attempts
for insert to authenticated
with check (
  (select private.frahoosh_current_role()) in ('parent','ولی','اولیا')
  and lower(coalesce(payer_username,'')) in (
    lower(coalesce(auth.jwt()->>'email','')),
    select lower(coalesce(a.username,'')) from public.account_settings a
      where lower(coalesce(a.email,''))=lower(coalesce(auth.jwt()->>'email',''))
  )
  and exists (
    select 1 from public.parent_children pc
    where pc.student_id=payment_attempts.student_id
      and lower(coalesce(pc.parent_username,'')) in (
        lower(coalesce(auth.jwt()->>'email','')),
        select lower(coalesce(a.username,'')) from public.account_settings a
          where lower(coalesce(a.email,''))=lower(coalesce(auth.jwt()->>'email',''))
      )
  )
);

-- Prevent consumers from changing payment results or school configuration.
drop policy if exists frahoosh_consumer_payment_update on public.payment_attempts;
drop policy if exists frahoosh_consumer_payment_delete on public.payment_attempts;
drop policy if exists frahoosh_consumer_payment_record_insert on public.payment_records;

-- Online class membership is staff-managed only; students/parents are readers.
-- Likewise exam authoring, grades, attendance and disciplinary records remain staff-owned.
