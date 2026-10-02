create extension if not exists pg_cron;
create or replace function public.purge_expired_assignment_submissions() returns integer language plpgsql security definer set search_path=public as $$
declare n integer; begin delete from public.assignment_submissions where expires_at is not null and expires_at<now(); get diagnostics n=row_count; return n; end; $$;
revoke all on function public.purge_expired_assignment_submissions() from public; grant execute on function public.purge_expired_assignment_submissions() to service_role;
do $$ begin
 if exists(select 1 from pg_namespace where nspname='cron') then
  if exists(select 1 from cron.job where jobname='frahoosh-assignment-expiry-cleanup') then perform cron.unschedule('frahoosh-assignment-expiry-cleanup'); end if;
  perform cron.schedule('frahoosh-assignment-expiry-cleanup','0 3 * * *','select public.purge_expired_assignment_submissions();');
 end if;
end $$;