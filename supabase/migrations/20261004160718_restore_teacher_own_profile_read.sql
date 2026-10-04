create policy "teacher own profile read"
on public.teachers
for select
to authenticated
using (
  id = private.frahoosh_current_teacher_id()
);
