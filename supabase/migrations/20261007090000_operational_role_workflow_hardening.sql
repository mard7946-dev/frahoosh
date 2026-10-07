-- Operational role/workflow hardening for the legacy gtmm... production project.
-- These are additive policies; existing permissive policies remain intact.

create policy "frahoosh_grades_teacher_delete_scope"
on public.grades as permissive for delete to authenticated
using (
  teacher_id = private.frahoosh_current_teacher_id()
  and exists (
    select 1 from public.teacher_classes tc
    where tc.teacher_id = private.frahoosh_current_teacher_id()
      and lower(coalesce(tc.subject,'')) = lower(coalesce(grades.subject,''))
      and (coalesce(grades.class_name,'')='' or lower(coalesce(tc.class_name,''))=lower(coalesce(grades.class_name,'')))
      and coalesce(tc.active,1) <> 0
  )
);

create policy "frahoosh_grades_teacher_subject_guard"
on public.grades as restrictive for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) <> 'teacher'
  or (
    teacher_id = private.frahoosh_current_teacher_id()
    and exists (
      select 1 from public.teacher_classes tc
      where tc.teacher_id = private.frahoosh_current_teacher_id()
        and lower(coalesce(tc.subject,'')) = lower(coalesce(grades.subject,''))
        and (coalesce(grades.class_name,'')='' or lower(coalesce(tc.class_name,''))=lower(coalesce(grades.class_name,'')))
        and coalesce(tc.active,1) <> 0
    )
  )
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) <> 'teacher'
  or (
    teacher_id = private.frahoosh_current_teacher_id()
    and exists (
      select 1 from public.teacher_classes tc
      where tc.teacher_id = private.frahoosh_current_teacher_id()
        and lower(coalesce(tc.subject,'')) = lower(coalesce(grades.subject,''))
        and (coalesce(grades.class_name,'')='' or lower(coalesce(tc.class_name,''))=lower(coalesce(grades.class_name,'')))
        and coalesce(tc.active,1) <> 0
    )
  )
);

create policy "frahoosh_attendance_visibility_guard"
on public.attendance as restrictive for select to authenticated
using (
  private.frahoosh_is_staff()
  or approval_status = 'approved'
);

create policy "frahoosh_attendance_write_guard"
on public.attendance as restrictive for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','educational','executive')
  or (
    lower(coalesce(private.frahoosh_current_role(),'')) = 'teacher'
    and teacher_id = private.frahoosh_current_teacher_id()
    and approval_status <> 'approved'
  )
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','educational','executive')
  or (
    lower(coalesce(private.frahoosh_current_role(),'')) = 'teacher'
    and teacher_id = private.frahoosh_current_teacher_id()
    and approval_status <> 'approved'
  )
);

create policy "frahoosh_attendance_batch_workflow_guard"
on public.attendance_batches as restrictive for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','educational','executive')
  or (
    lower(coalesce(private.frahoosh_current_role(),'')) = 'teacher'
    and teacher_id = private.frahoosh_current_teacher_id()
    and status in ('pending','در انتظار تأیید','pending_approval')
  )
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','educational','executive')
  or (
    lower(coalesce(private.frahoosh_current_role(),'')) = 'teacher'
    and teacher_id = private.frahoosh_current_teacher_id()
    and status in ('pending','در انتظار تأیید','pending_approval')
  )
);

create policy "frahoosh_messages_sender_guard"
on public.messages as restrictive for insert to authenticated
with check (
  exists (
    select 1 from public.account_settings a
    where a.auth_user_id = auth.uid()
      and (
        lower(coalesce(a.username,'')) = lower(coalesce(messages.sender,''))
        or lower(coalesce(a.email,'')) = lower(coalesce(messages.sender,''))
        or lower(coalesce(a.national_code,'')) = lower(coalesce(messages.sender,''))
      )
  )
  and private.frahoosh_can_message_target(receiver)
);

create index if not exists idx_grades_teacher_subject_class
  on public.grades (teacher_id, subject, class_name);
create index if not exists idx_attendance_student_approval
  on public.attendance (student_id, approval_status);
create index if not exists idx_attendance_batch_teacher_status
  on public.attendance_batches (teacher_id, status);
create index if not exists idx_weekly_schedule_entries_class_day_period
  on public.weekly_schedule_entries (class_name, weekday, period);
create index if not exists idx_messages_sender_receiver
  on public.messages (sender, receiver);
