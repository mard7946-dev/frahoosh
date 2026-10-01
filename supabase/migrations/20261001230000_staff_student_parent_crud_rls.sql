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
