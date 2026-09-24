-- Frahoosh consumer payment and online exam contract hardening
alter table public.payment_offers add column if not exists payment_url text;
alter table public.payment_offers add column if not exists gateway text;
alter table public.payment_offers add column if not exists gateway_enabled boolean not null default false;
alter table public.payment_offers add column if not exists manual_amount boolean not null default false;
alter table public.payment_offers add column if not exists payment_reason text;
alter table public.quiz_questions add column if not exists sort_order integer not null default 0;
alter table public.quiz_questions add column if not exists formula text;
create index if not exists idx_payment_offers_status on public.payment_offers(status);
create index if not exists idx_payment_attempts_student on public.payment_attempts(student_id);
create index if not exists idx_teacher_exam_questions_order on public.quiz_questions(quiz_id, sort_order);
create unique index if not exists uq_online_class_students_class_student on public.online_class_students(class_id, student_id);
create unique index if not exists uq_online_class_teachers_class_teacher on public.online_class_teachers(class_id, teacher_id);
