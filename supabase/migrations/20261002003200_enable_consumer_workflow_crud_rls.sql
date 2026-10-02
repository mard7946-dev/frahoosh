alter table public.parent_activities add column if not exists parent_username text;
create or replace function public.current_account_username() returns text language sql stable security definer set search_path=public as $$
select coalesce((select username from public.account_settings where auth_user_id=auth.uid() limit 1),(select email from public.account_settings where auth_user_id=auth.uid() limit 1),'') $$;
revoke all on function public.current_account_username() from public; grant execute on function public.current_account_username() to authenticated;
do $$ declare t text; begin
 foreach t in array array['activity_registrations','student_council','basij_registration','school_ally','school_mayor','certificate_requests'] loop
  execute format('drop policy if exists student_self_write_%s on public.%I',t,t);
  execute format('create policy student_self_write_%s on public.%I for all to authenticated using (student_id = private.frahoosh_current_student_id()) with check (student_id = private.frahoosh_current_student_id())',t,t);
 end loop;
end $$;
drop policy if exists student_payment_attempts_write on public.payment_attempts;
create policy student_payment_attempts_write on public.payment_attempts for all to authenticated using(student_id=private.frahoosh_current_student_id() and (payer_username is null or lower(payer_username)=lower(public.current_account_username()))) with check(student_id=private.frahoosh_current_student_id() and (payer_username is null or lower(payer_username)=lower(public.current_account_username())));
drop policy if exists parent_activities_self_write on public.parent_activities;
create policy parent_activities_self_write on public.parent_activities for all to authenticated using(lower(coalesce(parent_username,''))=lower(public.current_account_username())) with check(lower(coalesce(parent_username,''))=lower(public.current_account_username()));
drop policy if exists survey_responses_parent_write on public.survey_responses;
create policy survey_responses_parent_write on public.survey_responses for all to authenticated using(lower(respondent_username)=lower(public.current_account_username()) and lower(coalesce(respondent_role,''))='parent') with check(lower(respondent_username)=lower(public.current_account_username()) and lower(coalesce(respondent_role,''))='parent');
drop policy if exists parent_payment_attempts_write on public.payment_attempts;
create policy parent_payment_attempts_write on public.payment_attempts for all to authenticated using(lower(coalesce(payer_username,''))=lower(public.current_account_username()) and lower(coalesce(payer_role,'')) in('parent','parents','ولی','اولیا')) with check(lower(coalesce(payer_username,''))=lower(public.current_account_username()) and lower(coalesce(payer_role,'')) in('parent','parents','ولی','اولیا'));
create index if not exists idx_parent_activities_parent_username on public.parent_activities(parent_username);