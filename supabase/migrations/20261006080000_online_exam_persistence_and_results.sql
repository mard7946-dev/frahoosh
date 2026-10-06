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
-- Production function definition captured below.

CREATE OR REPLACE FUNCTION public.submit_teacher_exam(p_attempt_id bigint, p_answers jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_quiz integer;
  v_username text;
  v_email text;
  v_max numeric := 0;
  v_score numeric := 0;
  v_teacher_id integer;
  v_subject text;
  v_exam_title text;
  item jsonb;
  q public.quiz_questions;
  ans text;
  norm_ans text;
  norm text;
  correct boolean;
  pts numeric;
  accepted text[];
  idx text;
  correct_idx text;
  option_text text;
begin
  v_email := coalesce(auth.jwt()->>'email','');

  select a.quiz_id, a.student_username, a.max_score, e.teacher_id, e.subject, e.title
    into v_quiz, v_username, v_max, v_teacher_id, v_subject, v_exam_title
  from public.teacher_exam_attempts a
  join public.teacher_exams e on e.id = a.quiz_id
  where a.id = p_attempt_id
  for update;

  if v_quiz is null then
    raise exception 'attempt not found';
  end if;

  if not exists(
    select 1
    from public.account_settings
    where lower(email)=lower(v_email)
      and (lower(username)=lower(v_username) or lower(email)=lower(v_username))
  ) then
    raise exception 'attempt access denied';
  end if;

  if exists(select 1 from public.teacher_exam_attempts where id=p_attempt_id and status='submitted') then
    raise exception 'exam already submitted';
  end if;

  for item in select * from jsonb_array_elements(coalesce(p_answers,'[]'::jsonb)) loop
    select * into q
    from public.quiz_questions
    where id=(item->>'question_id')::integer
      and quiz_id=v_quiz;

    if q.id is null then continue; end if;

    ans := btrim(coalesce(item->>'answer',''));
    correct := false;
    pts := 0;

    if coalesce(q.auto_grade,true)=false or q.question_type='essay' then
      correct := null;
    elsif q.question_type='true_false' then
      norm_ans := lower(regexp_replace(replace(replace(replace(ans,'ي','ی'),'ك','ک'),'‌',''),'\\s+','','g'));
      norm := lower(regexp_replace(replace(replace(replace(coalesce(q.correct_answer,''),'ي','ی'),'ك','ک'),'‌',''),'\\s+','','g'));
      if norm_ans in ('1','true','صحیح','درست') then norm_ans:='صحیح';
      elsif norm_ans in ('0','false','غلط','نادرست') then norm_ans:='غلط'; end if;
      if norm in ('1','true','صحیح','درست') then norm:='صحیح';
      elsif norm in ('0','false','غلط','نادرست') then norm:='غلط'; end if;
      correct := norm_ans=norm;
      pts := case when correct then coalesce(q.points,1) else 0 end;
    elsif q.question_type in ('fill_blank','short_answer') then
      norm_ans := lower(regexp_replace(replace(replace(replace(ans,'ي','ی'),'ك','ک'),'‌',''),'\\s+','','g'));
      if nullif(btrim(coalesce(q.accepted_answers,q.correct_answer,'')),'') is not null then
        accepted := string_to_array(
          lower(replace(replace(replace(coalesce(q.accepted_answers,q.correct_answer,''),'ي','ی'),'ك','ک'),'‌','')),
          '|'
        );
        foreach norm in array accepted loop
          if norm_ans=regexp_replace(btrim(norm),'\\s+','','g') then
            correct:=true; exit;
          end if;
        end loop;
      end if;
      pts := case when correct then coalesce(q.points,1) else 0 end;
    else
      norm_ans := lower(regexp_replace(replace(replace(replace(ans,'ي','ی'),'ك','ک'),'‌',''),'\\s+','','g'));
      idx := case
        when norm_ans in ('1','۱','a','الف','گزینه1','گزینه۱') then '1'
        when norm_ans in ('2','۲','b','ب','گزینه2','گزینه۲') then '2'
        when norm_ans in ('3','۳','c','ج','گزینه3','گزینه۳') then '3'
        when norm_ans in ('4','۴','d','د','گزینه4','گزینه۴') then '4'
        else null end;
      correct_idx := case
        when lower(coalesce(q.correct_answer,'')) in ('1','۱','a','الف','گزینه ۱','گزینه۱') then '1'
        when lower(coalesce(q.correct_answer,'')) in ('2','۲','b','ب','گزینه ۲','گزینه۲') then '2'
        when lower(coalesce(q.correct_answer,'')) in ('3','۳','c','ج','گزینه ۳','گزینه۳') then '3'
        when lower(coalesce(q.correct_answer,'')) in ('4','۴','d','د','گزینه ۴','گزینه۴') then '4'
        else null end;
      if idx is not null and correct_idx is not null then
        correct:=idx=correct_idx;
      else
        option_text:=case correct_idx
          when '1' then q.option1 when '2' then q.option2
          when '3' then q.option3 when '4' then q.option4
          else q.correct_answer end;
        correct:=norm_ans=lower(regexp_replace(replace(replace(replace(coalesce(option_text,''),'ي','ی'),'ك','ک'),'‌',''),'\\s+','','g'));
      end if;
      pts := case when correct then coalesce(q.points,1) else 0 end;
    end if;

    v_score := v_score + coalesce(pts,0);
    insert into public.teacher_exam_answers(attempt_id,question_id,answer,is_correct,score)
    values(p_attempt_id,q.id,ans,correct,pts)
    on conflict(attempt_id,question_id) do update
      set answer=excluded.answer,
          is_correct=excluded.is_correct,
          score=excluded.score,
          answered_at=now();
  end loop;

  update public.teacher_exam_attempts
  set status='submitted', submitted_at=now(), score=v_score
  where id=p_attempt_id;

  insert into public.grades(
    student_id, teacher_id, subject, exam_name, score, max_score,
    description, created_at, grade_type, term, grade_date, title, assessment_date
  )
  select a.student_id, v_teacher_id, v_subject, v_exam_title, v_score, v_max,
         'نتیجه آزمون آنلاین', now()::text, 'آزمون آنلاین', 'آزمون آنلاین',
         now()::date::text, v_exam_title, now()::date::text
  from public.teacher_exam_attempts a
  where a.id=p_attempt_id;

  return jsonb_build_object(
    'attempt_id',p_attempt_id,
    'score',v_score,
    'max_score',v_max,
    'status','submitted'
  );
end;
$function$

