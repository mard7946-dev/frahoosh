-- Allow signed-in students to access quiz questions for their assigned school class
-- even when a timetable-created online class has not yet been backfilled into online_class_students.
drop policy if exists smart_board_quizzes_student_roster_read on public.smart_board_quizzes;
create policy smart_board_quizzes_student_roster_read
on public.smart_board_quizzes for select to authenticated
using (
  is_published = true
  and exists (
    select 1
    from public.students st
    join public.online_classes c on c.id = smart_board_quizzes.class_id
    where st.id = (select private.frahoosh_current_student_id())
      and replace(replace(regexp_replace(lower(btrim(st.class_name)), '\s+', '', 'g'),'ي','ی'),'ك','ک')
        = replace(replace(regexp_replace(lower(btrim(c.class_name)), '\s+', '', 'g'),'ي','ی'),'ك','ک')
  )
  and exists (
    select 1 from public.online_class_sessions s
    where s.class_id = smart_board_quizzes.class_id and s.ended_at is null
  )
);

drop policy if exists classroom_quiz_responses_insert_member on public.classroom_quiz_responses;
create policy classroom_quiz_responses_insert_member
on public.classroom_quiz_responses for insert to authenticated
with check (
  exists (
    select 1 from public.smart_board_quizzes q
    where q.id = classroom_quiz_responses.quiz_id
      and q.class_id = classroom_quiz_responses.class_id
      and q.is_published = true
  )
  and exists (
    select 1 from public.online_class_sessions s
    where s.id = classroom_quiz_responses.session_id
      and s.class_id = classroom_quiz_responses.class_id
      and s.ended_at is null
  )
  and (
    (
      classroom_quiz_responses.student_id is not null
      and classroom_quiz_responses.guest_user_id is null
      and classroom_quiz_responses.student_id = (select private.frahoosh_current_student_id())
      and (
        exists (
          select 1 from public.online_class_students m
          where m.class_id = classroom_quiz_responses.class_id
            and m.student_id = classroom_quiz_responses.student_id
        )
        or exists (
          select 1
          from public.students st
          join public.online_classes c on c.id = classroom_quiz_responses.class_id
          where st.id = classroom_quiz_responses.student_id
            and replace(replace(regexp_replace(lower(btrim(st.class_name)), '\s+', '', 'g'),'ي','ی'),'ك','ک')
              = replace(replace(regexp_replace(lower(btrim(c.class_name)), '\s+', '', 'g'),'ي','ی'),'ك','ک')
        )
      )
    )
    or
    (
      classroom_quiz_responses.student_id is null
      and classroom_quiz_responses.guest_user_id = (select auth.uid())
      and exists (
        select 1 from public.guest_online_members g
        where g.class_id = classroom_quiz_responses.class_id
          and g.user_id = (select auth.uid())
          and g.role = 'guest'
          and g.left_at is null
      )
    )
  )
);
