-- Remove legacy broad staff CRUD policies from core school domains.
drop policy if exists "staff full access assignments" on public.assignments;
drop policy if exists "staff domain access assignments" on public.assignments;
drop policy if exists "staff full access attendance" on public.attendance;
drop policy if exists "staff domain access attendance" on public.attendance;
drop policy if exists "staff full access grades" on public.grades;
drop policy if exists "staff domain access grades" on public.grades;
drop policy if exists "staff full access student_grades" on public.student_grades;
drop policy if exists "staff domain access student_grades" on public.student_grades;
drop policy if exists "staff full access teacher_classes" on public.teacher_classes;
drop policy if exists "staff full access teachers" on public.teachers;
drop policy if exists "staff full access payment_records" on public.payment_records;
drop policy if exists "staff full access parent_meetings" on public.parent_meetings;
drop policy if exists "staff full access teacher_parent_meetings" on public.teacher_parent_meetings;
drop policy if exists "staff domain access teacher_parent_meetings" on public.teacher_parent_meetings;