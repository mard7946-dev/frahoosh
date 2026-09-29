-- Align the end-to-end test fixture with the actual test accounts/roles.
-- Source of truth: the Supabase Auth user list and the agreed role mapping.
begin;

update public.users
set role='parent', display_name='علی'
where username='ali.test';

update public.account_settings
set preferences = coalesce(preferences,'{}'::jsonb) || jsonb_build_object('role','parent','test_user',true),
    display_name='علی',
    national_code='0123456781'
where username='ali.test';

update public.parent_children
set parent_username='ali.test'
where parent_username='reza.test' and student_id=900002;

update public.meeting_requests
set target_username='ali.test'
where target_username='reza.test';

update public.online_class_teachers
set teacher_id=2, teacher_name='رضا مردانه جهان تیغ'
where teacher_id=900001;

update public.online_classes
set teacher='رضا مردانه جهان تیغ'
where teacher='علی بانقش';

update public.grades
set teacher_id=2
where teacher_id=900001;

update public.student_grades
set teacher_id=2
where teacher_id=900001;

update public.teacher_exams
set teacher_id=2
where teacher_id=900001;

commit;
