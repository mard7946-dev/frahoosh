create or replace function public.register_online_class_student_guest(
  p_class_id integer,
  p_session_id integer,
  p_display_name text,
  p_class_name text
)
returns boolean
language plpgsql
security definer
set search_path = public, pg_temp
as $function$
declare
  v_uid uuid := auth.uid();
  v_name text := btrim(coalesce(p_display_name, ''));
  v_class text := btrim(coalesce(p_class_name, ''));
begin
  if v_uid is null then raise exception 'ورود مهمان معتبر نیست'; end if;
  if v_name = '' or v_class = '' then raise exception 'نام دانش‌آموز و کلاس الزامی است'; end if;

  if not exists (
    select 1 from public.online_class_sessions s
    where s.id = p_session_id
      and s.class_id = p_class_id
      and coalesce(s.ended_at, '') = ''
  ) then raise exception 'جلسه کلاس فعال نیست'; end if;

  if not exists (
    select 1 from public.weekly_schedule_entries w
    where w.online_class_id = p_class_id
      and w.activated_at is not null
      and replace(replace(regexp_replace(lower(btrim(w.class_name)), '\s+', '', 'g'),'ي','ی'),'ك','ک')
        = replace(replace(regexp_replace(lower(v_class), '\s+', '', 'g'),'ي','ی'),'ك','ک')
  ) then raise exception 'این کلاس در برنامه هفتگی به جلسه فعال متصل نیست'; end if;

  update public.guest_online_members
     set display_name = v_name, role = 'guest', left_at = null
   where class_id = p_class_id and user_id = v_uid;
  if not found then
    insert into public.guest_online_members(class_id,user_id,display_name,role)
    values(p_class_id,v_uid,v_name,'guest');
  end if;
  return true;
end;
$function$;

revoke all on function public.register_online_class_student_guest(integer, integer, text, text) from public;
grant execute on function public.register_online_class_student_guest(integer, integer, text, text) to authenticated;
