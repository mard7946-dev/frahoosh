-- Non-destructive E2E fixture data for the Frahoosh school workflow test.
INSERT INTO public.assignments (student_id,teacher_id,title,description,status,due_date,subject,class_name)
SELECT 2,2,'تکلیف تست فراهوش','حل ۱۰ سؤال از فصل اول و ارسال تصویر یا PDF.','published','۱۴۰۵/۰۷/۱۲','ریاضی','۸/۱'
WHERE NOT EXISTS (SELECT 1 FROM public.assignments WHERE title='تکلیف تست فراهوش' AND student_id=2 AND teacher_id=2);

INSERT INTO public.attendance (student_id,date,status,description,teacher_id,subject,class_name,attendance_date)
SELECT 2,'۱۴۰۵/۰۷/۰۸','حاضر','ثبت حضور نمونه برای تست واقعی پنل‌ها',2,'ریاضی','۸/۱','۱۴۰۵/۰۷/۰۸'
WHERE NOT EXISTS (SELECT 1 FROM public.attendance WHERE student_id=2 AND teacher_id=2 AND date='۱۴۰۵/۰۷/۰۸');

INSERT INTO public.student_referrals (student_id,teacher_id,referral_to,reason,referral_date,status)
SELECT 2,2,'educational','نیاز به پیگیری آموزشی','۱۴۰۵/۰۷/۰۸','pending'
WHERE NOT EXISTS (SELECT 1 FROM public.student_referrals WHERE student_id=2 AND teacher_id=2 AND referral_to='educational' AND referral_date='۱۴۰۵/۰۷/۰۸');

INSERT INTO public.discipline_records (student_id,teacher_id,title,description,discipline_type,record_date,priority,status,actor_username,actor_role,note)
SELECT 2,2,'ثبت نمونه انضباطی','رکورد نمونه برای تست گردش کار انضباطی','تذکر','۱۴۰۵/۰۷/۰۸','normal','open','1234567894','teacher','قابل پیگیری توسط معاون'
WHERE NOT EXISTS (SELECT 1 FROM public.discipline_records WHERE student_id=2 AND teacher_id=2 AND title='ثبت نمونه انضباطی');

INSERT INTO public.grades (student_id,teacher_id,subject,exam_name,score,description,grade_type,term,max_score,grade_date,title,assessment_date)
SELECT 2,2,'ریاضی','آزمون تست فراهوش',18.5,'نمره نمونه برای تست ارتباط دبیر، دانش‌آموز و ولی','امتحانی','نوبت اول',20,'۱۴۰۵/۰۷/۰۸','نمره آزمون تست فراهوش','۱۴۰۵/۰۷/۰۸'
WHERE NOT EXISTS (SELECT 1 FROM public.grades WHERE student_id=2 AND teacher_id=2 AND exam_name='آزمون تست فراهوش');

INSERT INTO public.meeting_requests
(requester_username,requester_name,requester_role,target_username,target_name,target_role,student_id,teacher_id,parent_id,parent_phone,requested_date,requested_time,reason,status,responsible_status,manager_status,requested_day,description,title)
SELECT 'ali.test','علی','parent','1234567894','رضا مردانه جهان تیغ','teacher',2,2,NULL,NULL,'۱۴۰۵/۰۷/۱۰','۱۰:۰۰','پیگیری وضعیت آموزشی دانش‌آموز','pending_manager','pending','pending','شنبه','درخواست نمونه برای تست گردش کار ملاقات','درخواست ملاقات نمونه'
WHERE NOT EXISTS (SELECT 1 FROM public.meeting_requests WHERE title='درخواست ملاقات نمونه' AND student_id=2);