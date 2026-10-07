drop policy if exists "staff domain access executive_operations" on public.executive_operations;

create policy "executive_operations_management_read"
on public.executive_operations
for select to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی','educational','معاون آموزشی','معاونت آموزشی')
);

create policy "executive_operations_management_insert"
on public.executive_operations
for insert to authenticated
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی')
);

create policy "executive_operations_management_update"
on public.executive_operations
for update to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی')
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی')
);

create policy "executive_operations_management_delete"
on public.executive_operations
for delete to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی')
);

drop policy if exists "staff domain access discipline_records" on public.discipline_records;
drop policy if exists "staff teacher domain access discipline_records" on public.discipline_records;

create policy "discipline_management_all"
on public.discipline_records
for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','executive','معاون اجرایی','معاونت اجرایی')
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','executive','معاون اجرایی','معاونت اجرایی')
);

create policy "discipline_teacher_insert_own"
on public.discipline_records
for insert to authenticated
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) = 'teacher'
  and teacher_id = private.frahoosh_current_teacher_id()
  and status = 'pending'
);

create policy "discipline_teacher_update_own_pending"
on public.discipline_records
for update to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) = 'teacher'
  and teacher_id = private.frahoosh_current_teacher_id()
  and status <> 'confirmed'
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) = 'teacher'
  and teacher_id = private.frahoosh_current_teacher_id()
  and status <> 'confirmed'
);

create policy "discipline_teacher_delete_own_pending"
on public.discipline_records
for delete to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) = 'teacher'
  and teacher_id = private.frahoosh_current_teacher_id()
  and status <> 'confirmed'
);

drop policy if exists "management_all_educational_followups" on public.educational_followups;
drop policy if exists "staff domain access educational_followups" on public.educational_followups;

create policy "educational_followups_authorized_read"
on public.educational_followups
for select to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','responsible','مسئول مربوطه','مسئول مربوطه آموزشی','executive','معاون اجرایی','معاونت اجرایی','advisor','مشاور','مشاوره')
  or student_id = private.frahoosh_current_student_id()
  or exists (
    select 1
    from parent_children pc
    where pc.student_id = educational_followups.student_id
      and private.frahoosh_current_parent_matches(pc.parent_username)
  )
);

create policy "educational_followups_authorized_write"
on public.educational_followups
for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','responsible','مسئول مربوطه','مسئول مربوطه آموزشی')
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) in
  ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','responsible','مسئول مربوطه','مسئول مربوطه آموزشی')
);
