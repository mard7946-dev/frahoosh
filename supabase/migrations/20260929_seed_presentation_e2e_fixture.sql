-- Presentation E2E fixture for Frahoosh.
-- Idempotent seed used to exercise exam, online class, assignment,
-- attendance, referral, parent link, and meeting workflows.

insert into public.school_class_config (grade,class_name,teacher_id,capacity,academic_year,active)
select 'هشتم','۸/۱',2,30,'۱۴۰۵-۱۴۰۶',true
where not exists (select 1 from public.school_class_config where grade='هشتم' and class_name='۸/۱' and academic_year='۱۴۰۵-۱۴۰۶');

insert into public.online_classes
(title,subject,lesson,teacher,grade,class_name,duration,start_time_shamsi,end_time_shamsi,status,join_url,meeting_url,class_day,start_date_shamsi,start_clock,end_clock)
select 'کلاس آنلاین ارائه فراهوش','ریاضی','ریاضی','رضا مردانه جهان تیغ','هشتم','۸/۱',60,'۱۴۰۵-۰۷-۰۸ ۱۰:۰۰','۱۴۰۵-۰۷-۰۸ ۱۱:۰۰','active','https://meet.jit.si/frahoosh-demo-81','https://meet.jit.si/frahoosh-demo-81','دوشنبه','۱۴۰۵-۰۷-۰۸','۱۰:۰۰','۱۱:۰۰'
where not exists (select 1 from public.online_classes where title='کلاس آنلاین ارائه فراهوش');

insert into public.online_class_teachers (class_id,teacher_id,teacher_name)
select c.id,2,'رضا مردانه جهان تیغ' from public.online_classes c
where c.title='کلاس آنلاین ارائه فراهوش'
and not exists (select 1 from public.online_class_teachers x where x.class_id=c.id and x.teacher_id=2);

insert into public.online_class_students (class_id,student_id,student_name)
select c.id,2,'محمد' from public.online_classes c
where c.title='کلاس آنلاین ارائه فراهوش'
and not exists (select 1 from public.online_class_students x where x.class_id=c.id and x.student_id=2);

insert into public.teacher_exams
(teacher_id,title,subject,grade,class_name,exam_type,duration,description,published,secure_mode,standard_mode,max_attempts,passing_score)
select 2,'آزمون ارائه فراهوش','ریاضی','هشتم','۸/۱','آزمایشی',20,'آزمون نمونه برای بررسی کامل گردش آزمون دبیر تا دانش‌آموز و ثبت نمره.',true,false,true,1,10
where not exists (select 1 from public.teacher_exams where title='آزمون ارائه فراهوش');

insert into public.quiz_questions
(quiz_id,question,option1,option2,option3,option4,correct_answer,points,question_type,options_json,accepted_answers,difficulty,cognitive_level,auto_grade,negative_score,sort_order)
select e.id,'حاصل ۲ + ۲ کدام است؟','۳','۴','۵','۶','۴',5,'multiple_choice','["۳","۴","۵","۶"]'::jsonb,'۴','آسان','دانش',true,0,1
from public.teacher_exams e
where e.title='آزمون ارائه فراهوش'
and not exists (select 1 from public.quiz_questions q where q.quiz_id=e.id);

insert into public.assignments
(student_id,teacher_id,title,description,status,due_date,subject,class_name)
select 2,2,'تکلیف ارائه فراهوش','حل تمرین فصل اول ریاضی و ارسال پاسخ یا فایل PDF.','active','۱۴۰۵-۰۷-۱۰','ریاضی','۸/۱'
where not exists (select 1 from public.assignments where title='تکلیف ارائه فراهوش');

insert into public.attendance
(student_id,teacher_id,class_name,subject,attendance_date,status,description,date)
select 2,2,'۸/۱','ریاضی','۱۴۰۵-۰۷-۰۸','present','حضور آزمایشی برای تست ارائه فراهوش','۱۴۰۵-۰۷-۰۸'
where not exists (select 1 from public.attendance where student_id=2 and class_name='۸/۱' and attendance_date='۱۴۰۵-۰۷-۰۸');

insert into public.student_referrals
(student_id,teacher_id,referral_to,reason,referral_date,status)
select 2,2,'معاون آموزشی','ارجاع آزمایشی برای بررسی روند آموزشی دانش‌آموز.','۱۴۰۵-۰۷-۰۸','pending'
where not exists (select 1 from public.student_referrals where student_id=2 and referral_to='معاون آموزشی' and reason like 'ارجاع آزمایشی%');

insert into public.parent_children (parent_username,student_id)
select 'reza.test',2
where not exists (select 1 from public.parent_children where parent_username='reza.test' and student_id=2);

insert into public.parent_meeting_requests
(parent_id,parent_name,student_id,student_name,target_role,target_name,requested_date_shamsi,requested_time,reason,status,educational_approval,manager_approval)
select null,'رضا',2,'محمد','educational','محمدرضا صفی','۱۴۰۵-۰۷-۰۹','۱۰:۳۰','درخواست ملاقات آزمایشی برای تست ارائه فراهوش.','pending',false,false
where not exists (select 1 from public.parent_meeting_requests where parent_name='رضا' and student_id=2 and reason like 'درخواست ملاقات آزمایشی%');
