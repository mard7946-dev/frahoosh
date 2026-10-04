create or replace function private.frahoosh_can_create_meeting_request(p_username text,p_role text)
returns boolean language sql stable security definer set search_path='' as $function$
  select exists(select 1 from public.account_settings a where a.auth_user_id=(select auth.uid()) and lower(coalesce(a.username,''))=lower(coalesce(p_username,'')) and lower(coalesce(a.role,''))=lower(coalesce(p_role,'')))
$function$;
revoke execute on function private.frahoosh_can_create_meeting_request(text,text) from public,anon;
grant execute on function private.frahoosh_can_create_meeting_request(text,text) to authenticated;
drop policy if exists parent_meeting_requests_insert on public.meeting_requests;
drop policy if exists staff_meeting_requests_insert on public.meeting_requests;
create policy parent_meeting_requests_insert on public.meeting_requests for insert to authenticated with check ((select private.frahoosh_can_create_meeting_request(requester_username,requester_role)));
create policy staff_meeting_requests_insert on public.meeting_requests for insert to authenticated with check ((select private.frahoosh_can_create_meeting_request(requester_username,requester_role)));
