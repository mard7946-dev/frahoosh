-- A session's teacher_user_id can be assigned before the teacher has entered the room.
-- Require an actual teacher join signal created after this session started before issuing/accepting guest invites.
create or replace function public.get_online_class_guest_invite(p_class_id integer)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_role text := lower(coalesce((select private.frahoosh_current_role()), ''));
  v_teacher_id integer := (select private.frahoosh_current_teacher_id());
  v_code text;
begin
  if not (
    v_role in ('manager','مدیر','مدیریت','educational','معاون آموزشی','معاونت آموزشی')
    or (
      v_role in ('teacher','دبیر')
      and exists (
        select 1 from public.online_class_teachers t
        where t.class_id = p_class_id and t.teacher_id = v_teacher_id
      )
    )
  ) then
    raise exception 'not authorized to create a guest invite';
  end if;

  if not exists (
    select 1
    from public.online_class_sessions s
    where s.class_id = p_class_id
      and s.teacher_user_id is not null
      and coalesce(s.ended_at, '') = ''
      and exists (
        select 1
        from public.online_class_signals sig
        where sig.class_id = s.class_id
          and sig.sender_user_id::text = s.teacher_user_id
          and sig.signal_type = 'join'
          and lower(coalesce(sig.payload->>'role','')) in ('teacher','دبیر')
          and sig.created_at >= s.started_at::timestamptz
      )
  ) then
    raise exception 'دبیر هنوز وارد اتاق کلاس نشده است؛ پس از ورود دبیر لینک دعوت را بسازید';
  end if;

  select c.guest_room_code into v_code
  from public.online_classes c where c.id = p_class_id for update;
  if v_code is null or btrim(v_code) = '' then
    v_code := upper(substr(md5(random()::text || clock_timestamp()::text || p_class_id::text), 1, 10));
    update public.online_classes set guest_room_code = v_code where id = p_class_id;
  end if;
  return v_code;
end;
$$;

create or replace function public.guest_join_online_class(p_room_code text, p_display_name text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_class_id integer;
  v_session_id bigint;
  v_started_at text;
  v_code text := upper(trim(coalesce(p_room_code, '')));
begin
  if v_uid is null or coalesce((auth.jwt()->>'is_anonymous')::boolean, false) is not true then
    raise exception 'guest authentication required';
  end if;
  if v_code = '' then raise exception 'کد دعوت کلاس وارد نشده است'; end if;

  select c.id, s.id, s.started_at::text
    into v_class_id, v_session_id, v_started_at
  from public.online_classes c
  join lateral (
    select ss.id, ss.started_at, ss.teacher_user_id
    from public.online_class_sessions ss
    where ss.class_id = c.id
      and ss.teacher_user_id is not null
      and coalesce(ss.ended_at, '') = ''
    order by ss.id desc limit 1
  ) s on true
  where c.guest_room_code = v_code
    and c.status = 'active'
    and exists (
      select 1
      from public.online_class_signals sig
      where sig.class_id = c.id::bigint
        and sig.sender_user_id::text = s.teacher_user_id
        and sig.signal_type = 'join'
        and lower(coalesce(sig.payload->>'role','')) in ('teacher','دبیر')
        and sig.created_at >= s.started_at::timestamptz
    )
  limit 1;

  if v_class_id is null or v_session_id is null then
    raise exception 'دبیر هنوز وارد اتاق کلاس نشده است؛ پس از ورود دبیر دوباره تلاش کنید';
  end if;

  insert into public.guest_online_members(class_id, user_id, display_name, role)
  values (v_class_id, v_uid, coalesce(nullif(trim(p_display_name), ''), 'میهمان'), 'guest')
  on conflict (class_id, user_id)
  do update set display_name = excluded.display_name, left_at = null;

  return jsonb_build_object('class_id', v_class_id, 'room_code', v_code,
                            'session_id', v_session_id, 'started_at', v_started_at);
end;
$$;

revoke all on function public.get_online_class_guest_invite(integer) from public, anon;
grant execute on function public.get_online_class_guest_invite(integer) to authenticated;
revoke all on function public.guest_join_online_class(text, text) from public;
grant execute on function public.guest_join_online_class(text, text) to authenticated;
