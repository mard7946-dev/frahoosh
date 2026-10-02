-- Canonical module contract field: explicit ALTER form is required by repository validation.
alter table public.teacher_exam_shares
  add column if not exists shared_by_teacher_id integer;
