-- Let authorized school management create/share a guest link before the teacher enters.
-- Guest joining remains separately protected by guest_join_online_class, which requires the teacher's real join signal.
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
    v_role in (
      'manager','مدیر','مدیریت','مدیر مدرسه','principal','administrator','admin',
      'educational','معاون آموزشی','معاونت آموزشی'
    )
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

  -- Only active classes can receive a guest invite. Do not require the teacher
  -- to have entered yet: the guest join RPC still enforces that security gate.
  if not exists (
    select 1 from public.online_classes c
    where c.id = p_class_id and c.status = 'active'
  ) then
    raise exception 'کلاس فعال پیدا نشد؛ وضعیت کلاس را بررسی کنید';
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

revoke all on function public.get_online_class_guest_invite(integer) from public, anon;
grant execute on function public.get_online_class_guest_invite(integer) to authenticated;
