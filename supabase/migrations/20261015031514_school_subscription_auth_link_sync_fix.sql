-- Preserve the existing email-to-auth account linking trigger while protecting account identities.
create or replace function private.frahoosh_set_tenant_school()
returns trigger language plpgsql set search_path=''
as $$
declare v_school_id uuid; v_class_id text; v_platform_admin boolean; v_auth_link_sync boolean;
begin
 v_platform_admin:=private.frahoosh_is_platform_admin();
 v_auth_link_sync:=coalesce(current_setting('frahoosh.auth_link_sync',true),'')='true';
 if tg_table_name='account_settings' and tg_op='UPDATE' and not v_platform_admin and not v_auth_link_sync
    and to_jsonb(new)->>'auth_user_id' is distinct from to_jsonb(old)->>'auth_user_id' then
  raise exception 'تغییر شناسه حساب احراز هویت فقط برای مدیر کل سامانه مجاز است.' using errcode='42501';
 end if;
 if coalesce(current_setting('request.jwt.claim.role',true),'')='service_role' or v_platform_admin then
  if new.tenant_school_id is null and tg_op='UPDATE' then new.tenant_school_id:=old.tenant_school_id; end if;
  return new;
 end if;
 v_school_id:=private.frahoosh_current_school_id();
 if v_school_id is null and tg_op='INSERT' and tg_table_name='account_settings' then
  select id into v_school_id from public.schools where slug='frahoosh-default' limit 1;
 end if;
 if v_school_id is null and tg_op='INSERT' and tg_table_name='online_classes'
    and coalesce((auth.jwt()->>'is_anonymous')::boolean,false) then
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

create or replace function public.sync_account_settings_auth_user()
returns trigger language plpgsql security definer set search_path='public'
as $$
declare v_old_flag text;
begin
 v_old_flag:=current_setting('frahoosh.auth_link_sync',true);
 perform set_config('frahoosh.auth_link_sync','true',true);
 update public.account_settings set auth_user_id=new.id
 where auth_user_id is null and lower(coalesce(email,''))=lower(coalesce(new.email,''));
 perform set_config('frahoosh.auth_link_sync',coalesce(v_old_flag,''),true);
 return new;
end; $$;
