-- Canonical module contract field.
alter table public.teacher_exam_shares
  add column shared_by_teacher_id integer;
