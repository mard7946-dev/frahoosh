-- Frahoosh: harden online exam attempts for real school delivery.
-- Idempotent and intended to run after 003_online_exam_operations.sql.

alter table public.teacher_exam_attempts
  add column if not exists duration_minutes integer;

create or replace function public.start_shared_teacher_exam(
  p_share_code text,
  p_student_id bigint default null,
  p_student_username text default null
) returns table(attempt_id bigint,duration integer)
language plpgsql security definer set search_path=public
as $$
declare
  s public.teacher_exam_shares;
  q public.teacher_exams;
  a public.teacher_exam_attempts;
  used_attempts integer := 0;
  d integer;
begin
  select * into s
    from public.teacher_exam_shares
   where share_code=p_share_code
     and active=true
   limit 1;

  if not found then
    raise exception 'آزمون پیدا نشد یا فعال نیست';
  end if;

  if s.start_at is not null and now() < s.start_at then
    raise exception 'زمان شروع آزمون فرا نرسیده است';
  end if;

  if s.end_at is not null and now() > s.end_at then
    raise exception 'مهلت آزمون به پایان رسیده است';
  end if;

  select * into q
    from public.teacher_exams
   where id=s.quiz_id
     and published=true
   limit 1;

  if not found then
    raise exception 'آزمون منتشر نشده است';
  end if;

  if coalesce(q.locked,false) then
    raise exception 'این آزمون توسط مدرسه قفل شده است';
  end if;

  select count(*) into used_attempts
    from public.teacher_exam_attempts
   where quiz_id=q.id
     and (
       (p_student_id is not null and student_id=p_student_id)
       or (p_student_id is null and p_student_username is not null and student_username=p_student_username)
     );

  if used_attempts >= greatest(coalesce(q.max_attempts,1),1) then
    raise exception 'حداکثر دفعات شرکت در این آزمون استفاده شده است';
  end if;

  d := greatest(coalesce(s.duration_minutes,q.duration),1);

  insert into public.teacher_exam_attempts(
    quiz_id,student_id,student_username,started_at,status,duration_minutes
  )
  values(q.id,p_student_id,p_student_username,now(),'started',d)
  returning * into a;

  return query select a.id,d;
end;
$$;

create or replace function public.submit_teacher_exam(
  p_attempt_id bigint,
  p_answers jsonb
) returns jsonb
language plpgsql security definer set search_path=public
as $$
declare
  a public.teacher_exam_attempts;
  q record;
  item jsonb;
  answer text;
  ok boolean;
  total numeric:=0;
  score numeric:=0;
  max_duration integer;
begin
  select * into a
    from public.teacher_exam_attempts
   where id=p_attempt_id
   for update;

  if not found then
    raise exception 'تلاش آزمون پیدا نشد';
  end if;

  if a.status <> 'started' then
    raise exception 'این تلاش آزمون قبلاً ثبت نهایی شده است';
  end if;

  max_duration := greatest(coalesce(a.duration_minutes,0),0);
  if max_duration > 0 and a.started_at + make_interval(mins => max_duration) < now() then
    update public.teacher_exam_attempts
       set submitted_at=now(), status='expired'
     where id=a.id;
    raise exception 'زمان آزمون به پایان رسیده است';
  end if;

  for q in
    select * from public.quiz_questions where quiz_id=a.quiz_id
  loop
    total := total + coalesce(q.points,1);
    item := coalesce(
      (select x from jsonb_array_elements(p_answers) x
        where (x->>'question_id')::bigint=q.id
        limit 1),
      '{}'::jsonb
    );
    answer := coalesce(item->>'answer','');
    ok := false;

    if q.question_type <> 'essay' then
      ok := answer=coalesce(q.correct_answer,'')
         or (q.accepted_answers is not null
             and answer=any(string_to_array(q.accepted_answers,'|')));
      if ok then
        score := score + coalesce(q.points,1);
      elsif coalesce(q.negative_score,0) > 0 then
        score := greatest(0, score - coalesce(q.negative_score,0));
      end if;
    end if;

    insert into public.teacher_exam_answers(
      attempt_id,question_id,answer,auto_correct,score
    )
    values(
      a.id,q.id,answer,ok,
      case when ok then q.points else 0 end
    );
  end loop;

  update public.teacher_exam_attempts
     set submitted_at=now(),
         status='submitted',
         score=score,
         max_score=total
   where id=a.id;

  return jsonb_build_object('score',score,'max_score',total);
end;
$$;

grant execute on function public.start_shared_teacher_exam(text,bigint,text) to authenticated;
grant execute on function public.submit_teacher_exam(bigint,jsonb) to authenticated;
