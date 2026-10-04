create or replace function public.update_meeting_request(p_id bigint,p_title text,p_target_username text,p_target_name text,p_requested_day text,p_requested_date text,p_requested_time text,p_reason text,p_description text)
returns boolean language plpgsql security definer set search_path='' as $function$
declare v_role text; v_username text;
begin
  if auth.uid() is null then raise exception 'نشست کاربر معتبر نیست'; end if;
  v_role:=lower(trim(coalesce(private.frahoosh_current_role(),'')));
  v_username:=trim(coalesce(public.current_account_username(),''));
  if v_role in ('manager','مدیر','مدیریت') then
    update public.meeting_requests set title=trim(p_title),target_username=trim(p_target_username),target_name=trim(p_target_name),requested_day=nullif(trim(coalesce(p_requested_day,'')),''),requested_date=trim(p_requested_date),requested_time=trim(p_requested_time),reason=trim(p_reason),description=nullif(trim(coalesce(p_description,'')),'') where id=p_id and status='pending_manager';
  else
    update public.meeting_requests set title=trim(p_title),target_username=trim(p_target_username),target_name=trim(p_target_name),requested_day=nullif(trim(coalesce(p_requested_day,'')),''),requested_date=trim(p_requested_date),requested_time=trim(p_requested_time),reason=trim(p_reason),description=nullif(trim(coalesce(p_description,'')),'') where id=p_id and status='pending_manager' and lower(coalesce(requester_username,''))=lower(v_username);
  end if;
  if not found then raise exception 'این درخواست برای ویرایش در دسترس نیست'; end if;
  return true;
end;$function$;
create or replace function public.delete_meeting_request(p_id bigint)
returns boolean language plpgsql security definer set search_path='' as $function$
declare v_role text; v_username text;
begin
  if auth.uid() is null then raise exception 'نشست کاربر معتبر نیست'; end if;
  v_role:=lower(trim(coalesce(private.frahoosh_current_role(),'')));
  v_username:=trim(coalesce(public.current_account_username(),''));
  if v_role in ('manager','مدیر','مدیریت') then
    delete from public.meeting_requests where id=p_id and status in ('pending_manager','rejected');
  else
    delete from public.meeting_requests where id=p_id and status in ('pending_manager','rejected') and lower(coalesce(requester_username,''))=lower(v_username);
  end if;
  if not found then raise exception 'این درخواست برای حذف در دسترس نیست'; end if;
  return true;
end;$function$;
revoke all on function public.update_meeting_request(bigint,text,text,text,text,text,text,text,text) from public,anon;
grant execute on function public.update_meeting_request(bigint,text,text,text,text,text,text,text,text) to authenticated;
revoke all on function public.delete_meeting_request(bigint) from public,anon;
grant execute on function public.delete_meeting_request(bigint) to authenticated;
