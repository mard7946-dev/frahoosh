-- Keep subscription/status screens readable after expiry, but lock school data writes.
drop policy if exists frahoosh_tenant_scope on public.account_settings;
drop policy if exists frahoosh_tenant_scope on public.school_profile;

create policy frahoosh_account_settings_read_scope on public.account_settings
as restrictive for select to authenticated
using (tenant_school_id=private.frahoosh_current_school_id() or private.frahoosh_is_platform_admin());
create policy frahoosh_account_settings_insert_scope on public.account_settings
as restrictive for insert to authenticated
with check ((tenant_school_id=private.frahoosh_current_school_id() or private.frahoosh_is_platform_admin())
 and (private.frahoosh_is_platform_admin() or private.frahoosh_school_access_active(tenant_school_id)));
create policy frahoosh_account_settings_update_scope on public.account_settings
as restrictive for update to authenticated
using ((tenant_school_id=private.frahoosh_current_school_id() or private.frahoosh_is_platform_admin())
 and (private.frahoosh_is_platform_admin() or private.frahoosh_school_access_active(tenant_school_id)))
with check ((tenant_school_id=private.frahoosh_current_school_id() or private.frahoosh_is_platform_admin())
 and (private.frahoosh_is_platform_admin() or private.frahoosh_school_access_active(tenant_school_id)));
create policy frahoosh_account_settings_delete_scope on public.account_settings
as restrictive for delete to authenticated
using ((tenant_school_id=private.frahoosh_current_school_id() or private.frahoosh_is_platform_admin())
 and (private.frahoosh_is_platform_admin() or private.frahoosh_school_access_active(tenant_school_id)));

create policy frahoosh_school_profile_read_scope on public.school_profile
as restrictive for select to authenticated
using (tenant_school_id=private.frahoosh_current_school_id() or private.frahoosh_is_platform_admin());
create policy frahoosh_school_profile_insert_scope on public.school_profile
as restrictive for insert to authenticated
with check ((tenant_school_id=private.frahoosh_current_school_id() or private.frahoosh_is_platform_admin())
 and (private.frahoosh_is_platform_admin() or private.frahoosh_school_access_active(tenant_school_id)));
create policy frahoosh_school_profile_update_scope on public.school_profile
as restrictive for update to authenticated
using ((tenant_school_id=private.frahoosh_current_school_id() or private.frahoosh_is_platform_admin())
 and (private.frahoosh_is_platform_admin() or private.frahoosh_school_access_active(tenant_school_id)))
with check ((tenant_school_id=private.frahoosh_current_school_id() or private.frahoosh_is_platform_admin())
 and (private.frahoosh_is_platform_admin() or private.frahoosh_school_access_active(tenant_school_id)));
create policy frahoosh_school_profile_delete_scope on public.school_profile
as restrictive for delete to authenticated
using ((tenant_school_id=private.frahoosh_current_school_id() or private.frahoosh_is_platform_admin())
 and (private.frahoosh_is_platform_admin() or private.frahoosh_school_access_active(tenant_school_id)));
