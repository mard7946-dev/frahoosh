-- Record missed online-class presence verification without allowing students to impersonate one another.
create or replace function public.record_online_class_checkpoint_failure(
  p_class_id integer,
  p_session_id bigint,
  p_student_id integer,
  p_checkpoint_no integer
) returns text
language plpgsql
security definer
set search_path=''
as $$
declare
  v_student_id integer := (select private.frahoosh_current_student_id());
  v_name text;
begin
  if v_student_id is null or v_student_id <> p_student_id then
    raise exception 'student identity mismatch';
  end if;
  if p_checkpoint_no not in (1,2) then
    raise exception 'invalid checkpoint';
  end if;
  if not exists (
    select 1 from public.online_class_students m
    where m.class_id=p_class_id and m.student_id=p_student_id
  ) then
    raise exception 'not class member';
  end if;
  if not exists (
    select 1 from public.online_class_sessions s
    where s.id=p_session_id and s.class_id=p_class_id and s.ended_at is null
  ) then
    raise exception 'session inactive';
  end if;
  select concat_ws(' ',s.first_name,s.last_name)
    into v_name from public.students s where s.id=p_student_id;
  insert into public.online_attendance(
    class_id,student_id,student_name,status,session_id,source,event_time,recorded_at,checkpoint_no
  ) values (
    p_class_id,p_student_id,coalesce(v_name,''),'absent',p_session_id,
    'online_class_verification_failed',now()::text,now(),p_checkpoint_no
  );
  return 'absent';
end;
$$;

revoke execute on function public.record_online_class_checkpoint_failure(integer,bigint,integer,integer) from public,anon;
grant execute on function public.record_online_class_checkpoint_failure(integer,bigint,integer,integer) to authenticated;
