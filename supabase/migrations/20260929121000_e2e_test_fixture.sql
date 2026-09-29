-- End-to-end test fixture used to verify manager -> class/exam/meeting -> student/parent.
delete from public.online_class_students where student_id=900002 and class_id in (select id from public.online_classes where title='کلاس تست فراهوش');
delete from public.online_class_teachers where teacher_id=900001 and class_id in (select id from public.online_classes where title='کلاس تست فراهوش');
delete from public.online_class_sessions where class_id in (select id from public.online_classes where title='کلاس تست فراهوش');
delete from public.online_classes where title='کلاس تست فراهوش';
insert into public.online_classes(title,subject,lesson,teacher,grade,class_name,duration,start_time_shamsi,end_time_shamsi,status,join_url,meeting_url,class_day,start_date_shamsi,start_clock,end_clock)
values('کلاس تست فراهوش','ریاضی','ریاضی','علی بانقش','هفتم','۷/۱',45,'۱۴۰۵/۰۷/۰۸ ۱۰:۰۰','۱۴۰۵/۰۷/۰۸ ۱۰:۴۵','active','https://meet.jit.si/frahoosh-test-class','https://meet.jit.si/frahoosh-test-class','دوشنبه','۱۴۰۵/۰۷/۰۸','۱۰:۰۰','۱۰:۴۵');
insert into public.online_class_teachers(class_id,teacher_id,teacher_name) select id,900001,'علی بانقش' from public.online_classes where title='کلاس تست فراهوش';
insert into public.online_class_students(class_id,student_id,student_name) select id,900002,'محمد آزمایشی' from public.online_classes where title='کلاس تست فراهوش';
insert into public.online_attendance(class_id,student_id,student_name,status) select id,900002,'محمد آزمایشی','present' from public.online_classes where title='کلاس تست فراهوش';
delete from public.grades where title='نمره تست فراهوش' and student_id=900002;
insert into public.grades(student_id,teacher_id,subject,exam_name,score,description,grade_type,term,max_score,grade_date,title,assessment_date) values(900002,900001,'ریاضی','آزمون تستی فراهوش',18.5,'نمره آزمایشی برای تست ارتباط پنل‌ها','امتحانی','نوبت اول',20,'۱۴۰۵/۰۷/۰۸','نمره تست فراهوش','۱۴۰۵/۰۷/۰۸');
delete from public.student_grades where assessment_title='نمره تست فراهوش' and student_id=900002;
insert into public.student_grades(student_id,teacher_id,subject,class_name,assessment_type,assessment_title,score,coefficient,grade_date,grade_date_shamsi,description,term,manager_released) values(900002,900001,'ریاضی','۷/۱','امتحانی','نمره تست فراهوش',18.5,1,'۱۴۰۵/۰۷/۰۸','۱۴۰۵/۰۷/۰۸','نمره آزمایشی برای تست ارتباط پنل‌ها','نوبت اول',true);
delete from public.teacher_exam_attempts where quiz_id in (select id from public.teacher_exams where title='آزمون تست فراهوش') and student_id=900002;
delete from public.teacher_exam_slots where quiz_id in (select id from public.teacher_exams where title='آزمون تست فراهوش');
delete from public.quiz_questions where quiz_id in (select id from public.teacher_exams where title='آزمون تست فراهوش');
delete from public.teacher_exams where title='آزمون تست فراهوش';
with ex as (insert into public.teacher_exams(teacher_id,title,subject,grade,class_name,exam_type,duration,description,published,secure_mode,standard_mode,max_attempts,passing_score) values(900001,'آزمون تست فراهوش','ریاضی','هفتم','۷/۱','آزمون آنلاین',20,'آزمون آزمایشی برای بررسی نمایش در پنل دانش‌آموز',true,true,true,1,10) returning id)
insert into public.quiz_questions(quiz_id,question,option1,option2,option3,option4,correct_answer,points,question_type,options_json,auto_grade,negative_score,sort_order) select id,'حاصل ۲ + ۲ کدام است؟','۴','۵','۶','۸','۴',1,'multiple_choice','["۴","۵","۶","۸"]'::jsonb,true,0,1 from ex;
insert into public.teacher_exam_slots(quiz_id,class_name,exam_date_shamsi,start_time_shamsi,end_time_shamsi,duration,coordinated,secure_mode,active) select id,'۷/۱','۱۴۰۵/۰۷/۰۸','۱۱:۰۰','۱۱:۲۰',20,true,true,true from public.teacher_exams where title='آزمون تست فراهوش';
delete from public.meeting_requests where requester_username='0053409531' and target_username='reza.test' and reason='بررسی وضعیت آموزشی دانش‌آموز';
insert into public.meeting_requests(requester_username,requester_name,requester_role,target_username,target_name,target_role,student_id,teacher_id,requested_date,requested_time,reason,status,manager_status,requested_day,description,title)
values('0053409531','حسن مردانه جهان تیغ','manager','reza.test','رضا','parent',900002,900001,'۱۴۰۵/۰۷/۰۹','۱۲:۰۰','بررسی وضعیت آموزشی دانش‌آموز','pending_manager','pending','سه‌شنبه','قرار ملاقات آزمایشی مدیر با ولی برای تست اتصال پنل‌ها','قرار ملاقات تست فراهوش');
insert into public.parent_children(parent_username,student_id) select 'reza.test',900002 where not exists(select 1 from public.parent_children where parent_username='reza.test' and student_id=900002);