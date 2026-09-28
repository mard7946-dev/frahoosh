-- Keep Auth users and the canonical school-role directory synchronized.

create or replace function private.sync_frahoosh_auth_user()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, auth, private
as $$
declare
  s public.account_settings;
  v_username text;
  v_role text;
  v_display text;
  v_student bigint;
  v_teacher bigint;
  v_staff bigint;
begin
  if new.email is null then return new; end if;
  select * into s from public.account_settings
  where lower(email)=lower(new.email) order by id limit 1;
  v_username := coalesce(s.username,new.email);
  v_role := lower(coalesce(s.preferences->>'role',nullif(new.raw_app_meta_data->>'role',''),'student'));
  v_display := coalesce(s.display_name,new.raw_user_meta_data->>'display_name',new.email);
  begin v_student := nullif(s.preferences->>'linked_student_id','')::bigint; exception when others then v_student := null; end;
  begin v_teacher := nullif(s.preferences->>'linked_teacher_id','')::bigint; exception when others then v_teacher := null; end;
  begin v_staff := nullif(s.preferences->>'linked_staff_id','')::bigint; exception when others then v_staff := null; end;
  insert into public.users(username,role,linked_student_id,linked_teacher_id,linked_staff_id,display_name)
  values(v_username,v_role,v_student,v_teacher,v_staff,v_display)
  on conflict(username) do update set display_name=coalesce(excluded.display_name,public.users.display_name);
  return new;
end;
$$;

create or replace function private.sync_frahoosh_account_settings()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, auth, private
as $$
declare
  v_role text := lower(coalesce(new.preferences->>'role','student'));
  v_student bigint;
  v_teacher bigint;
  v_staff bigint;
begin
  if new.email is null then return new; end if;
  begin v_student := nullif(new.preferences->>'linked_student_id','')::bigint; exception when others then v_student := null; end;
  begin v_teacher := nullif(new.preferences->>'linked_teacher_id','')::bigint; exception when others then v_teacher := null; end;
  begin v_staff := nullif(new.preferences->>'linked_staff_id','')::bigint; exception when others then v_staff := null; end;
  insert into public.users(username,role,linked_student_id,linked_teacher_id,linked_staff_id,display_name)
  values(new.username,v_role,v_student,v_teacher,v_staff,new.display_name)
  on conflict(username) do update set
    role=excluded.role,
    linked_student_id=coalesce(excluded.linked_student_id,public.users.linked_student_id),
    linked_teacher_id=coalesce(excluded.linked_teacher_id,public.users.linked_teacher_id),
    linked_staff_id=coalesce(excluded.linked_staff_id,public.users.linked_staff_id),
    display_name=coalesce(excluded.display_name,public.users.display_name);
  return new;
end;
$$;

revoke all on function private.sync_frahoosh_auth_user() from public;
revoke all on function private.sync_frahoosh_account_settings() from public;

drop trigger if exists frahoosh_auth_user_sync on auth.users;
create trigger frahoosh_auth_user_sync
after insert on auth.users
for each row execute function private.sync_frahoosh_auth_user();

drop trigger if exists frahoosh_account_settings_sync on public.account_settings;
create trigger frahoosh_account_settings_sync
after insert or update on public.account_settings
for each row execute function private.sync_frahoosh_account_settings();
