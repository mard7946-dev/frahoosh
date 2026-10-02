drop policy if exists "quiz_questions_teacher_delete" on public.quiz_questions;
create policy "quiz_questions_teacher_delete"
on public.quiz_questions for delete to authenticated
using (
 exists (
  select 1 from public.teacher_exams e
  join public.teachers t on t.id=e.teacher_id
  join public.account_settings a on lower(a.email)=lower(coalesce(auth.jwt()->>'email',''))
  where e.id=quiz_questions.quiz_id
    and (a.national_code=t.national_code or a.username=t.national_code)
 )
);

drop policy if exists "teacher_exam_shares_teacher_delete" on public.teacher_exam_shares;
create policy "teacher_exam_shares_teacher_delete"
on public.teacher_exam_shares for delete to authenticated
using (
 lower(coalesce(auth.jwt()->>'role','')) in
 ('manager','educational','executive','teacher','مدیر','مدیریت','معاون آموزشی','معاون اجرایی','دبیر')
);

drop policy if exists "teacher_exam_answers_management_delete" on public.teacher_exam_answers;
create policy "teacher_exam_answers_management_delete"
on public.teacher_exam_answers for delete to authenticated
using (private.frahoosh_current_role() in ('manager','مدیر','مدیریت','educational','معاون آموزشی','executive','معاون اجرایی'));
