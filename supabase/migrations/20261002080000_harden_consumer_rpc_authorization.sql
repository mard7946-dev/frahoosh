-- Frahoosh: close remaining RPC authorization gaps and normalize parent payment identity.

alter table public.parent_children
  drop constraint if exists fk_parent_children_student_id_core;

-- The canonical FK is the explicit named constraint below.
do $$ begin
  if not exists (
    select 1 from pg_constraint
    where conname='parent_children_student_id_fkey'
      and conrelid='public.parent_children'::regclass
  ) then
    alter table public.parent_children
      add constraint parent_children_student_id_fkey
      foreign key (student_id) references public.students(id) on delete cascade;
  end if;
end $$;

create or replace function public.create_payment_attempt(p_offer_id integer, p_student_id integer)
returns public.payment_attempts
language plpgsql
security definer
set search_path='public'
as $function$
declare
  o public.payment_offers;
  r public.payment_attempts;
  v_role text;
  v_email text := coalesce(auth.jwt()->>'email','');
  v_username text;
  v_national_code text;
  v_sid integer;
begin
  select lower(role), username, national_code
    into v_role, v_username, v_national_code
    from public.account_settings
   where auth_user_id=auth.uid()
   limit 1;

  if v_role not in ('student','دانش آموز','دانش‌آموز','parent','ولی','اولیا') then
    raise exception 'این عملیات فقط برای دانش آموز و اولیا مجاز است';
  end if;

  if v_role in ('parent','ولی','اولیا') then
    if p_student_id is null then
      select min(pc.student_id)
        into v_sid
        from public.parent_children pc
       where lower(pc.parent_username) in (lower(coalesce(v_username,'')),lower(coalesce(v_national_code,'')),lower(coalesce(v_email,'')));
    else
      select pc.student_id
        into v_sid
        from public.parent_children pc
       where pc.student_id=p_student_id
         and lower(pc.parent_username) in (lower(coalesce(v_username,'')),lower(coalesce(v_national_code,'')),lower(coalesce(v_email,'')))
       limit 1;
    end if;
  else
    select s.id
      into v_sid
      from public.students s
     where lower(s.email)=lower(v_email)
        or lower(s.national_code)=lower(coalesce(v_national_code,''))
     order by s.id
     limit 1;
  end if;

  if v_sid is null then
    raise exception 'فرزند/پرونده دانش آموز متصل به این حساب پیدا نشد';
  end if;

  select * into o
    from public.payment_offers
   where id=p_offer_id and active=1;
  if not found then
    raise exception 'گزینه پرداخت فعال نیست';
  end if;

  insert into public.payment_attempts
    (offer_id,student_id,payer_username,payer_role,amount,description)
  values
    (p_offer_id,v_sid,coalesce(v_username,v_email),v_role,o.amount,
     coalesce(o.title,'پرداخت مدرسه') ||
     case when coalesce(o.payment_reason,'')<>'' then ' - '||o.payment_reason else '' end)
  returning * into r;

  return r;
end;
$function$;

-- A sender may only message a real relationship target or management.
create or replace function public.send_school_message(
  p_receiver text,
  p_title text,
  p_body text,
  p_audience_type text default 'user',
  p_audience_value text default null
)
returns public.messages
language plpgsql
security definer
set search_path='public,private'
as $function$
declare
  r public.messages;
  v_email text:=coalesce(auth.jwt()->>'email','');
  v_receiver text:=coalesce(nullif(btrim(p_receiver),''),nullif(btrim(p_audience_value),''));
begin
  if v_receiver is null then
    raise exception 'receiver required';
  end if;
  if not private.frahoosh_can_message_target(v_receiver) then
    raise exception 'مخاطب خارج از ارتباط مجاز مدرسه است';
  end if;

  insert into public.messages(
    sender,receiver,text,sender_user_id,sender_name,title,body,audience_type,audience_value
  )
  values(
    v_email,v_receiver,coalesce(p_body,''),auth.uid(),v_email,
    coalesce(nullif(btrim(p_title),''),'پیام سامانه'),
    coalesce(p_body,''),coalesce(p_audience_type,'user'),
    nullif(btrim(p_audience_value),'')
  )
  returning * into r;

  return r;
end;
$function$;

-- Shared-attempt questions must belong to the authenticated user's own attempt.
create or replace function public.get_shared_attempt_questions(p_attempt_id bigint)
returns table(
  id integer, question text, options_json text, points numeric,
  question_type text, image_url text
)
language sql
security definer
set search_path='public'
as $function$
  select q.id,q.question,
    case when q.question_type='multiple_choice' then
      (select jsonb_agg(value order by random())::text
       from jsonb_array_elements_text(
         case when q.options_json is null or q.options_json='' or q.options_json='[]'
              then jsonb_build_array(q.option1,q.option2,q.option3,q.option4)
              else q.options_json::jsonb end ) AS x(value))
    when q.question_type='true_false' then '["صحیح","غلط"]'
    else '[]' end,
    q.points,q.question_type,q.image_url
  from public.teacher_exam_attempts a
  join public.quiz_questions q on q.quiz_id=a.quiz_id
  join public.account_settings ac on ac.auth_user_id=auth.uid()
 where a.id=p_attempt_id
   and (
     lower(coalesce(ac.email,''))=lower(coalesce(a.student_username,''))
     or lower(coalesce(ac.username,''))=lower(coalesce(a.student_username,''))
     or lower(coalesce(ac.national_code,''))=lower(coalesce(a.student_username,''))
   )
   and q.id in (select x::integer from jsonb_array_elements_text(a.question_order) x)
 order by array_position(
   array(select x::integer from jsonb_array_elements_text(a.question_order)),q.id
 );
$function$;

-- These helpers return only the caller's own state and do not need anonymous execution.
revoke execute on function public.current_account_username() from anon;
revoke execute on function public.frahoosh_can_activate_modules() from anon;
revoke execute on function public.is_module_active(text) from anon;

revoke execute on function public.send_school_message(text,text,text,text,text) from anon;
revoke execute on function public.get_shared_attempt_questions(bigint) from anon;
revoke execute on function public.create_payment_attempt(integer,integer) from anon;

grant execute on function public.send_school_message(text,text,text,text,text) to authenticated;
grant execute on function public.get_shared_attempt_questions(bigint) to authenticated;
grant execute on function public.create_payment_attempt(integer,integer) to authenticated;
