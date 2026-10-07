-- Keep discipline records hidden from students/parents until approved.
drop policy if exists "discipline owner read" on public.discipline_records;
drop policy if exists "frahoosh_student_own_read" on public.discipline_records;
drop policy if exists "frahoosh_parent_child_read" on public.discipline_records;
drop policy if exists "student linked read discipline_records" on public.discipline_records;
drop policy if exists "parent linked read discipline_records" on public.discipline_records;

create policy "frahoosh_student_approved_discipline_read"
on public.discipline_records for select to authenticated
using (student_id = private.frahoosh_current_student_id() and status = 'confirmed');

create policy "frahoosh_parent_approved_discipline_read"
on public.discipline_records for select to authenticated
using (
  status = 'confirmed'
  and exists (
    select 1 from public.parent_children pc
    where pc.student_id = discipline_records.student_id
      and private.frahoosh_current_parent_matches(pc.parent_username)
  )
);

create policy "student linked approved read discipline_records"
on public.discipline_records for select to authenticated
using (student_id = private.frahoosh_current_student_id() and status = 'confirmed');

create policy "parent linked approved read discipline_records"
on public.discipline_records for select to authenticated
using (
  status = 'confirmed'
  and exists (
    select 1
    from public.parent_children pc
    join public.account_settings a on lower(a.username)=lower(pc.parent_username)
    where pc.student_id = discipline_records.student_id
      and a.auth_user_id = auth.uid()
  )
);

create policy "responsible staff manage educational followups"
on public.educational_followups for all to authenticated
using (lower(coalesce(private.frahoosh_current_role,'')) in ('responsible','مسئول مربوطه','مسئول مربوطه آموزشی'))
with check (lower(coalesce(private.frahoosh_current_role,'')) in ('responsible','مسئول مربوطه','مسئول مربوطه آموزشی'));
