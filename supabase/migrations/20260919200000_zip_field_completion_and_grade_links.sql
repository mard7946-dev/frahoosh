-- Final canonical ZIP field completion and grade cross-panel links.
-- The Web and Android clients use the same tables. Missing fields are added
-- without replacing existing installations or data.

alter table if exists public.morning_ceremony
  add column if not exists ceremony_date text,
  add column if not exists title text,
  add column if not exists qari_name text,
  add column if not exists program text;

alter table if exists public.activity_programs
  add column if not exists activity_key text,
  add column if not exists title text,
  add column if not exists active boolean default true,
  add column if not exists amount numeric default 0;

alter table if exists public.student_referrals
  add column if not exists teacher_id bigint,
  add column if not exists referral_date text;

alter table if exists public.discipline_records
  add column if not exists student_id bigint,
  add column if not exists teacher_id bigint,
  add column if not exists description text;

alter table if exists public.monthly_report_cards
  add column if not exists month_name text,
  add column if not exists active boolean default true;

alter table if exists public.class_seat_assignments
  add column if not exists class_id bigint,
  add column if not exists academic_year text;

alter table if exists public.exam_seat_assignments
  add column if not exists exam_id bigint,
  add column if not exists exam_date text;

alter table if exists public.assignment_submissions
  add column if not exists submitted_at timestamptz;

alter table if exists public.program_activations
  add column if not exists program_key text,
  add column if not exists title text,
  add column if not exists activated_by text;

alter table if exists public.khwarizmi_registrations
  add column if not exists title text,
  add column if not exists category text,
  add column if not exists grade text,
  add column if not exists student_id bigint,
  add column if not exists status text;

-- Link mirrored grade records so teacher entry is visible to the student,
-- parent, report card and Web views without creating unrelated duplicates.
alter table if exists public.grades
  add column if not exists source_grade_id bigint;

alter table if exists public.student_grades
  add column if not exists source_grade_id bigint;

alter table if exists public.grade_items
  add column if not exists source_grade_id bigint;

create index if not exists idx_student_grades_source_grade_id
  on public.student_grades(source_grade_id);

create index if not exists idx_grade_items_source_grade_id
  on public.grade_items(source_grade_id);

do $$
declare t text;
begin
  foreach t in array array[
    'morning_ceremony','activity_programs','student_referrals','discipline_records',
    'monthly_report_cards','class_seat_assignments','exam_seat_assignments',
    'assignment_submissions','program_activations','khwarizmi_registrations',
    'grades','student_grades','grade_items'
  ] loop
    if to_regclass('public.' || t) is not null then
      execute format('alter table public.%I enable row level security', t);
    end if;
  end loop;
end $$;
