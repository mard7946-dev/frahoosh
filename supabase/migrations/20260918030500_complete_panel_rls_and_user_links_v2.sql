-- Complete panel RLS and user-to-student/teacher links.
-- Applied to project gtmmllcxhdejwjjnyzrh.
create schema if not exists private;

create or replace function private.frahoosh_current_role()
returns text language sql stable security definer set search_path=''
as $$ select coalesce((select u.role from public.users u where lower(u.username)=lower(coalesce(auth.jwt()->>'email','')) limit 1),'') $$;

create or replace function private.frahoosh_current_student_id()
returns bigint language sql stable security definer set search_path=''
as $$ select coalesce((select u.linked_student_id from public.users u where lower(u.username)=lower(coalesce(auth.jwt()->>'email','')) limit 1),(select s.id from public.students s join public.account_settings a on lower(a.email)=lower(coalesce(auth.jwt()->>'email','')) where s.national_code=a.national_code limit 1)) $$;

create or replace function private.frahoosh_current_teacher_id()
returns bigint language sql stable security definer set search_path=''
as $$ select coalesce((select u.linked_teacher_id from public.users u where lower(u.username)=lower(coalesce(auth.jwt()->>'email','')) limit 1),(select t.id from public.teachers t join public.account_settings a on lower(a.email)=lower(coalesce(auth.jwt()->>'email','')) where t.national_code=a.national_code limit 1)) $$;

create or replace function private.frahoosh_is_staff()
returns boolean language sql stable security definer set search_path=''
as $$ select lower(coalesce((select u.role from public.users u where lower(u.username)=lower(coalesce(auth.jwt()->>'email','')) limit 1),'')) = any(array['مدیر','مدیریت','manager','معاون آموزشی','educational','معاون اجرایی','اجرایی','executive','معاون پرورشی','cultural','مشاوره','counselor','advisor','دبیر','teacher']) $$;

revoke all on function private.frahoosh_current_role() from public;
revoke all on function private.frahoosh_current_student_id() from public;
revoke all on function private.frahoosh_current_teacher_id() from public;
revoke all on function private.frahoosh_is_staff() from public;
grant execute on function private.frahoosh_current_role() to authenticated;
grant execute on function private.frahoosh_current_student_id() to authenticated;
grant execute on function private.frahoosh_current_teacher_id() to authenticated;
grant execute on function private.frahoosh_is_staff() to authenticated;

do $$ declare t text; tables text[]:=array['ai_assistant_sessions','ai_educational_analysis','ai_questions','ai_smart_reports','archive_items','assets','assignments','attendance','audience_presets','backup_records','certificates','class_cards','class_seats','competitions','counseling_followups','counseling_records','cultural_activity_registrations','cultural_reports','discipline_items','discipline_records','discipline_settings','educational_activities','event_audiences','exam_cards','exam_schedule','exam_seats','executive_classes','executive_operations','executive_reports','executive_requests','finance_accounts','finance_donations','finance_extra','finance_transactions','generated_weekly_schedule','grade_items','grade_visibility','grades','lesson_plans','message_delivery','message_targets','online_attendance','online_class_activity','online_class_ai_reports','online_class_board_events','online_class_chat','online_class_notifications','online_class_sessions','online_class_settings','online_class_students','online_class_teachers','online_presence_checks','online_quizzes','parent_children','parent_dashboard_events','parent_meetings','payment_records','payment_transactions','permissions','report_card_snapshots','report_cards','school_class_config','school_profile','seating','smart_board_activities','smart_board_content','smart_board_files','smart_board_interactive_tools','smart_board_media','smart_board_quizzes','smart_board_whiteboards','staff','student_cards','student_dashboard_events','student_files','student_grades','student_registrations','students','survey_answers','survey_questions','survey_responses','surveys','teacher_activities','teacher_attendance','teacher_classes','teacher_messages','teachers','users','weekly_schedule']; begin foreach t in array tables loop if to_regclass('public.'||t) is not null then execute format('create policy "manager full access %s" on public.%I for all to authenticated using ((select private.frahoosh_current_role()) = any(array[''مدیر'',''مدیریت'',''manager''])) with check ((select private.frahoosh_current_role()) = any(array[''مدیر'',''مدیریت'',''manager'']))',t,t); end if; end loop; end $$;

create policy "students staff read" on public.students for select to authenticated using ((select private.frahoosh_is_staff()));
create policy "students owner read" on public.students for select to authenticated using (id=(select private.frahoosh_current_student_id()));
create policy "students parent read" on public.students for select to authenticated using (exists(select 1 from public.parent_children pc where pc.student_id=students.id and lower(pc.parent_username)=lower(coalesce(auth.jwt()->>'email',''))));

create policy "student grades owner read" on public.student_grades for select to authenticated using (student_id=(select private.frahoosh_current_student_id()) or (select private.frahoosh_is_staff()));
create policy "student grades teacher insert" on public.student_grades for insert to authenticated with check (teacher_id=(select private.frahoosh_current_teacher_id()));
create policy "student grades teacher update" on public.student_grades for update to authenticated using (teacher_id=(select private.frahoosh_current_teacher_id())) with check (teacher_id=(select private.frahoosh_current_teacher_id()));

create policy "grades owner read" on public.grades for select to authenticated using (student_id=(select private.frahoosh_current_student_id()) or (select private.frahoosh_is_staff()));
create policy "grades teacher insert" on public.grades for insert to authenticated with check (teacher_id=(select private.frahoosh_current_teacher_id()));
create policy "grades teacher update" on public.grades for update to authenticated using (teacher_id=(select private.frahoosh_current_teacher_id())) with check (teacher_id=(select private.frahoosh_current_teacher_id()));

create policy "attendance owner read" on public.attendance for select to authenticated using (student_id=(select private.frahoosh_current_student_id()) or (select private.frahoosh_is_staff()));
create policy "attendance teacher insert" on public.attendance for insert to authenticated with check (teacher_id=(select private.frahoosh_current_teacher_id()));
create policy "attendance teacher update" on public.attendance for update to authenticated using (teacher_id=(select private.frahoosh_current_teacher_id())) with check (teacher_id=(select private.frahoosh_current_teacher_id()));

create policy "assignments owner read" on public.assignments for select to authenticated using (student_id=(select private.frahoosh_current_student_id()) or teacher_id=(select private.frahoosh_current_teacher_id()) or (select private.frahoosh_is_staff()));
create policy "assignments teacher insert" on public.assignments for insert to authenticated with check (teacher_id=(select private.frahoosh_current_teacher_id()));
create policy "assignments teacher update" on public.assignments for update to authenticated using (teacher_id=(select private.frahoosh_current_teacher_id())) with check (teacher_id=(select private.frahoosh_current_teacher_id()));

create policy "weekly schedule authenticated read" on public.weekly_schedule for select to authenticated using (true);
create policy "exam schedule authenticated read" on public.exam_schedule for select to authenticated using (true);
create policy "online class sessions authenticated read" on public.online_class_sessions for select to authenticated using (true);
create policy "online class students authenticated read" on public.online_class_students for select to authenticated using (true);
create policy "online class teachers authenticated read" on public.online_class_teachers for select to authenticated using (true);
create policy "online attendance owner or staff read" on public.online_attendance for select to authenticated using (student_id=(select private.frahoosh_current_student_id()) or (select private.frahoosh_is_staff()));
create policy "smart board content authenticated read" on public.smart_board_content for select to authenticated using (true);
create policy "smart board activities authenticated read" on public.smart_board_activities for select to authenticated using (true);
create policy "smart board quizzes authenticated read" on public.smart_board_quizzes for select to authenticated using (true);
create policy "smart board whiteboards authenticated read" on public.smart_board_whiteboards for select to authenticated using (true);

create policy "parent meetings parent read" on public.parent_meetings for select to authenticated using (exists(select 1 from public.parent_children pc where pc.student_id=parent_meetings.student_id and lower(pc.parent_username)=lower(coalesce(auth.jwt()->>'email',''))));
create policy "parent meetings staff read" on public.parent_meetings for select to authenticated using ((select private.frahoosh_is_staff()));
create policy "parent meetings parent insert" on public.parent_meetings for insert to authenticated with check (exists(select 1 from public.parent_children pc where pc.student_id=parent_meetings.student_id and lower(pc.parent_username)=lower(coalesce(auth.jwt()->>'email',''))));

create policy "counseling followups owner read" on public.counseling_followups for select to authenticated using (student_id=(select private.frahoosh_current_student_id()) or (select private.frahoosh_is_staff()));
create policy "discipline owner read" on public.discipline_records for select to authenticated using (student_id=(select private.frahoosh_current_student_id()) or (select private.frahoosh_is_staff()));

create policy "teacher classes owner read" on public.teacher_classes for select to authenticated using (teacher_id=(select private.frahoosh_current_teacher_id()) or (select private.frahoosh_is_staff()));
create policy "teacher classes owner update" on public.teacher_classes for update to authenticated using (teacher_id=(select private.frahoosh_current_teacher_id()) or (select private.frahoosh_current_role()) = any(array['مدیر','مدیریت','manager','معاون آموزشی','educational'])) with check (teacher_id=(select private.frahoosh_current_teacher_id()) or (select private.frahoosh_current_role()) = any(array['مدیر','مدیریت','manager','معاون آموزشی','educational']));