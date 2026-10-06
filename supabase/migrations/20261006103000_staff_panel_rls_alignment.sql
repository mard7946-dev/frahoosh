-- Align staff-facing panel CRUD with the operational module contract.
-- Online-class business rules are intentionally unchanged.

drop policy if exists "educational_crud_attendance" on public.attendance;
create policy "educational_crud_attendance" on public.attendance for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['educational','معاون آموزشی','معاونت آموزشی']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['educational','معاون آموزشی','معاونت آموزشی']));

drop policy if exists "educational_crud_ai_smart_reports" on public.ai_smart_reports;
create policy "educational_crud_ai_smart_reports" on public.ai_smart_reports for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['educational','معاون آموزشی','معاونت آموزشی']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['educational','معاون آموزشی','معاونت آموزشی']));

drop policy if exists "executive_crud_executive_classes" on public.executive_classes;
create policy "executive_crud_executive_classes" on public.executive_classes for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['executive','معاون اجرایی','معاونت اجرایی']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['executive','معاون اجرایی','معاونت اجرایی']));

drop policy if exists "executive_crud_staff" on public.staff;
create policy "executive_crud_staff" on public.staff for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['executive','معاون اجرایی','معاونت اجرایی']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['executive','معاون اجرایی','معاونت اجرایی']));

drop policy if exists "executive_crud_archive_items" on public.archive_items;
create policy "executive_crud_archive_items" on public.archive_items for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['executive','معاون اجرایی','معاونت اجرایی']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['executive','معاون اجرایی','معاونت اجرایی']));

drop policy if exists "executive_crud_requests" on public.executive_requests;
create policy "executive_crud_requests" on public.executive_requests for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['executive','معاون اجرایی','معاونت اجرایی']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['executive','معاون اجرایی','معاونت اجرایی']));

drop policy if exists "cultural_crud_morning_ceremony" on public.morning_ceremony;
create policy "cultural_crud_morning_ceremony" on public.morning_ceremony for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['cultural','معاون پرورشی','معاونت پرورشی']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['cultural','معاون پرورشی','معاونت پرورشی']));

drop policy if exists "cultural_crud_reports" on public.cultural_reports;
create policy "cultural_crud_reports" on public.cultural_reports for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['cultural','معاون پرورشی','معاونت پرورشی']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['cultural','معاون پرورشی','معاونت پرورشی']));

drop policy if exists "advisor_crud_parent_activities" on public.parent_activities;
create policy "advisor_crud_parent_activities" on public.parent_activities for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['advisor','مشاور','مشاوره']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['advisor','مشاور','مشاوره']));

drop policy if exists "advisor_crud_ai_smart_reports" on public.ai_smart_reports;
create policy "advisor_crud_ai_smart_reports" on public.ai_smart_reports for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['advisor','مشاور','مشاوره']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['advisor','مشاور','مشاوره']));

drop policy if exists "teacher_crud_teacher_parent_meetings" on public.teacher_parent_meetings;
create policy "teacher_crud_teacher_parent_meetings" on public.teacher_parent_meetings for all to authenticated
using (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['teacher','دبیر','معلم']))
with check (lower(coalesce(private.frahoosh_current_role(),'')) = any(array['teacher','دبیر','معلم']));

drop policy if exists "staff_crud_message_targets" on public.message_targets;
create policy "staff_crud_message_targets" on public.message_targets for all to authenticated
using ((select private.frahoosh_is_staff()))
with check ((select private.frahoosh_is_staff()));
