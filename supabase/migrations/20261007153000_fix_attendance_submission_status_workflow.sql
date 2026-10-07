-- Keep attendance submission state aligned with the production check constraint.
-- Teachers submit a batch as "submitted"; management/deputies approve it.
drop policy if exists "frahoosh_attendance_batch_workflow_guard" on public.attendance_batches;
create policy "frahoosh_attendance_batch_workflow_guard"
on public.attendance_batches as restrictive for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','educational','executive')
  or (
    lower(coalesce(private.frahoosh_current_role(),'')) = 'teacher'
    and teacher_id = private.frahoosh_current_teacher_id()
    and status in ('draft','submitted','pending','در انتظار تأیید','pending_approval')
  )
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','educational','executive')
  or (
    lower(coalesce(private.frahoosh_current_role(),'')) = 'teacher'
    and teacher_id = private.frahoosh_current_teacher_id()
    and status in ('draft','submitted','pending','در انتظار تأیید','pending_approval')
  )
);
