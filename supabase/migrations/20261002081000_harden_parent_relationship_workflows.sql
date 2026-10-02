-- Frahoosh: close parent self-link escalation and align parent-owned workflows with national-code identity.

drop policy if exists "parent_children_parent_insert" on public.parent_children;
drop policy if exists "parent_children_parent_update" on public.parent_children;
drop policy if exists "parent_children_parent_delete" on public.parent_children;

drop policy if exists "authenticated read parent_activities" on public.parent_activities;
drop policy if exists "parent_activities_self_read" on public.parent_activities;
create policy "parent_activities_self_read"
on public.parent_activities
for select to authenticated
using (private.frahoosh_current_parent_matches(parent_username));

drop policy if exists "parent_activities_self_write" on public.parent_activities;
create policy "parent_activities_self_write"
on public.parent_activities
for all to authenticated
using (private.frahoosh_current_parent_matches(parent_username))
with check (private.frahoosh_current_parent_matches(parent_username));

drop policy if exists "survey_responses_parent_write" on public.survey_responses;
create policy "survey_responses_parent_write"
on public.survey_responses
for all to authenticated
using (
  lower(coalesce(respondent_role,''))='parent'
  and private.frahoosh_current_parent_matches(respondent_username)
)
with check (
  lower(coalesce(respondent_role,''))='parent'
  and private.frahoosh_current_parent_matches(respondent_username)
);

drop policy if exists "parent payment access" on public.payment_records;
create policy "parent payment access"
on public.payment_records
for all to authenticated
using (
  exists (
    select 1 from public.parent_children pc
    where pc.student_id=payment_records.student_id
      and lower(coalesce(payment_records.parent_username,''))=lower(coalesce(pc.parent_username,''))
      and private.frahoosh_current_parent_matches(pc.parent_username)
  )
)
with check (
  exists (
    select 1 from public.parent_children pc
    where pc.student_id=payment_records.student_id
      and lower(coalesce(payment_records.parent_username,''))=lower(coalesce(pc.parent_username,''))
      and private.frahoosh_current_parent_matches(pc.parent_username)
  )
);
