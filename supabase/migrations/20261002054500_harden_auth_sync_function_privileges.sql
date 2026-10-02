-- Harden privileged Auth synchronization functions.
revoke execute on function public.link_current_auth_users_by_national_code() from public, anon, authenticated;
grant execute on function public.link_current_auth_users_by_national_code() to service_role;

revoke execute on function public.sync_existing_auth_users_to_account_settings() from public, anon, authenticated;
grant execute on function public.sync_existing_auth_users_to_account_settings() to service_role;

-- Trigger-only function: it is invoked by PostgreSQL, not through the Data API.
revoke execute on function public.sync_account_settings_auth_user() from public, anon, authenticated;
