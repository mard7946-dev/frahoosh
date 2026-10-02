-- Manager has full CRUD on every canonical module table.
drop policy if exists "manager_crud_users" on public.users;
create policy "manager_crud_users" on public.users
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_account_settings" on public.account_settings;
create policy "manager_crud_account_settings" on public.account_settings
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_students" on public.students;
create policy "manager_crud_students" on public.students
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teachers" on public.teachers;
create policy "manager_crud_teachers" on public.teachers
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_staff" on public.staff;
create policy "manager_crud_staff" on public.staff
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_parent_children" on public.parent_children;
create policy "manager_crud_parent_children" on public.parent_children
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_attendance" on public.attendance;
create policy "manager_crud_attendance" on public.attendance
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_grades" on public.grades;
create policy "manager_crud_grades" on public.grades
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_student_grades" on public.student_grades;
create policy "manager_crud_student_grades" on public.student_grades
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_assignments" on public.assignments;
create policy "manager_crud_assignments" on public.assignments
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teacher_classes" on public.teacher_classes;
create policy "manager_crud_teacher_classes" on public.teacher_classes
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_weekly_schedule" on public.weekly_schedule;
create policy "manager_crud_weekly_schedule" on public.weekly_schedule
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_generated_weekly_schedule" on public.generated_weekly_schedule;
create policy "manager_crud_generated_weekly_schedule" on public.generated_weekly_schedule
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_exam_schedule" on public.exam_schedule;
create policy "manager_crud_exam_schedule" on public.exam_schedule
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_classes" on public.online_classes;
create policy "manager_crud_online_classes" on public.online_classes
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_class_sessions" on public.online_class_sessions;
create policy "manager_crud_online_class_sessions" on public.online_class_sessions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_class_students" on public.online_class_students;
create policy "manager_crud_online_class_students" on public.online_class_students
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_class_teachers" on public.online_class_teachers;
create policy "manager_crud_online_class_teachers" on public.online_class_teachers
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_attendance" on public.online_attendance;
create policy "manager_crud_online_attendance" on public.online_attendance
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_messages" on public.messages;
create policy "manager_crud_messages" on public.messages
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_message_targets" on public.message_targets;
create policy "manager_crud_message_targets" on public.message_targets
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_message_reads" on public.message_reads;
create policy "manager_crud_message_reads" on public.message_reads
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_finance_accounts" on public.finance_accounts;
create policy "manager_crud_finance_accounts" on public.finance_accounts
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_finance_transactions" on public.finance_transactions;
create policy "manager_crud_finance_transactions" on public.finance_transactions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_payment_offers" on public.payment_offers;
create policy "manager_crud_payment_offers" on public.payment_offers
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_payment_attempts" on public.payment_attempts;
create policy "manager_crud_payment_attempts" on public.payment_attempts
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_payment_records" on public.payment_records;
create policy "manager_crud_payment_records" on public.payment_records
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_report_cards" on public.report_cards;
create policy "manager_crud_report_cards" on public.report_cards
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_report_card_snapshots" on public.report_card_snapshots;
create policy "manager_crud_report_card_snapshots" on public.report_card_snapshots
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_school_profile" on public.school_profile;
create policy "manager_crud_school_profile" on public.school_profile
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_school_class_config" on public.school_class_config;
create policy "manager_crud_school_class_config" on public.school_class_config
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teacher_exams" on public.teacher_exams;
create policy "manager_crud_teacher_exams" on public.teacher_exams
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_quiz_questions" on public.quiz_questions;
create policy "manager_crud_quiz_questions" on public.quiz_questions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teacher_exam_slots" on public.teacher_exam_slots;
create policy "manager_crud_teacher_exam_slots" on public.teacher_exam_slots
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teacher_exam_attempts" on public.teacher_exam_attempts;
create policy "manager_crud_teacher_exam_attempts" on public.teacher_exam_attempts
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teacher_exam_answers" on public.teacher_exam_answers;
create policy "manager_crud_teacher_exam_answers" on public.teacher_exam_answers
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teacher_attendance" on public.teacher_attendance;
create policy "manager_crud_teacher_attendance" on public.teacher_attendance
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_grade_items" on public.grade_items;
create policy "manager_crud_grade_items" on public.grade_items
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_educational_activities" on public.educational_activities;
create policy "manager_crud_educational_activities" on public.educational_activities
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_executive_classes" on public.executive_classes;
create policy "manager_crud_executive_classes" on public.executive_classes
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_executive_operations" on public.executive_operations;
create policy "manager_crud_executive_operations" on public.executive_operations
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_executive_reports" on public.executive_reports;
create policy "manager_crud_executive_reports" on public.executive_reports
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_archive_items" on public.archive_items;
create policy "manager_crud_archive_items" on public.archive_items
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_cultural_activity_registrations" on public.cultural_activity_registrations;
create policy "manager_crud_cultural_activity_registrations" on public.cultural_activity_registrations
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_cultural_competitions" on public.cultural_competitions;
create policy "manager_crud_cultural_competitions" on public.cultural_competitions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_competitions" on public.competitions;
create policy "manager_crud_competitions" on public.competitions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_cultural_reports" on public.cultural_reports;
create policy "manager_crud_cultural_reports" on public.cultural_reports
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_morning_ceremony" on public.morning_ceremony;
create policy "manager_crud_morning_ceremony" on public.morning_ceremony
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_activity_programs" on public.activity_programs;
create policy "manager_crud_activity_programs" on public.activity_programs
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_activity_offers" on public.activity_offers;
create policy "manager_crud_activity_offers" on public.activity_offers
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_activity_registrations" on public.activity_registrations;
create policy "manager_crud_activity_registrations" on public.activity_registrations
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_student_council" on public.student_council;
create policy "manager_crud_student_council" on public.student_council
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_basij_registration" on public.basij_registration;
create policy "manager_crud_basij_registration" on public.basij_registration
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_school_ally" on public.school_ally;
create policy "manager_crud_school_ally" on public.school_ally
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_school_mayor" on public.school_mayor;
create policy "manager_crud_school_mayor" on public.school_mayor
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_qari_registration" on public.qari_registration;
create policy "manager_crud_qari_registration" on public.qari_registration
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_counseling_records" on public.counseling_records;
create policy "manager_crud_counseling_records" on public.counseling_records
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_counseling_followups" on public.counseling_followups;
create policy "manager_crud_counseling_followups" on public.counseling_followups
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_counseling_guidance" on public.counseling_guidance;
create policy "manager_crud_counseling_guidance" on public.counseling_guidance
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_counselor_board" on public.counselor_board;
create policy "manager_crud_counselor_board" on public.counselor_board
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_parent_meetings" on public.parent_meetings;
create policy "manager_crud_parent_meetings" on public.parent_meetings
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_counseling_classes" on public.counseling_classes;
create policy "manager_crud_counseling_classes" on public.counseling_classes
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_parent_activities" on public.parent_activities;
create policy "manager_crud_parent_activities" on public.parent_activities
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_student_referrals" on public.student_referrals;
create policy "manager_crud_student_referrals" on public.student_referrals
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_discipline_records" on public.discipline_records;
create policy "manager_crud_discipline_records" on public.discipline_records
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teacher_meetings" on public.teacher_meetings;
create policy "manager_crud_teacher_meetings" on public.teacher_meetings
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teacher_activities" on public.teacher_activities;
create policy "manager_crud_teacher_activities" on public.teacher_activities
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_survey_responses" on public.survey_responses;
create policy "manager_crud_survey_responses" on public.survey_responses
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_transport_requests" on public.transport_requests;
create policy "manager_crud_transport_requests" on public.transport_requests
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_backup_records" on public.backup_records;
create policy "manager_crud_backup_records" on public.backup_records
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_smart_board_content" on public.smart_board_content;
create policy "manager_crud_smart_board_content" on public.smart_board_content
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_smart_board_whiteboards" on public.smart_board_whiteboards;
create policy "manager_crud_smart_board_whiteboards" on public.smart_board_whiteboards
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_smart_board_files" on public.smart_board_files;
create policy "manager_crud_smart_board_files" on public.smart_board_files
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_smart_board_media" on public.smart_board_media;
create policy "manager_crud_smart_board_media" on public.smart_board_media
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_smart_board_interactive_tools" on public.smart_board_interactive_tools;
create policy "manager_crud_smart_board_interactive_tools" on public.smart_board_interactive_tools
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_smart_board_quizzes" on public.smart_board_quizzes;
create policy "manager_crud_smart_board_quizzes" on public.smart_board_quizzes
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_smart_board_activities" on public.smart_board_activities;
create policy "manager_crud_smart_board_activities" on public.smart_board_activities
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_ai_assistant_sessions" on public.ai_assistant_sessions;
create policy "manager_crud_ai_assistant_sessions" on public.ai_assistant_sessions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_ai_questions" on public.ai_questions;
create policy "manager_crud_ai_questions" on public.ai_questions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_ai_educational_analysis" on public.ai_educational_analysis;
create policy "manager_crud_ai_educational_analysis" on public.ai_educational_analysis
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_ai_smart_reports" on public.ai_smart_reports;
create policy "manager_crud_ai_smart_reports" on public.ai_smart_reports
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_meeting_requests" on public.meeting_requests;
create policy "manager_crud_meeting_requests" on public.meeting_requests
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_certificate_requests" on public.certificate_requests;
create policy "manager_crud_certificate_requests" on public.certificate_requests
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_monthly_report_cards" on public.monthly_report_cards;
create policy "manager_crud_monthly_report_cards" on public.monthly_report_cards
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_class_seat_assignments" on public.class_seat_assignments;
create policy "manager_crud_class_seat_assignments" on public.class_seat_assignments
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_exam_seat_assignments" on public.exam_seat_assignments;
create policy "manager_crud_exam_seat_assignments" on public.exam_seat_assignments
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_assignment_submissions" on public.assignment_submissions;
create policy "manager_crud_assignment_submissions" on public.assignment_submissions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_program_activations" on public.program_activations;
create policy "manager_crud_program_activations" on public.program_activations
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_school_events" on public.school_events;
create policy "manager_crud_school_events" on public.school_events
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_smart_class_preview" on public.smart_class_preview;
create policy "manager_crud_smart_class_preview" on public.smart_class_preview
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_assets" on public.assets;
create policy "manager_crud_assets" on public.assets
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_certificates" on public.certificates;
create policy "manager_crud_certificates" on public.certificates
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_student_cards" on public.student_cards;
create policy "manager_crud_student_cards" on public.student_cards
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_class_cards" on public.class_cards;
create policy "manager_crud_class_cards" on public.class_cards
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_surveys" on public.surveys;
create policy "manager_crud_surveys" on public.surveys
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_educational_followups" on public.educational_followups;
create policy "manager_crud_educational_followups" on public.educational_followups
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_academic_followups" on public.academic_followups;
create policy "manager_crud_academic_followups" on public.academic_followups
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_khwarizmi_registrations" on public.khwarizmi_registrations;
create policy "manager_crud_khwarizmi_registrations" on public.khwarizmi_registrations
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_executive_requests" on public.executive_requests;
create policy "manager_crud_executive_requests" on public.executive_requests
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_art_competitions" on public.art_competitions;
create policy "manager_crud_art_competitions" on public.art_competitions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_sport_competitions" on public.sport_competitions;
create policy "manager_crud_sport_competitions" on public.sport_competitions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_morning_leaders" on public.morning_leaders;
create policy "manager_crud_morning_leaders" on public.morning_leaders
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_lesson_plans" on public.lesson_plans;
create policy "manager_crud_lesson_plans" on public.lesson_plans
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_student_class_info" on public.student_class_info;
create policy "manager_crud_student_class_info" on public.student_class_info
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_parent_meeting_requests" on public.parent_meeting_requests;
create policy "manager_crud_parent_meeting_requests" on public.parent_meeting_requests
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_audience_presets" on public.audience_presets;
create policy "manager_crud_audience_presets" on public.audience_presets
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_class_seats" on public.class_seats;
create policy "manager_crud_class_seats" on public.class_seats
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_discipline_items" on public.discipline_items;
create policy "manager_crud_discipline_items" on public.discipline_items
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_discipline_settings" on public.discipline_settings;
create policy "manager_crud_discipline_settings" on public.discipline_settings
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_event_audiences" on public.event_audiences;
create policy "manager_crud_event_audiences" on public.event_audiences
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_exam_cards" on public.exam_cards;
create policy "manager_crud_exam_cards" on public.exam_cards
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_exam_seats" on public.exam_seats;
create policy "manager_crud_exam_seats" on public.exam_seats
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_finance_donations" on public.finance_donations;
create policy "manager_crud_finance_donations" on public.finance_donations
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_finance_extra" on public.finance_extra;
create policy "manager_crud_finance_extra" on public.finance_extra
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_grade_visibility" on public.grade_visibility;
create policy "manager_crud_grade_visibility" on public.grade_visibility
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_message_delivery" on public.message_delivery;
create policy "manager_crud_message_delivery" on public.message_delivery
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_class_activity" on public.online_class_activity;
create policy "manager_crud_online_class_activity" on public.online_class_activity
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_class_ai_reports" on public.online_class_ai_reports;
create policy "manager_crud_online_class_ai_reports" on public.online_class_ai_reports
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_class_board_events" on public.online_class_board_events;
create policy "manager_crud_online_class_board_events" on public.online_class_board_events
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_class_chat" on public.online_class_chat;
create policy "manager_crud_online_class_chat" on public.online_class_chat
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_class_notifications" on public.online_class_notifications;
create policy "manager_crud_online_class_notifications" on public.online_class_notifications
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_class_settings" on public.online_class_settings;
create policy "manager_crud_online_class_settings" on public.online_class_settings
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_presence_checks" on public.online_presence_checks;
create policy "manager_crud_online_presence_checks" on public.online_presence_checks
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_online_quizzes" on public.online_quizzes;
create policy "manager_crud_online_quizzes" on public.online_quizzes
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_parent_dashboard_events" on public.parent_dashboard_events;
create policy "manager_crud_parent_dashboard_events" on public.parent_dashboard_events
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_payment_transactions" on public.payment_transactions;
create policy "manager_crud_payment_transactions" on public.payment_transactions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_permissions" on public.permissions;
create policy "manager_crud_permissions" on public.permissions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_seating" on public.seating;
create policy "manager_crud_seating" on public.seating
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_student_dashboard_events" on public.student_dashboard_events;
create policy "manager_crud_student_dashboard_events" on public.student_dashboard_events
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_student_files" on public.student_files;
create policy "manager_crud_student_files" on public.student_files
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_student_registrations" on public.student_registrations;
create policy "manager_crud_student_registrations" on public.student_registrations
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_survey_answers" on public.survey_answers;
create policy "manager_crud_survey_answers" on public.survey_answers
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_survey_questions" on public.survey_questions;
create policy "manager_crud_survey_questions" on public.survey_questions
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_module_activations" on public.module_activations;
create policy "manager_crud_module_activations" on public.module_activations
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teacher_exam_shares" on public.teacher_exam_shares;
create policy "manager_crud_teacher_exam_shares" on public.teacher_exam_shares
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));

drop policy if exists "manager_crud_teacher_parent_meetings" on public.teacher_parent_meetings;
create policy "manager_crud_teacher_parent_meetings" on public.teacher_parent_meetings
for all to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'))
with check (private.frahoosh_current_role() in ('manager','مدیر','مدیریت'));
