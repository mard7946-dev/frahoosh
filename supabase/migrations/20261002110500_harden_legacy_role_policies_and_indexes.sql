-- Replace legacy public.frahoosh_role() policy calls with the canonical private role resolver.
do $$
declare r record;
begin
  for r in
    select schemaname,tablename,policyname,qual,with_check
    from pg_policies
    where schemaname='public'
      and (coalesce(qual,'') ilike '%frahoosh_role%' or coalesce(with_check,'') ilike '%frahoosh_role%')
  loop
    execute format(
      'alter policy %I on %I.%I%s%s',
      r.policyname,r.schemaname,r.tablename,
      case when r.qual is not null then format(' using (%s)',replace(r.qual,'frahoosh_role()','private.frahoosh_current_role()')) else '' end,
      case when r.with_check is not null then format(' with check (%s)',replace(r.with_check,'frahoosh_role()','private.frahoosh_current_role()')) else '' end
    );
  end loop;
end $$;

-- Remove confirmed duplicate indexes and add missing FK indexes.
drop index if exists public.online_class_students_student_id_idx;
drop index if exists public.online_class_teachers_teacher_id_idx;
drop index if exists public.teacher_exam_answers_attempt_id_idx;
drop index if exists public.teacher_exam_shares_quiz_idx;
create index if not exists counseling_records_student_id_idx on public.counseling_records(student_id);
create index if not exists online_attendance_session_id_idx on public.online_attendance(session_id);
create index if not exists school_class_config_teacher_id_idx on public.school_class_config(teacher_id);
create index if not exists smart_class_preview_class_id_idx on public.smart_class_preview(class_id);
create index if not exists smart_class_preview_student_id_idx on public.smart_class_preview(student_id);
create index if not exists smart_class_preview_teacher_id_idx on public.smart_class_preview(teacher_id);
