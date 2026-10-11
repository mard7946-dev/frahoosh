-- Fix infinite RLS recursion on public.guest_online_members.
-- Applied to Supabase project gtmmllcxhdejwjjnyzrh.
-- The SECURITY DEFINER helper reads host membership without re-entering the
-- caller's row-level security policy.
create or replace function public.is_guest_online_class_host(p_class_id integer)
returns boolean
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select exists (
    select 1
    from public.guest_online_members h
    where h.class_id = p_class_id
      and h.user_id = auth.uid()
      and h.role = 'host'
  );
$$;

revoke all on function public.is_guest_online_class_host(integer) from public;
grant execute on function public.is_guest_online_class_host(integer) to authenticated;

drop policy if exists guest_members_own_class on public.guest_online_members;

create policy guest_members_own_class
on public.guest_online_members
for all
to authenticated
using (
  user_id = (select auth.uid())
  or public.is_guest_online_class_host(class_id)
)
with check (
  user_id = (select auth.uid())
);
