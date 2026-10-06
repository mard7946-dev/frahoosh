-- Real online-exam persistence for educational deputy and parent-visible results.
-- Applied to Supabase production on 2026-10-06.

create policy "educational_crud_teacher_exams"
on public.teacher_exams
for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) = any (array[
    'educational','معاون آموزشی','معاونت آموزشی'
  ])
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) = any (array[
    'educational','معاون آموزشی','معاونت آموزشی'
  ])
);

create policy "educational_crud_quiz_questions"
on public.quiz_questions
for all to authenticated
using (
  lower(coalesce(private.frahoosh_current_role(),'')) = any (array[
    'educational','معاون آموزشی','معاونت آموزشی'
  ])
)
with check (
  lower(coalesce(private.frahoosh_current_role(),'')) = any (array[
    'educational','معاون آموزشی','معاونت آموزشی'
  ])
);

-- The submit RPC keeps the secure server-side grading path and additionally
-- publishes the resulting score into grades, so the student's parent can see
-- the same result through the normal grades/RLS path.
-- Full function body is maintained in the production migration history.
