create or replace function public.frahoosh_can_activate_modules()
returns boolean language sql stable security definer set search_path=public as $$
select lower(coalesce((select role from public.account_settings where auth_user_id=auth.uid() limit 1),'')) in ('manager','educational','executive','cultural') $$;
revoke all on function public.frahoosh_can_activate_modules() from public;
grant execute on function public.frahoosh_can_activate_modules() to authenticated;
drop policy if exists module_activations_staff_all on public.module_activations;
create policy module_activations_staff_all on public.module_activations for all to authenticated
using(public.frahoosh_can_activate_modules()) with check(public.frahoosh_can_activate_modules());