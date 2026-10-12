-- Secure invitation codes for the actual active classroom (not a separate GUEST-* class row).
alter table public.online_classes
  add column if not exists guest_room_code text;

update public.online_classes
set guest_room_code = upper(substr(md5(random()::text || clock_timestamp()::text || id::text), 1, 10))
where guest_room_code is null or btrim(guest_room_code) = '';

create unique index if not exists online_classes_guest_room_code_uidx
  on public.online_classes (guest_room_code);

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
    select 1 from public.online_class_sessions s
    where s.class_id = p_class_id and coalesce(s.ended_at, '') = ''
  ) then
    raise exception 'کلاس هنوز فعال نیست؛ ابتدا دبیر وارد جلسه شود';
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
  v_code text := upper(trim(coalesce(p_room_code, '')));
begin
  if v_uid is null or coalesce((auth.jwt()->>'is_anonymous')::boolean, false) is not true then
    raise exception 'guest authentication required';
  end if;
  if v_code = '' then
    raise exception 'کد دعوت کلاس وارد نشده است';
  end if;

  select c.id into v_class_id
  from public.online_classes c
  where c.guest_room_code = v_code
    and c.status = 'active'
    and exists (
      select 1 from public.online_class_sessions s
      where s.class_id = c.id and coalesce(s.ended_at, '') = ''
    )
  limit 1;

  if v_class_id is null then
    raise exception 'کد دعوت معتبر نیست یا دبیر هنوز در کلاس فعال نیست';
  end if;

  insert into public.guest_online_members(class_id, user_id, display_name, role)
  values (v_class_id, v_uid, coalesce(nullif(trim(p_display_name), ''), 'میهمان'), 'guest')
  on conflict (class_id, user_id)
  do update set display_name = excluded.display_name, left_at = null;

  return jsonb_build_object('class_id', v_class_id, 'room_code', v_code);
end;
$$;

revoke all on function public.get_online_class_guest_invite(integer) from public, anon;
grant execute on function public.get_online_class_guest_invite(integer) to authenticated;
revoke all on function public.guest_join_online_class(text, text) from public;
grant execute on function public.guest_join_online_class(text, text) to authenticated;
