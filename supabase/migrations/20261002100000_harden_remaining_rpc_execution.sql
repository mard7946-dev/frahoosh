-- Frahoosh: harden remaining SECURITY DEFINER RPC/function execution grants.
-- Anonymous clients must not invoke internal authorization helpers or school operations.

revoke execute on function private.frahoosh_can_message_target(text) from public;
revoke execute on function private.frahoosh_current_parent_matches(text) from public;
revoke execute on function private.frahoosh_current_parent_username() from public;
revoke execute on function private.frahoosh_teacher_can_access_student(bigint) from public;

grant execute on function private.frahoosh_can_message_target(text) to authenticated;
grant execute on function private.frahoosh_current_parent_matches(text) to authenticated;
grant execute on function private.frahoosh_current_parent_username() to authenticated;
grant execute on function private.frahoosh_teacher_can_access_student(bigint) to authenticated;

revoke execute on function public.create_online_class_with_members(integer,text,text,text,text) from public;
grant execute on function public.create_online_class_with_members(integer,text,text,text,text) to authenticated;

revoke execute on function public.lookup_auth_email_by_national_code(text) from anon;
revoke execute on function public.lookup_auth_email_by_national_code(text) from public;
grant execute on function public.lookup_auth_email_by_national_code(text) to authenticated;

revoke execute on function public.frahoosh_token_hash() from public;
grant execute on function public.frahoosh_token_hash() to authenticated;
