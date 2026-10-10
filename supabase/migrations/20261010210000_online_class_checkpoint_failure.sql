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

-- Entry attendance is recorded by the authenticated student's identity, not by a client-supplied status.
create or replace function public.record_online_class_entry(
  p_class_id integer,
  p_session_id bigint,
  p_student_id integer
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
  if not exists (select 1 from public.online_class_students m where m.class_id=p_class_id and m.student_id=p_student_id) then
    raise exception 'not class member';
  end if;
  if not exists (select 1 from public.online_class_sessions s where s.id=p_session_id and s.class_id=p_class_id and s.ended_at is null) then
    raise exception 'session inactive';
  end if;
  select concat_ws(' ',s.first_name,s.last_name) into v_name from public.students s where s.id=p_student_id;
  insert into public.online_attendance(class_id,student_id,student_name,status,session_id,source,event_time,recorded_at,checkpoint_no)
  values(p_class_id,p_student_id,coalesce(v_name,''),'present',p_session_id,'standalone_online_class_entry',now()::text,now(),0);
  return 'present';
end;
$$;
revoke execute on function public.record_online_class_entry(integer,bigint,integer) from public,anon;
grant execute on function public.record_online_class_entry(integer,bigint,integer) to authenticated;

create table if not exists public.online_class_student_blocks (
  class_id integer not null references public.online_classes(id) on delete cascade,
  session_id bigint not null references public.online_class_sessions(id) on delete cascade,
  student_id integer not null references public.students(id) on delete cascade,
  checkpoint_no integer not null check (checkpoint_no in (1,2)),
  blocked_at timestamptz not null default now(),
  primary key(class_id,session_id,student_id)
);
alter table public.online_class_student_blocks enable row level security;
revoke all on table public.online_class_student_blocks from anon,authenticated;

create or replace function public.is_online_class_student_blocked(
  p_class_id integer,
  p_session_id bigint,
  p_student_id integer
) returns boolean
language plpgsql
security definer
set search_path=''
as $$
declare v_student_id integer := (select private.frahoosh_current_student_id());
begin
  if v_student_id is null or v_student_id <> p_student_id then
    raise exception 'student identity mismatch';
  end if;
  return exists(select 1 from public.online_class_student_blocks b where b.class_id=p_class_id and b.session_id=p_session_id and b.student_id=p_student_id);
end;
$$;
revoke execute on function public.is_online_class_student_blocked(integer,bigint,integer) from public,anon;
grant execute on function public.is_online_class_student_blocked(integer,bigint,integer) to authenticated;

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
  if v_student_id is null or v_student_id <> p_student_id then raise exception 'student identity mismatch'; end if;
  if p_checkpoint_no not in (1,2) then raise exception 'invalid checkpoint'; end if;
  if not exists(select 1 from public.online_class_students m where m.class_id=p_class_id and m.student_id=p_student_id) then raise exception 'not class member'; end if;
  if not exists(select 1 from public.online_class_sessions s where s.id=p_session_id and s.class_id=p_class_id and s.ended_at is null) then raise exception 'session inactive'; end if;
  select concat_ws(' ',s.first_name,s.last_name) into v_name from public.students s where s.id=p_student_id;
  insert into public.online_attendance(class_id,student_id,student_name,status,session_id,source,event_time,recorded_at,checkpoint_no)
  values(p_class_id,p_student_id,coalesce(v_name,''),'absent',p_session_id,'online_class_verification_failed',now()::text,now(),p_checkpoint_no);
  insert into public.online_class_student_blocks(class_id,session_id,student_id,checkpoint_no)
  values(p_class_id,p_session_id,p_student_id,p_checkpoint_no)
  on conflict(class_id,session_id,student_id) do update set checkpoint_no=excluded.checkpoint_no,blocked_at=now();
  return 'blocked';
end;
$$;
