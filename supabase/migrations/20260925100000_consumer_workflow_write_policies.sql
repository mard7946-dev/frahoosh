-- Frahoosh: consumer workflow write policies.
-- Apply after 20260924170000_final_consumer_rls_and_workflow_hardening.sql.
-- These policies keep student/parent writes scoped to their authenticated identity.

drop policy if exists frahoosh_student_payment_insert on public.payment_attempts;
create policy frahoosh_student_payment_insert
on public.payment_attempts
for insert to authenticated
with check (
  (select private.frahoosh_current_role()) in ('student','دانش‌آموز')
  and student_id = (select private.frahoosh_current_student_id())
  and lower(coalesce(payer_username,'')) = lower(coalesce(private.frahoosh_current_username(),''))
);

drop policy if exists frahoosh_parent_payment_insert on public.payment_attempts;
create policy frahoosh_parent_payment_insert
on public.payment_attempts
for insert to authenticated
with check (
  (select private.frahoosh_current_role()) in ('parent','parents','ولی','اولیا')
  and lower(coalesce(payer_username,'')) = lower(coalesce(private.frahoosh_current_username(),''))
  and exists (
    select 1
    from public.parent_children pc
    where pc.student_id = payment_attempts.student_id
      and lower(coalesce(pc.parent_username,'')) =
          lower(coalesce(private.frahoosh_current_username(),''))
  )
);

drop policy if exists frahoosh_parent_children_insert on public.parent_children;
create policy frahoosh_parent_children_insert
on public.parent_children
for insert to authenticated
with check (
  (select private.frahoosh_current_role()) in ('parent','parents','ولی','اولیا')
  and lower(coalesce(parent_username,'')) =
      lower(coalesce(private.frahoosh_current_username(),''))
  and exists (select 1 from public.students s where s.id = parent_children.student_id)
);

drop policy if exists frahoosh_parent_children_update on public.parent_children;
create policy frahoosh_parent_children_update
on public.parent_children
for update to authenticated
using (
  (select private.frahoosh_current_role()) in ('parent','parents','ولی','اولیا')
  and lower(coalesce(parent_username,'')) =
      lower(coalesce(private.frahoosh_current_username(),''))
)
with check (
  (select private.frahoosh_current_role()) in ('parent','parents','ولی','اولیا')
  and lower(coalesce(parent_username,'')) =
      lower(coalesce(private.frahoosh_current_username(),''))
  and exists (select 1 from public.students s where s.id = parent_children.student_id)
);

drop policy if exists frahoosh_parent_children_delete on public.parent_children;
create policy frahoosh_parent_children_delete
on public.parent_children
for delete to authenticated
using (
  (select private.frahoosh_current_role()) in ('parent','parents','ولی','اولیا')
  and lower(coalesce(parent_username,'')) =
      lower(coalesce(private.frahoosh_current_username(),''))
);

drop policy if exists frahoosh_parent_meeting_insert on public.meeting_requests;
create policy frahoosh_parent_meeting_insert
on public.meeting_requests
for insert to authenticated
with check (
  (select private.frahoosh_current_role()) in ('parent','parents','ولی','اولیا')
  and lower(coalesce(requester_username,'')) =
      lower(coalesce(private.frahoosh_current_username(),''))
  and exists (
    select 1
    from public.parent_children pc
    where pc.student_id = meeting_requests.student_id
      and lower(coalesce(pc.parent_username,'')) =
          lower(coalesce(private.frahoosh_current_username(),''))
  )
);

drop policy if exists frahoosh_parent_meeting_update on public.meeting_requests;
create policy frahoosh_parent_meeting_update
on public.meeting_requests
for update to authenticated
using (
  (select private.frahoosh_current_role()) in ('parent','parents','ولی','اولیا')
  and lower(coalesce(requester_username,'')) =
      lower(coalesce(private.frahoosh_current_username(),''))
)
with check (
  (select private.frahoosh_current_role()) in ('parent','parents','ولی','اولیا')
  and lower(coalesce(requester_username,'')) =
      lower(coalesce(private.frahoosh_current_username(),''))
);

drop policy if exists frahoosh_parent_meeting_delete on public.meeting_requests;
create policy frahoosh_parent_meeting_delete
on public.meeting_requests
for delete to authenticated
using (
  (select private.frahoosh_current_role()) in ('parent','parents','ولی','اولیا')
  and lower(coalesce(requester_username,'')) =
      lower(coalesce(private.frahoosh_current_username(),''))
);

grant select, insert, update, delete on table
  public.parent_children,
  public.payment_attempts,
  public.meeting_requests
to authenticated;
