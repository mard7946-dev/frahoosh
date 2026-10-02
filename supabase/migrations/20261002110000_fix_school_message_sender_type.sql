-- Fix message sender_user_id type mismatch: messages stores legacy integer user ids.
create or replace function public.send_school_message(
  p_receiver text,p_title text,p_body text,
  p_audience_type text default 'user',p_audience_value text default null
) returns public.messages
language plpgsql security definer
set search_path to 'public,private'
as $function$
declare
  r public.messages;
  v_email text:=coalesce(auth.jwt()->>'email','');
  v_receiver text:=coalesce(nullif(btrim(p_receiver),''),nullif(btrim(p_audience_value),''));
  v_sender_user_id integer;
  v_sender_name text;
begin
  if v_receiver is null then raise exception 'receiver required'; end if;
  if not private.frahoosh_can_message_target(v_receiver) then
    raise exception 'مخاطب خارج از ارتباط مجاز مدرسه است';
  end if;
  select u.id,u.display_name into v_sender_user_id,v_sender_name
  from public.users u
  left join public.account_settings a on a.username=u.username
  where lower(u.username)=lower(coalesce(a.username,''))
    and (lower(coalesce(a.email,''))=lower(v_email) or lower(coalesce(u.username,''))=lower(v_email))
  order by u.id limit 1;
  insert into public.messages(sender,receiver,text,sender_user_id,sender_name,title,body,audience_type,audience_value)
  values(v_email,v_receiver,coalesce(p_body,''),v_sender_user_id,coalesce(v_sender_name,v_email),
    coalesce(nullif(btrim(p_title),''),'پیام سامانه'),coalesce(p_body,''),
    coalesce(p_audience_type,'user'),nullif(btrim(p_audience_value),''))
  returning * into r;
  return r;
end;
$function$;
grant execute on function public.send_school_message(text,text,text,text,text) to authenticated;
