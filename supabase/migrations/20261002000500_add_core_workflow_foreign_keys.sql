-- Establish real relational integrity for the core school workflows.
-- Existing orphaned online-class membership rows are removed first.
begin;

delete from public.online_class_students o
where not exists (select 1 from public.online_classes c where c.id=o.class_id);

alter table public.teacher_classes
  add constraint teacher_classes_teacher_id_fkey
  foreign key (teacher_id) references public.teachers(id);

alter table public.assignments
  add constraint assignments_student_id_fkey foreign key (student_id) references public.students(id),
  add constraint assignments_teacher_id_fkey foreign key (teacher_id) references public.teachers(id);

alter table public.assignment_submissions
  add constraint assignment_submissions_assignment_id_fkey foreign key (assignment_id) references public.assignments(id) on delete cascade,
  add constraint assignment_submissions_student_id_fkey foreign key (student_id) references public.students(id);

alter table public.attendance
  add constraint attendance_student_id_fkey foreign key (student_id) references public.students(id),
  add constraint attendance_teacher_id_fkey foreign key (teacher_id) references public.teachers(id);

alter table public.grades
  add constraint grades_student_id_fkey foreign key (student_id) references public.students(id),
  add constraint grades_teacher_id_fkey foreign key (teacher_id) references public.teachers(id);

alter table public.student_grades
  add constraint student_grades_student_id_fkey foreign key (student_id) references public.students(id),
  add constraint student_grades_teacher_id_fkey foreign key (teacher_id) references public.teachers(id);

alter table public.online_class_students
  add constraint online_class_students_class_id_fkey foreign key (class_id) references public.online_classes(id) on delete cascade,
  add constraint online_class_students_student_id_fkey foreign key (student_id) references public.students(id) on delete cascade;

alter table public.online_class_teachers
  add constraint online_class_teachers_class_id_fkey foreign key (class_id) references public.online_classes(id) on delete cascade,
  add constraint online_class_teachers_teacher_id_fkey foreign key (teacher_id) references public.teachers(id) on delete cascade;

alter table public.online_class_sessions
  add constraint online_class_sessions_class_id_fkey foreign key (class_id) references public.online_classes(id) on delete cascade;

alter table public.online_attendance
  add constraint online_attendance_class_id_fkey foreign key (class_id) references public.online_classes(id) on delete cascade,
  add constraint online_attendance_student_id_fkey foreign key (student_id) references public.students(id) on delete cascade;

alter table public.payment_attempts
  add constraint payment_attempts_offer_id_fkey foreign key (offer_id) references public.payment_offers(id),
  add constraint payment_attempts_student_id_fkey foreign key (student_id) references public.students(id);

alter table public.payment_records
  add constraint payment_records_student_id_fkey foreign key (student_id) references public.students(id);

alter table public.payment_transactions
  add constraint payment_transactions_student_id_fkey foreign key (student_id) references public.students(id);

alter table public.teacher_exams
  add constraint teacher_exams_teacher_id_fkey foreign key (teacher_id) references public.teachers(id);

alter table public.quiz_questions
  add constraint quiz_questions_quiz_id_fkey foreign key (quiz_id) references public.teacher_exams(id) on delete cascade;

commit;
