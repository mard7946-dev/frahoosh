-- Harden SECURITY DEFINER exam RPCs against arbitrary student/teacher IDs.

create or replace function public.create_teacher_exam_share(
  p_quiz_id bigint,
  p_target_school_id text default null,
  p_target_class_name text default null,
  p_start_at timestamptz default null,
  p_end_at timestamptz default null,
  p_duration_minutes integer default 45
)
returns table(share_code text)
language plpgsql
security definer
set search_path = public, pg_catalog
as $function$
declare
  c text;
  q public.teacher_exams;
  ctx jsonb := private.frahoosh_context();
  v_role text := lower(coalesce(ctx->>'role',''));
  v_teacher text := nullif(ctx->>'teacher_id','');
begin
  select * into q from public.teacher_exams where id=p_quiz_id limit 1;
  if not found then raise exception 'آزمون پیدا نشد'; end if;
  if v_role not in ('manager','educational','executive','cultural','advisor','teacher','staff',
                    'مدیر','معاون آموزشی','معاون اجرایی','معاون پرورشی','مشاور','دبیر','کارمند') then
    raise exception 'دسترسی ایجاد لینک آزمون مجاز نیست';
  end if;
  if v_role = 'teacher' and q.teacher_id::text <> v_teacher then
    raise exception 'این آزمون متعلق به دبیر جاری نیست';
  end if;
  c := 'FRAH-' || upper(substr(md5(random()::text || clock_timestamp()::text),1,8));
  insert into public.teacher_exam_shares(
    quiz_id,share_code,target_school_id,target_class_name,start_at,end_at,duration_minutes,active
  ) values(q.id,c,p_target_school_id,p_target_class_name,p_start_at,p_end_at,p_duration_minutes,true);
  return query select c;
end;
$function$;

create or replace function public.get_shared_attempt_questions(p_attempt_id bigint)
returns setof quiz_questions
language plpgsql
security definer
set search_path = public, pg_catalog
as $function$
declare
  a public.teacher_exam_attempts;
  q_teacher text;
  ctx jsonb := private.frahoosh_context();
  v_role text := lower(coalesce(ctx->>'role',''));
  v_student text := nullif(ctx->>'student_id','');
  v_teacher text := nullif(ctx->>'teacher_id','');
begin
  select * into a from public.teacher_exam_attempts where id=p_attempt_id limit 1;
  if not found then raise exception 'تلاش آزمون پیدا نشد'; end if;
  select teacher_id::text into q_teacher from public.teacher_exams where id=a.quiz_id limit 1;
  if v_role = 'student' then
    if a.student_id::text <> v_student then raise exception 'دسترسی به این آزمون مجاز نیست'; end if;
  elsif v_role = 'teacher' then
    if q_teacher is null or q_teacher <> v_teacher then raise exception 'دسترسی به این آزمون مجاز نیست'; end if;
  elsif v_role not in ('manager','educational','executive','cultural','advisor','staff',
                       'مدیر','معاون آموزشی','معاون اجرایی','معاون پرورشی','مشاور','کارمند') then
    raise exception 'دسترسی به این آزمون مجاز نیست';
  end if;
  return query select q.* from public.quiz_questions q where q.quiz_id=a.quiz_id order by random();
end;
$function$;

create or replace function public.start_shared_teacher_exam(
  p_share_code text,
  p_student_id bigint default null,
  p_student_username text default null
)
returns table(attempt_id bigint, duration integer)
language plpgsql
security definer
set search_path = public, pg_catalog
as $function$
declare
  s public.teacher_exam_shares;
  q public.teacher_exams;
  a public.teacher_exam_attempts;
  ctx jsonb := private.frahoosh_context();
  v_role text := lower(coalesce(ctx->>'role',''));
  v_student text := nullif(ctx->>'student_id','');
  v_username text := nullif(ctx->>'username','');
begin
  if v_role <> 'student' then raise exception 'فقط دانش‌آموز می‌تواند آزمون را شروع کند'; end if;
  if p_student_id is null or p_student_id::text <> v_student then raise exception 'شناسه دانش‌آموز معتبر نیست'; end if;
  if coalesce(p_student_username,'') <> v_username then raise exception 'نام کاربری دانش‌آموز معتبر نیست'; end if;
  select * into s from public.teacher_exam_shares where share_code=p_share_code and active=true limit 1;
  if not found then raise exception 'آزمون پیدا نشد یا فعال نیست'; end if;
  if s.start_at is not null and now()<s.start_at then raise exception 'زمان آزمون هنوز شروع نشده است'; end if;
  if s.end_at is not null and now()>s.end_at then raise exception 'زمان آزمون به پایان رسیده است'; end if;
  select * into q from public.teacher_exams where id=s.quiz_id and published=true limit 1;
  if not found then raise exception 'آزمون منتشر نشده است'; end if;
  insert into public.teacher_exam_attempts(quiz_id,student_id,student_username,started_at,status)
  values(q.id,p_student_id,p_student_username,now(),'started') returning * into a;
  return query select a.id,coalesce(s.duration_minutes,q.duration);
end;
$function$;

create or replace function public.submit_teacher_exam(p_attempt_id bigint, p_answers jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_catalog
as $function$
declare
  a public.teacher_exam_attempts;
  q record;
  item jsonb;
  answer text;
  ok boolean;
  total numeric:=0;
  score numeric:=0;
  ctx jsonb := private.frahoosh_context();
  v_role text := lower(coalesce(ctx->>'role',''));
  v_student text := nullif(ctx->>'student_id','');
begin
  select * into a from public.teacher_exam_attempts where id=p_attempt_id for update;
  if not found then raise exception 'تلاش آزمون پیدا نشد'; end if;
  if v_role = 'student' then
    if a.student_id::text <> v_student then raise exception 'دسترسی به این تلاش آزمون مجاز نیست'; end if;
  elsif v_role not in ('manager','educational','executive','cultural','advisor','staff',
                       'مدیر','معاون آموزشی','معاون اجرایی','معاون پرورشی','مشاور','کارمند') then
    raise exception 'دسترسی به این تلاش آزمون مجاز نیست';
  end if;
  if a.status = 'submitted' then raise exception 'این آزمون قبلاً تحویل شده است'; end if;
  for q in select * from public.quiz_questions where quiz_id=a.quiz_id loop
    total := total + coalesce(q.points,1);
    item := coalesce((select x from jsonb_array_elements(p_answers) x where (x->>'question_id')::bigint=q.id limit 1),'{}'::jsonb);
    answer := coalesce(item->>'answer','');
    ok := false;
    if q.question_type <> 'essay' then
      ok := answer=coalesce(q.correct_answer,'')
         or (q.accepted_answers is not null and answer=any(string_to_array(q.accepted_answers,'|')));
      if ok then score := score + coalesce(q.points,1); end if;
    end if;
    insert into public.teacher_exam_answers(attempt_id,question_id,answer,auto_correct,score)
    values(a.id,q.id,answer,ok,case when ok then q.points else 0 end);
  end loop;
  update public.teacher_exam_attempts
  set submitted_at=now(),status='submitted',score=score,max_score=total
  where id=a.id;
  return jsonb_build_object('score',score,'max_score',total);
end;
$function$;

revoke execute on function public.notify_school_student_change() from public;
