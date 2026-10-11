-- Repair the private-schema permissions used by online-class RLS.
grant usage on schema private to authenticated;
revoke usage on schema private from anon;

-- Managers may start the clock, but students wait until the assigned teacher claims the session.
create or replace function public.start_online_class_session(p_class_id integer)
returns bigint language plpgsql security definer set search_path = '' as $$
declare
  v_role text := lower(coalesce((select private.frahoosh_current_role()), ''));
  v_teacher_id integer := (select private.frahoosh_current_teacher_id());
  v_duration integer; v_session_id bigint; v_teacher_user_id uuid;
begin
  if not (
    v_role in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','executive','معاون اجرایی','معاونت اجرایی')
    or (v_role in ('teacher','دبیر') and exists (select 1 from public.online_class_teachers t where t.class_id=p_class_id and t.teacher_id=v_teacher_id))
  ) then raise exception 'not authorized to start this class'; end if;
  select greatest(5,least(240,coalesce(c.duration,50))) into v_duration from public.online_classes c where c.id=p_class_id;
  if v_duration is null then raise exception 'class not found'; end if;
  if v_role in ('teacher','دبیر') then
    select a.auth_user_id into v_teacher_user_id
    from public.teachers t join public.account_settings a on a.national_code=t.national_code
    where t.id=v_teacher_id order by a.updated_at desc nulls last limit 1;
    v_teacher_user_id:=coalesce(v_teacher_user_id,auth.uid());
  end if;
  select s.id into v_session_id from public.online_class_sessions s
  where s.class_id=p_class_id and coalesce(s.ended_at,'')='' order by s.id desc limit 1;
  if v_session_id is not null then
    if v_teacher_user_id is not null then update public.online_class_sessions set teacher_user_id=v_teacher_user_id::text where id=v_session_id; end if;
    update public.online_classes set status='active',activated_at=coalesce(activated_at,now()),pages=15,smart_board=1,quiz=1,camera=1,microphone=1,record=1 where id=p_class_id;
    return v_session_id;
  end if;
  insert into public.online_class_sessions(class_id,started_at,ended_at,created_at,duration_minutes,teacher_user_id)
  values(p_class_id,now()::text,null,now()::text,v_duration,case when v_teacher_user_id is null then null else v_teacher_user_id::text end)
  returning id into v_session_id;
  update public.online_classes set status='active',activated_at=now(),pages=15,smart_board=1,quiz=1,camera=1,microphone=1,record=1 where id=p_class_id;
  return v_session_id;
end;
$$;

create or replace function public.end_online_class_session(p_class_id integer)
returns bigint language plpgsql security definer set search_path = '' as $$
declare
  v_role text:=lower(coalesce((select private.frahoosh_current_role()),''));
  v_teacher_id integer:=(select private.frahoosh_current_teacher_id()); v_session_id bigint;
begin
  if not (
    v_role in ('manager','مدیر','مدیریت','executive','معاون اجرایی','معاونت اجرایی')
    or (v_role in ('teacher','دبیر') and exists(select 1 from public.online_class_teachers t where t.class_id=p_class_id and t.teacher_id=v_teacher_id))
  ) then raise exception 'not authorized to end this class'; end if;
  select s.id into v_session_id from public.online_class_sessions s where s.class_id=p_class_id and coalesce(s.ended_at,'')='' order by s.id desc limit 1;
  if v_session_id is null then raise exception 'no active session'; end if;
  update public.online_class_sessions set ended_at=now()::text where id=v_session_id;
  update public.online_classes set status='ended' where id=p_class_id;
  return v_session_id;
end;
$$;

create or replace function public.delete_online_class_admin(p_class_id integer)
returns boolean language plpgsql security definer set search_path = '' as $$
declare v_role text:=lower(coalesce((select private.frahoosh_current_role()),''));
begin
  if v_role not in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی','executive','معاون اجرایی','معاونت اجرایی') then raise exception 'not authorized to delete this class'; end if;
  if not exists(select 1 from public.online_classes where id=p_class_id) then return false; end if;
  delete from public.online_attendance where class_id=p_class_id or session_id in(select id from public.online_class_sessions where class_id=p_class_id);
  delete from public.online_class_student_blocks where class_id=p_class_id or session_id in(select id from public.online_class_sessions where class_id=p_class_id);
  delete from public.guest_online_members where class_id=p_class_id;
  delete from public.online_class_student_permissions where class_id=p_class_id;
  delete from public.online_class_signals where class_id=p_class_id;
  delete from public.online_class_students where class_id=p_class_id;
  delete from public.online_class_teachers where class_id=p_class_id;
  delete from public.smart_class_preview where class_id=p_class_id;
  delete from public.online_class_sessions where class_id=p_class_id;
  delete from public.online_classes where id=p_class_id;
  return true;
end;
$$;

revoke all on function public.start_online_class_session(integer) from public,anon;
revoke all on function public.end_online_class_session(integer) from public,anon;
revoke all on function public.delete_online_class_admin(integer) from public,anon;
grant execute on function public.start_online_class_session(integer) to authenticated;
grant execute on function public.end_online_class_session(integer) to authenticated;
grant execute on function public.delete_online_class_admin(integer) to authenticated;
