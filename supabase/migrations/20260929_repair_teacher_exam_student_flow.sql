-- Repair the student-side online exam flow used by the Android client.
CREATE OR REPLACE FUNCTION public.start_teacher_exam(
  p_quiz_id bigint,
  p_student_id bigint DEFAULT NULL,
  p_student_username text DEFAULT NULL
)
RETURNS TABLE(attempt_id bigint, duration integer)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
DECLARE
  q public.teacher_exams;
  a public.teacher_exam_attempts;
  ctx jsonb := private.frahoosh_context();
  v_role text := lower(coalesce(ctx->>'role',''));
  v_student text := nullif(ctx->>'student_id','');
  v_username text := nullif(ctx->>'username','');
  v_existing public.teacher_exam_attempts;
BEGIN
  IF v_role <> 'student' THEN RAISE EXCEPTION 'فقط دانش‌آموز می‌تواند آزمون را شروع کند'; END IF;
  IF p_student_id IS NULL OR p_student_id::text <> v_student THEN RAISE EXCEPTION 'شناسه دانش‌آموز معتبر نیست'; END IF;
  IF coalesce(p_student_username,'') <> v_username THEN RAISE EXCEPTION 'نام کاربری دانش‌آموز معتبر نیست'; END IF;
  SELECT * INTO q FROM public.teacher_exams WHERE id=p_quiz_id AND published=true LIMIT 1;
  IF NOT FOUND THEN RAISE EXCEPTION 'آزمون پیدا نشد یا منتشر نشده است'; END IF;
  IF q.class_name IS NOT NULL AND q.class_name <> '' AND NOT EXISTS (
    SELECT 1 FROM public.students s WHERE s.id=p_student_id AND (s.class_name=q.class_name OR s.grade=q.grade)
  ) THEN RAISE EXCEPTION 'این آزمون برای کلاس یا پایه دانش‌آموز منتشر نشده است'; END IF;
  SELECT * INTO v_existing FROM public.teacher_exam_attempts
    WHERE quiz_id=q.id AND student_id=p_student_id ORDER BY id DESC LIMIT 1;
  IF FOUND AND v_existing.status='started' THEN RETURN QUERY SELECT v_existing.id,q.duration; RETURN; END IF;
  IF FOUND AND q.max_attempts IS NOT NULL AND (
    SELECT count(*) FROM public.teacher_exam_attempts WHERE quiz_id=q.id AND student_id=p_student_id
  ) >= q.max_attempts THEN RAISE EXCEPTION 'تعداد مجاز شرکت در این آزمون به پایان رسیده است'; END IF;
  INSERT INTO public.teacher_exam_attempts(quiz_id,student_id,student_username,started_at,status,score,max_score)
  VALUES(q.id,p_student_id,p_student_username,now(),'started',0,0) RETURNING * INTO a;
  RETURN QUERY SELECT a.id,q.duration;
END;
$$;
GRANT EXECUTE ON FUNCTION public.start_teacher_exam(bigint,bigint,text) TO authenticated;

CREATE OR REPLACE FUNCTION public.get_teacher_exam_questions(p_attempt_id bigint)
RETURNS SETOF public.quiz_questions
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
DECLARE
  a public.teacher_exam_attempts;
  ctx jsonb := private.frahoosh_context();
  v_role text := lower(coalesce(ctx->>'role',''));
  v_student text := nullif(ctx->>'student_id','');
BEGIN
  SELECT * INTO a FROM public.teacher_exam_attempts WHERE id=p_attempt_id LIMIT 1;
  IF NOT FOUND THEN RAISE EXCEPTION 'تلاش آزمون پیدا نشد'; END IF;
  IF v_role='student' THEN
    IF a.student_id::text<>v_student THEN RAISE EXCEPTION 'دسترسی به این آزمون مجاز نیست'; END IF;
  ELSIF v_role NOT IN ('manager','educational','executive','cultural','advisor','teacher','staff','مدیر','معاون آموزشی','معاون اجرایی','معاون پرورشی','مشاور','دبیر','کارمند') THEN
    RAISE EXCEPTION 'دسترسی به سؤال‌های آزمون مجاز نیست';
  END IF;
  RETURN QUERY SELECT q.* FROM public.quiz_questions q WHERE q.quiz_id=a.quiz_id ORDER BY q.sort_order ASC,q.id ASC;
END;
$$;
GRANT EXECUTE ON FUNCTION public.get_teacher_exam_questions(bigint) TO authenticated;
