alter table if exists public.teacher_exam_shares
  add column if not exists shared_by_teacher_id integer;
