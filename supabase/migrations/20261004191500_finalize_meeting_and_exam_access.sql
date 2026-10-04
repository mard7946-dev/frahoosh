-- Finalize meeting workflow and exam-authoring RLS.
drop policy if exists frahoosh_management_related_read on public.meeting_requests;
drop policy if exists meeting_requests_owner_read on public.meeting_requests;
drop policy if exists meeting_requests_parent_write on public.meeting_requests;
drop policy if exists meeting_requests_staff_all on public.meeting_requests;
drop policy if exists manager_crud_meeting_requests on public.meeting_requests;

create policy manager_meeting_requests_all on public.meeting_requests for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت'))
with check (lower(coalesce(private.frahoosh_current_role(),'')) in ('manager','مدیر','مدیریت'));

create policy educational_meeting_requests_read on public.meeting_requests for select to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) in ('educational','معاون آموزشی','معاونت آموزشی')
       and status in ('manager_approved','confirmed','rejected'));

create policy requester_meeting_requests_read on public.meeting_requests for select to authenticated
using (status <> 'pending_manager' and (
  lower(coalesce(requester_username,'')) in (select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid())
  or lower(coalesce(requester_username,'')) in (select lower(coalesce(a.national_code,'')) from public.account_settings a where a.auth_user_id=auth.uid())
));

create policy target_meeting_requests_read on public.meeting_requests for select to authenticated
using (status <> 'pending_manager' and (
  lower(coalesce(target_username,'')) in (select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid())
  or lower(coalesce(target_username,'')) in (select lower(coalesce(a.national_code,'')) from public.account_settings a where a.auth_user_id=auth.uid())
  or lower(coalesce(target_username,'')) in (select lower(coalesce(a.email,'')) from public.account_settings a where a.auth_user_id=auth.uid())
));

create policy student_meeting_requests_read on public.meeting_requests for select to authenticated
using (status <> 'pending_manager' and student_id=(select private.frahoosh_current_student_id()));

create policy teacher_meeting_requests_read on public.meeting_requests for select to authenticated
using (status <> 'pending_manager' and (
  teacher_id=(select private.frahoosh_current_teacher_id())
  or private.frahoosh_teacher_can_access_student((student_id)::bigint)
));

create policy parent_meeting_requests_read on public.meeting_requests for select to authenticated
using (status <> 'pending_manager' and exists (
  select 1 from public.parent_children pc
  where pc.student_id=meeting_requests.student_id
    and private.frahoosh_current_parent_matches(pc.parent_username)
));

create policy parent_meeting_requests_insert on public.meeting_requests for insert to authenticated
with check (
  requester_role in ('parent','parents','ولی','اولیا')
  and lower(coalesce(requester_username,'')) in (
    select lower(coalesce(a.national_code,'')) from public.account_settings a where a.auth_user_id=auth.uid()
  )
);

create policy staff_meeting_requests_insert on public.meeting_requests for insert to authenticated
with check (
  requester_role in ('teacher','staff','counselor','advisor','مشاور')
  and lower(coalesce(requester_username,'')) in (
    select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid()
  )
);

create policy requester_meeting_requests_update on public.meeting_requests for update to authenticated
using (status='pending_manager' and lower(coalesce(requester_username,'')) in (
  select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid()
  union select lower(coalesce(a.national_code,'')) from public.account_settings a where a.auth_user_id=auth.uid()
))
with check (status='pending_manager' and lower(coalesce(requester_username,'')) in (
  select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid()
  union select lower(coalesce(a.national_code,'')) from public.account_settings a where a.auth_user_id=auth.uid()
));

create policy requester_meeting_requests_delete on public.meeting_requests for delete to authenticated
using (status in ('pending_manager','rejected') and lower(coalesce(requester_username,'')) in (
  select lower(coalesce(a.username,'')) from public.account_settings a where a.auth_user_id=auth.uid()
  union select lower(coalesce(a.national_code,'')) from public.account_settings a where a.auth_user_id=auth.uid()
));

create policy educational_meeting_requests_update on public.meeting_requests for update to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) in ('educational','معاون آموزشی','معاونت آموزشی')
       and status='manager_approved')
with check (lower(coalesce(private.frahoosh_current_role(),'')) in ('educational','معاون آموزشی','معاونت آموزشی')
       and status in ('manager_approved','confirmed'));

drop policy if exists "staff full access teacher_exams" on public.teacher_exams;