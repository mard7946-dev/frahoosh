-- Ensure first-time auth signup still gets a safe default tenant and lock down private helper execution.
create or replace function private.frahoosh_set_tenant_school()
returns trigger language plpgsql set search_path=''
as $$
declare v_school_id uuid; v_class_id text;
begin
 if coalesce(current_setting('request.jwt.claim.role',true),'')='service_role' or private.frahoosh_is_platform_admin() then
  if new.tenant_school_id is null and tg_op='UPDATE' then new.tenant_school_id:=old.tenant_school_id; end if;
  return new;
 end if;
 v_school_id:=private.frahoosh_current_school_id();
 if v_school_id is null and tg_op='INSERT' and tg_table_name='account_settings' then
  select id into v_school_id from public.schools where slug='frahoosh-default' limit 1;
 end if;
 if v_school_id is null and tg_op='INSERT' and to_jsonb(new)?'class_id' then
  v_class_id:=to_jsonb(new)->>'class_id';
  if v_class_id is not null then select oc.tenant_school_id into v_school_id from public.online_classes oc where oc.id::text=v_class_id limit 1; end if;
 end if;
 if v_school_id is not null then new.tenant_school_id:=v_school_id;
 elsif tg_op='UPDATE' then new.tenant_school_id:=old.tenant_school_id;
 elsif new.tenant_school_id is null then raise exception 'مدرسهٔ کاربر مشخص نیست؛ ثبت اطلاعات انجام نشد.' using errcode='42501';
 end if;
 return new;
end; $$;

revoke all on function private.frahoosh_is_platform_admin() from public,anon;
revoke all on function private.frahoosh_current_school_id() from public,anon;
revoke all on function private.frahoosh_school_access_active(uuid) from public,anon;
revoke all on function private.frahoosh_set_tenant_school() from public,anon,authenticated;
revoke all on function private.frahoosh_sync_school_membership() from public,anon,authenticated;
revoke all on function private.frahoosh_fill_subscription_from_plan() from public,anon,authenticated;
revoke all on function private.frahoosh_enforce_student_limit() from public,anon,authenticated;
revoke all on function private.frahoosh_normalize_school_role(text) from public,anon;
grant execute on function private.frahoosh_is_platform_admin() to authenticated;
grant execute on function private.frahoosh_current_school_id() to authenticated;
grant execute on function private.frahoosh_school_access_active(uuid) to authenticated;
