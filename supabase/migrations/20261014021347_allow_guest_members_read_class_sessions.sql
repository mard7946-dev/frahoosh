-- Allow an authenticated anonymous guest to read session metadata for their own active class.
-- Guest identity is kept in guest_online_members; no student row is created.
create policy "guest member read class sessions"
on public.online_class_sessions
for select
to authenticated
using (
  exists (
    select 1
    from public.guest_online_members m
    where m.class_id = online_class_sessions.class_id
      and m.user_id = (select auth.uid())
      and m.left_at is null
  )
);
