-- Persist online-exam results into the school's grade views.
CREATE OR REPLACE FUNCTION public.submit_teacher_exam(p_attempt_id bigint, p_answers jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
DECLARE
  a public.teacher_exam_attempts;
  q record;
  exam_row public.teacher_exams;
  item jsonb;
  answer text;
  ok boolean;
  total numeric:=0;
  score numeric:=0;
  ctx jsonb := private.frahoosh_context();
  v_role text := lower(coalesce(ctx->>'role',''));
  v_student text := nullif(ctx->>'student_id','');
BEGIN
  SELECT * INTO a FROM public.teacher_exam_attempts WHERE id=p_attempt_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'تلاش آزمون پیدا نشد'; END IF;
  IF v_role='student' THEN
    IF a.student_id::text<>v_student THEN RAISE EXCEPTION 'دسترسی به این تلاش آزمون مجاز نیست'; END IF;
  ELSIF v_role NOT IN ('manager','educational','executive','cultural','advisor','staff','مدیر','معاون آموزشی','معاون اجرایی','معاون پرورشی','مشاور','کارمند') THEN
    RAISE EXCEPTION 'دسترسی به این تلاش آزمون مجاز نیست';
  END IF;
  IF a.status='submitted' THEN RAISE EXCEPTION 'این آزمون قبلاً تحویل شده است'; END IF;
  SELECT * INTO exam_row FROM public.teacher_exams WHERE id=a.quiz_id LIMIT 1;
  IF NOT FOUND THEN RAISE EXCEPTION 'آزمون مربوط به این تلاش پیدا نشد'; END IF;
  FOR q IN SELECT * FROM public.quiz_questions WHERE quiz_id=a.quiz_id ORDER BY sort_order,id LOOP
    total := total + coalesce(q.points,1);
    item := coalesce((SELECT x FROM jsonb_array_elements(p_answers) x WHERE (x->>'question_id')::bigint=q.id LIMIT 1),'{}'::jsonb);
    answer := coalesce(item->>'answer','');
    ok := false;
    IF q.question_type <> 'essay' THEN
      ok := answer=coalesce(q.correct_answer,'')
         OR (q.accepted_answers IS NOT NULL AND answer=ANY(string_to_array(q.accepted_answers,'|')));
      IF ok THEN score := score + coalesce(q.points,1); END IF;
    END IF;
    INSERT INTO public.teacher_exam_answers(attempt_id,question_id,answer,auto_correct,score)
    VALUES(a.id,q.id,answer,ok,CASE WHEN ok THEN q.points ELSE 0 END);
  END LOOP;
  UPDATE public.teacher_exam_attempts SET submitted_at=now(),status='submitted',score=score,max_score=total WHERE id=a.id;
  INSERT INTO public.student_grades(
    student_id,teacher_id,subject,class_name,assessment_type,assessment_title,score,coefficient,
    grade_date,grade_date_shamsi,description,term,manager_released
  ) VALUES(
    a.student_id,exam_row.teacher_id,exam_row.subject,exam_row.class_name,'آزمون آنلاین',exam_row.title,
    score,1,to_char(current_date,'YYYY-MM-DD'),to_char(current_date,'YYYY-MM-DD'),
    'نمره ثبت‌شده خودکار از آزمون آنلاین','نوبت جاری',true
  );
  INSERT INTO public.grades(
    student_id,teacher_id,subject,exam_name,score,description,grade_type,term,max_score,grade_date,title,assessment_date
  ) VALUES(
    a.student_id,exam_row.teacher_id,exam_row.subject,exam_row.title,score,
    'نمره ثبت‌شده خودکار از آزمون آنلاین','آزمون آنلاین','نوبت جاری',total,
    to_char(current_date,'YYYY-MM-DD'),exam_row.title,to_char(current_date,'YYYY-MM-DD')
  );
  RETURN jsonb_build_object('score',score,'max_score',total,'student_id',a.student_id,'exam_id',a.quiz_id);
END;
$$;
GRANT EXECUTE ON FUNCTION public.submit_teacher_exam(bigint,jsonb) TO authenticated;