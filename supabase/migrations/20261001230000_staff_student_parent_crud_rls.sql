-- Allow authenticated school staff to manage student records and parent-child links.
-- This keeps the UI CRUD contract aligned with database authorization.
create policy "staff students select"
on public.students
for select
to authenticated
using ((select private.frahoosh_is_staff()));

create policy "staff students insert"
on public.students
for insert
to authenticated
with check ((select private.frahoosh_is_staff()));

create policy "staff students update"
on public.students
for update
to authenticated
using ((select private.frahoosh_is_staff()))
with check ((select private.frahoosh_is_staff()));

create policy "staff students delete"
on public.students
for delete
to authenticated
using ((select private.frahoosh_is_staff()));

create policy "staff parent_children select"
on public.parent_children
for select
to authenticated
using ((select private.frahoosh_is_staff()));

create policy "staff parent_children insert"
on public.parent_children
for insert
to authenticated
with check ((select private.frahoosh_is_staff()));

create policy "staff parent_children update"
on public.parent_children
for update
to authenticated
using ((select private.frahoosh_is_staff()))
with check ((select private.frahoosh_is_staff()));

create policy "staff parent_children delete"
on public.parent_children
for delete
to authenticated
using ((select private.frahoosh_is_staff()));

drop policy if exists "students parent read" on public.students;

create policy "students parent read"
on public.students
for select
to authenticated
using (
  exists (
    select 1
    from public.parent_children pc
    join public.account_settings a
      on lower(a.username) = lower(pc.parent_username)
    where pc.student_id = students.id
      and a.auth_user_id = (select auth.uid())
      and lower(coalesce(a.role, '')) = any (array['parent','parents','ولی','اولیا'])
  )
);

create policy "parent own children select"
on public.parent_children
for select
to authenticated
using (
  exists (
    select 1
    from public.account_settings a
    where lower(a.username) = lower(parent_children.parent_username)
      and a.auth_user_id = (select auth.uid())
      and lower(coalesce(a.role, '')) = any (array['parent','parents','ولی','اولیا'])
  )
);
