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
    select ss.id, ss.started_at
    from public.online_class_sessions ss
    where ss.class_id = c.id and coalesce(ss.ended_at, '') = ''
    order by ss.id desc limit 1
  ) s on true
  where c.guest_room_code = v_code and c.status = 'active'
  limit 1;

  if v_class_id is null or v_session_id is null then
    raise exception 'کد دعوت معتبر نیست یا دبیر هنوز در کلاس فعال نیست';
  end if;

  insert into public.guest_online_members(class_id, user_id, display_name, role)
  values (v_class_id, v_uid, coalesce(nullif(trim(p_display_name), ''), 'میهمان'), 'guest')
  on conflict (class_id, user_id)
  do update set display_name = excluded.display_name, left_at = null;

  return jsonb_build_object('class_id', v_class_id, 'room_code', v_code,
                            'session_id', v_session_id, 'started_at', v_started_at);
end;
$$;
revoke all on function public.guest_join_online_class(text, text) from public;
grant execute on function public.guest_join_online_class(text, text) to authenticated;