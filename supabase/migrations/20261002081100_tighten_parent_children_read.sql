drop policy if exists "frahoosh_parent_child_read" on public.parent_children;
create policy "frahoosh_parent_child_read"
on public.parent_children
for select to authenticated
using (private.frahoosh_current_parent_matches(parent_username));
